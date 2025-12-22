use crate::error::{Result, RupdfError};
use crate::pdf::FontEmbedder;
use crate::resources::{LoadedImage, LoadedResources};
use crate::types::*;
use pdf_writer::{Content, Filter, Finish, Name, Pdf, Rect, Ref, Str, TextStr};
use std::collections::HashMap;

/// Main PDF generator
pub struct PdfGenerator<'a> {
    doc: &'a Document,
    resources: &'a LoadedResources,
    compress: bool,
}

impl<'a> PdfGenerator<'a> {
    pub fn new(doc: &'a Document, resources: &'a LoadedResources, compress: bool) -> Self {
        Self {
            doc,
            resources,
            compress,
        }
    }

    pub fn generate(&self) -> Result<Vec<u8>> {
        let mut pdf = Pdf::new();
        let mut ref_alloc = Ref::new(1);

        // Allocate refs for catalog and page tree
        let catalog_ref = ref_alloc.bump();
        let page_tree_ref = ref_alloc.bump();

        // First pass: collect all used fonts and images
        let mut font_embedders: HashMap<String, FontEmbedder> = HashMap::new();
        // Track each unique (image_ref, size) for per-size 300 DPI embedding
        // Key: "imagename_WxH" where W/H are display points rounded to int
        // Value: (original image_ref, width_pts, height_pts)
        let mut image_usages: HashMap<String, (String, f32, f32)> = HashMap::new();
        // Map user alias -> PostScript name for font references
        let mut alias_to_ps: HashMap<String, String> = HashMap::new();

        for page in &self.doc.pages {
            for element in &page.elements {
                match element {
                    Element::Text(t) => {
                        let font = self.resources.get_font(&t.font)?;
                        alias_to_ps.entry(t.font.clone()).or_insert_with(|| font.postscript_name.clone());
                        let embedder = font_embedders
                            .entry(t.font.clone())
                            .or_insert_with(|| FontEmbedder::new(font, &t.font));
                        embedder.use_text(&t.text)?;
                    }
                    Element::Barcode(b) if b.human_readable => {
                        let font = self.resources.get_font(&b.font)?;
                        alias_to_ps.entry(b.font.clone()).or_insert_with(|| font.postscript_name.clone());
                        let embedder = font_embedders
                            .entry(b.font.clone())
                            .or_insert_with(|| FontEmbedder::new(font, &b.font));
                        embedder.use_text(&b.value)?;
                    }
                    Element::Image(img) => {
                        // Check image type to determine tracking strategy
                        let loaded = self.resources.get_image(&img.image_ref)?;
                        let key = match loaded {
                            LoadedImage::Svg { .. } => {
                                // SVGs are vector - use original name, size 0x0 as placeholder
                                img.image_ref.clone()
                            }
                            LoadedImage::Raster { .. } => {
                                // Raster images get per-size entries for 300 DPI
                                Self::image_size_key(&img.image_ref, img.w, img.h)
                            }
                        };
                        image_usages.entry(key).or_insert_with(|| {
                            (img.image_ref.clone(), img.w, img.h)
                        });
                    }
                    _ => {}
                }
            }
        }

        // Allocate refs for fonts (5 refs each: Type0, CIDFont, Descriptor, CMap, FontFile)
        // Use PostScript names as keys for font_refs (for page resources)
        let mut font_refs: HashMap<String, Ref> = HashMap::new();
        let mut font_all_refs: HashMap<String, (Ref, Ref, Ref, Ref, Ref)> = HashMap::new();
        for font_alias in font_embedders.keys() {
            let ps_name = alias_to_ps.get(font_alias)
                .expect("font alias was inserted in first pass");
            let type0_ref = ref_alloc.bump();
            let cid_ref = ref_alloc.bump();
            let desc_ref = ref_alloc.bump();
            let cmap_ref = ref_alloc.bump();
            let file_ref = ref_alloc.bump();
            font_refs.insert(ps_name.clone(), type0_ref);
            font_all_refs.insert(font_alias.clone(), (type0_ref, cid_ref, desc_ref, cmap_ref, file_ref));
        }

        // Allocate refs for images (one per unique size)
        let mut image_refs: HashMap<String, Ref> = HashMap::new();
        for size_key in image_usages.keys() {
            image_refs.insert(size_key.clone(), ref_alloc.bump());
        }

        // Allocate refs for pages
        let mut page_refs: Vec<Ref> = Vec::with_capacity(self.doc.pages.len());
        let mut content_refs: Vec<Ref> = Vec::with_capacity(self.doc.pages.len());
        for _ in &self.doc.pages {
            page_refs.push(ref_alloc.bump());
            content_refs.push(ref_alloc.bump());
        }

        // Allocate refs for alpha graphics states (we'll create a few common ones)
        let mut alpha_states: HashMap<u8, Ref> = HashMap::new();
        for alpha in [255u8, 191, 127, 63] {
            alpha_states.insert(alpha, ref_alloc.bump());
        }

        // Write catalog
        pdf.catalog(catalog_ref).pages(page_tree_ref);

        // Write document info
        if self.doc.metadata.title.is_some()
            || self.doc.metadata.author.is_some()
            || self.doc.metadata.subject.is_some()
            || self.doc.metadata.creator.is_some()
        {
            let info_ref = ref_alloc.bump();
            let mut info = pdf.document_info(info_ref);
            if let Some(title) = &self.doc.metadata.title {
                info.title(TextStr(title));
            }
            if let Some(author) = &self.doc.metadata.author {
                info.author(TextStr(author));
            }
            if let Some(subject) = &self.doc.metadata.subject {
                info.subject(TextStr(subject));
            }
            if let Some(creator) = &self.doc.metadata.creator {
                info.creator(TextStr(creator));
            }
            info.finish();
        }

        // Write page tree
        let mut pages = pdf.pages(page_tree_ref);
        pages.kids(page_refs.iter().copied());
        pages.count(self.doc.pages.len() as i32);
        pages.finish();

        // Write alpha graphics states
        for (&alpha, &state_ref) in &alpha_states {
            let alpha_f = alpha as f32 / 255.0;
            let mut gs = pdf.ext_graphics(state_ref);
            gs.non_stroking_alpha(alpha_f);
            gs.stroking_alpha(alpha_f);
            gs.finish();
        }

        // Write fonts
        for (font_name, embedder) in &font_embedders {
            let (type0_ref, cid_ref, desc_ref, cmap_ref, file_ref) = font_all_refs[font_name];
            embedder.embed(&mut pdf, type0_ref, cid_ref, desc_ref, cmap_ref, file_ref)?;
        }

        // Write images (each size gets its own XObject at 300 DPI)
        for (size_key, &image_ref) in &image_refs {
            let (image_name, w, h) = image_usages.get(size_key)
                .expect("size_key was inserted in first pass");
            let loaded = self.resources.get_image(image_name)?;
            self.write_image(&mut pdf, image_ref, loaded, image_name, (*w, *h))?;
        }

        // Write pages and content
        for (i, page) in self.doc.pages.iter().enumerate() {
            let page_ref = page_refs[i];
            let content_ref = content_refs[i];

            // Generate content stream
            let content_data = self.render_page_content(page, &font_embedders, &alias_to_ps, &image_refs, &alpha_states)?;

            // Write content stream
            let mut stream = pdf.stream(content_ref, &content_data);
            if self.compress {
                stream.filter(Filter::FlateDecode);
            }
            stream.finish();

            // Write page dictionary
            let mut page_dict = pdf.page(page_ref);
            page_dict.parent(page_tree_ref);
            page_dict.media_box(Rect::new(0.0, 0.0, page.width, page.height));

            // Page resources
            let mut resources = page_dict.resources();

            // Font resources
            if !font_refs.is_empty() {
                let mut fonts = resources.fonts();
                for (font_name, &font_ref) in &font_refs {
                    fonts.pair(Name(font_name.as_bytes()), font_ref);
                }
                fonts.finish();
            }

            // Image resources (XObjects)
            if !image_refs.is_empty() {
                let mut xobjects = resources.x_objects();
                for (img_name, &img_ref) in &image_refs {
                    xobjects.pair(Name(img_name.as_bytes()), img_ref);
                }
                xobjects.finish();
            }

            // Graphics state resources
            if !alpha_states.is_empty() {
                let mut ext_g = resources.ext_g_states();
                for (&alpha, &state_ref) in &alpha_states {
                    let name = format!("A{}", alpha);
                    ext_g.pair(Name(name.as_bytes()), state_ref);
                }
                ext_g.finish();
            }

            resources.finish();
            page_dict.contents(content_ref);
            page_dict.finish();
        }

        Ok(pdf.finish())
    }

    fn render_page_content(
        &self,
        page: &Page,
        font_embedders: &HashMap<String, FontEmbedder>,
        alias_to_ps: &HashMap<String, String>,
        _image_refs: &HashMap<String, Ref>,
        alpha_states: &HashMap<u8, Ref>,
    ) -> Result<Vec<u8>> {
        let mut content = Content::new();

        // Draw background if not white
        if page.background.r != 255 || page.background.g != 255 || page.background.b != 255 || page.background.a != 255 {
            let (r, g, b) = page.background.to_rgb_floats();

            // Set alpha if needed
            if page.background.a != 255 {
                let alpha_name = self.get_alpha_state_name(page.background.a, alpha_states);
                content.set_parameters(Name(alpha_name.as_bytes()));
            }

            content.set_fill_rgb(r, g, b);
            content.rect(0.0, 0.0, page.width, page.height);
            content.fill_nonzero();
        }

        // Render elements
        for element in &page.elements {
            match element {
                Element::Text(t) => {
                    self.render_text(&mut content, t, page.height, font_embedders, alias_to_ps, alpha_states)?;
                }
                Element::Rect(r) => {
                    self.render_rect(&mut content, r, page.height, alpha_states);
                }
                Element::Line(l) => {
                    self.render_line(&mut content, l, page.height, alpha_states);
                }
                Element::Image(img) => {
                    self.render_image(&mut content, img, page.height)?;
                }
                Element::Barcode(b) => {
                    self.render_barcode(&mut content, b, page.height, font_embedders, alias_to_ps, alpha_states)?;
                }
                Element::QRCode(qr) => {
                    self.render_qrcode(&mut content, qr, page.height, alpha_states)?;
                }
            }
        }

        let data = content.finish();

        if self.compress {
            // Use zlib format (not raw deflate) - PDF FlateDecode expects zlib header/checksum
            Ok(miniz_oxide::deflate::compress_to_vec_zlib(&data, 6))
        } else {
            Ok(data)
        }
    }

    fn get_alpha_state_name(&self, alpha: u8, alpha_states: &HashMap<u8, Ref>) -> String {
        // Find closest alpha state
        let closest = alpha_states.keys()
            .min_by_key(|&&a| (a as i16 - alpha as i16).abs())
            .copied()
            .unwrap_or(255);
        format!("A{}", closest)
    }

    fn render_text(
        &self,
        content: &mut Content,
        text: &TextElement,
        page_height: f32,
        font_embedders: &HashMap<String, FontEmbedder>,
        alias_to_ps: &HashMap<String, String>,
        alpha_states: &HashMap<u8, Ref>,
    ) -> Result<()> {
        let font = self.resources.get_font(&text.font)?;
        let embedder = font_embedders.get(&text.font)
            .expect("font was collected in first pass");
        let ps_name = alias_to_ps.get(&text.font)
            .expect("font alias was collected in first pass");

        // Calculate text position
        // y is top of bounding box, we need baseline
        let ascender_pts = font.ascender_pts(text.size);
        let baseline_y = page_height - text.y - ascender_pts;

        // Calculate x based on alignment
        let text_width = font.text_width(&text.text, text.size, &text.font)?;
        let x = match text.align {
            TextAlign::Left => text.x,
            TextAlign::Center => text.x - text_width / 2.0,
            TextAlign::Right => text.x - text_width,
        };

        // Set alpha if needed
        if text.color.a != 255 {
            let alpha_name = self.get_alpha_state_name(text.color.a, alpha_states);
            content.set_parameters(Name(alpha_name.as_bytes()));
        }

        // Set color and font - use PostScript name for Illustrator compatibility
        let (r, g, b) = text.color.to_rgb_floats();
        content.set_fill_rgb(r, g, b);

        content.begin_text();
        content.set_font(Name(ps_name.as_bytes()), text.size);
        content.next_line(x, baseline_y);

        // Encode text for CID font
        let encoded = embedder.encode_text(&text.text);
        content.show(Str(&encoded));
        content.end_text();

        Ok(())
    }

    fn render_rect(
        &self,
        content: &mut Content,
        rect: &RectElement,
        page_height: f32,
        alpha_states: &HashMap<u8, Ref>,
    ) {
        // Convert to PDF coordinates (bottom-left origin)
        let pdf_y = page_height - rect.y - rect.h;

        // Fill if fill_color is specified
        if let Some(fill) = &rect.fill_color {
            if fill.a != 255 {
                let alpha_name = self.get_alpha_state_name(fill.a, alpha_states);
                content.set_parameters(Name(alpha_name.as_bytes()));
            }
            let (r, g, b) = fill.to_rgb_floats();
            content.set_fill_rgb(r, g, b);
            content.rect(rect.x, pdf_y, rect.w, rect.h);
            content.fill_nonzero();
        }

        // Stroke
        if rect.stroke > 0.0 {
            if rect.stroke_color.a != 255 {
                let alpha_name = self.get_alpha_state_name(rect.stroke_color.a, alpha_states);
                content.set_parameters(Name(alpha_name.as_bytes()));
            }
            let (r, g, b) = rect.stroke_color.to_rgb_floats();
            content.set_stroke_rgb(r, g, b);
            content.set_line_width(rect.stroke);
            content.rect(rect.x, pdf_y, rect.w, rect.h);
            content.stroke();
        }
    }

    fn render_line(
        &self,
        content: &mut Content,
        line: &LineElement,
        page_height: f32,
        alpha_states: &HashMap<u8, Ref>,
    ) {
        // Convert to PDF coordinates
        let pdf_y1 = page_height - line.y1;
        let pdf_y2 = page_height - line.y2;

        if line.color.a != 255 {
            let alpha_name = self.get_alpha_state_name(line.color.a, alpha_states);
            content.set_parameters(Name(alpha_name.as_bytes()));
        }

        let (r, g, b) = line.color.to_rgb_floats();
        content.set_stroke_rgb(r, g, b);
        content.set_line_width(line.stroke);
        content.move_to(line.x1, pdf_y1);
        content.line_to(line.x2, pdf_y2);
        content.stroke();
    }

    fn render_image(
        &self,
        content: &mut Content,
        img: &ImageElement,
        page_height: f32,
    ) -> Result<()> {
        // Convert to PDF coordinates
        let pdf_y = page_height - img.y - img.h;

        // Save graphics state
        content.save_state();

        // Get the loaded image to determine scaling
        let loaded = self.resources.get_image(&img.image_ref)?;

        // Transform depends on image type:
        // - Raster images use unit coordinates (0-1), scale by target size
        // - SVG Form XObjects use native BBox coordinates, scale uniformly to fit
        let xobject_name = match loaded {
            LoadedImage::Svg { width, height, .. } => {
                // Scale uniformly to fit within target bounds (preserve aspect ratio)
                let scale_x = img.w / width;
                let scale_y = img.h / height;
                let scale = scale_x.min(scale_y); // Use smaller scale to fit

                // Center the SVG within the target bounds
                let actual_w = width * scale;
                let actual_h = height * scale;
                let offset_x = (img.w - actual_w) / 2.0;
                let offset_y = (img.h - actual_h) / 2.0;

                content.transform([scale, 0.0, 0.0, scale, img.x + offset_x, pdf_y + offset_y]);
                // SVGs use original name (vector, no per-size variants)
                img.image_ref.clone()
            }
            LoadedImage::Raster { .. } => {
                // Raster images are in unit coordinates, scale by target size
                content.transform([img.w, 0.0, 0.0, img.h, img.x, pdf_y]);
                // Raster images use size-specific key (each size embedded at 300 DPI)
                Self::image_size_key(&img.image_ref, img.w, img.h)
            }
        };

        // Draw image XObject
        content.x_object(Name(xobject_name.as_bytes()));

        // Restore graphics state
        content.restore_state();

        Ok(())
    }

    fn render_barcode(
        &self,
        content: &mut Content,
        barcode: &BarcodeElement,
        page_height: f32,
        font_embedders: &HashMap<String, FontEmbedder>,
        alias_to_ps: &HashMap<String, String>,
        _alpha_states: &HashMap<u8, Ref>,
    ) -> Result<()> {
        use barcoders::sym::code128::Code128;

        // Code128 requires a character-set prefix:
        // \u{00C0} (À) = character-set A (uppercase, control chars)
        // \u{0181} (Ɓ) = character-set B (upper/lowercase, punctuation)
        // \u{0106} (Ć) = character-set C (numeric pairs)
        // Use character-set B as default for general alphanumeric data
        let prefixed_value = format!("\u{0181}{}", barcode.value);

        // Generate barcode
        let code = Code128::new(&prefixed_value).map_err(|e| RupdfError::InvalidBarcode {
            value: barcode.value.clone(),
            reason: format!("{:?}", e),
        })?;

        let encoded = code.encode();

        // Calculate bar dimensions
        let bar_height = if barcode.human_readable {
            barcode.h - barcode.font_size - 4.0 // Leave space for text
        } else {
            barcode.h
        };

        let total_modules: usize = encoded.len();
        let module_width = barcode.w / total_modules as f32;

        // Convert y to PDF coordinates
        let bar_top_y = page_height - barcode.y;
        let bar_bottom_y = bar_top_y - bar_height;

        // Draw bars
        content.set_fill_rgb(0.0, 0.0, 0.0);

        let mut x = barcode.x;
        for &module in &encoded {
            if module == 1 {
                content.rect(x, bar_bottom_y, module_width, bar_height);
                content.fill_nonzero();
            }
            x += module_width;
        }

        // Draw human readable text
        if barcode.human_readable {
            let font = self.resources.get_font(&barcode.font)?;
            let embedder = font_embedders.get(&barcode.font)
                .expect("barcode font was collected in first pass");
            let ps_name = alias_to_ps.get(&barcode.font)
                .expect("barcode font alias was collected in first pass");

            let text_width = font.text_width(&barcode.value, barcode.font_size, &barcode.font)?;
            let text_x = barcode.x + (barcode.w - text_width) / 2.0;

            // Position text below barcode
            let ascender_pts = font.ascender_pts(barcode.font_size);
            let text_y = bar_bottom_y - 2.0 - ascender_pts;

            content.begin_text();
            content.set_font(Name(ps_name.as_bytes()), barcode.font_size);
            content.next_line(text_x, text_y);
            let encoded_text = embedder.encode_text(&barcode.value);
            content.show(Str(&encoded_text));
            content.end_text();
        }

        Ok(())
    }

    fn render_qrcode(
        &self,
        content: &mut Content,
        qr: &QRCodeElement,
        page_height: f32,
        alpha_states: &HashMap<u8, Ref>,
    ) -> Result<()> {
        use qrcode::QrCode;

        // Generate QR code
        let code = QrCode::new(qr.value.as_bytes()).map_err(|e| RupdfError::InvalidBarcode {
            value: qr.value.clone(),
            reason: format!("QR code generation failed: {}", e),
        })?;

        let matrix = code.render::<char>()
            .quiet_zone(false)
            .module_dimensions(1, 1)
            .build();

        // Parse the matrix to get dimensions
        let lines: Vec<&str> = matrix.lines().collect();
        let qr_height = lines.len();
        let qr_width = if qr_height > 0 { lines[0].chars().count() } else { 0 };

        if qr_width == 0 || qr_height == 0 {
            return Ok(());
        }

        // Calculate module size
        let module_size = qr.size / qr_width.max(qr_height) as f32;

        // Convert to PDF coordinates
        let qr_top_y = page_height - qr.y;

        // Draw background if not white
        if qr.background.r != 255 || qr.background.g != 255 || qr.background.b != 255 {
            if qr.background.a != 255 {
                let alpha_name = self.get_alpha_state_name(qr.background.a, alpha_states);
                content.set_parameters(Name(alpha_name.as_bytes()));
            }
            let (r, g, b) = qr.background.to_rgb_floats();
            content.set_fill_rgb(r, g, b);
            content.rect(qr.x, qr_top_y - qr.size, qr.size, qr.size);
            content.fill_nonzero();
        }

        // Set foreground color
        if qr.color.a != 255 {
            let alpha_name = self.get_alpha_state_name(qr.color.a, alpha_states);
            content.set_parameters(Name(alpha_name.as_bytes()));
        }
        let (r, g, b) = qr.color.to_rgb_floats();
        content.set_fill_rgb(r, g, b);

        // Draw dark modules
        for (row, line) in lines.iter().enumerate() {
            for (col, ch) in line.chars().enumerate() {
                if ch == '█' || ch == '▀' || ch == '▄' || ch == '#' {
                    let x = qr.x + col as f32 * module_size;
                    let y = qr_top_y - (row + 1) as f32 * module_size;
                    content.rect(x, y, module_size, module_size);
                }
            }
        }
        content.fill_nonzero();

        Ok(())
    }

    fn write_image(&self, pdf: &mut Pdf, image_ref: Ref, loaded: &LoadedImage, name: &str, max_size_pts: (f32, f32)) -> Result<()> {
        match loaded {
            LoadedImage::Svg { tree, .. } => {
                crate::elements::svg::write_svg_form(pdf, image_ref, tree, name)
            }
            LoadedImage::Raster { data, .. } => {
                self.write_raster_image(pdf, image_ref, data, name, max_size_pts)
            }
        }
    }

    fn write_raster_image(&self, pdf: &mut Pdf, image_ref: Ref, data: &[u8], name: &str, max_size_pts: (f32, f32)) -> Result<()> {
        // Decode image
        let img = image::load_from_memory(data).map_err(|e| {
            RupdfError::InvalidImage(name.to_string(), format!("Failed to decode: {}", e))
        })?;

        // Convert to RGB (flatten alpha against white)
        let rgb = img.to_rgb8();
        let src_width = rgb.width();
        let src_height = rgb.height();

        // Calculate target dimensions for 300 DPI
        // max_size_pts is in points (72 points per inch)
        // target_pixels = (points / 72) * 300
        let target_dpi = 300.0;
        let target_width = ((max_size_pts.0 / 72.0) * target_dpi).ceil() as u32;
        let target_height = ((max_size_pts.1 / 72.0) * target_dpi).ceil() as u32;

        // Only downscale if source is larger than target
        let (final_img, final_width, final_height) = if src_width > target_width || src_height > target_height {
            // Calculate scale to fit within target bounds while preserving aspect ratio
            let scale_x = target_width as f32 / src_width as f32;
            let scale_y = target_height as f32 / src_height as f32;
            let scale = scale_x.min(scale_y).min(1.0); // Never upscale

            let new_width = (src_width as f32 * scale).round() as u32;
            let new_height = (src_height as f32 * scale).round() as u32;

            // Use Lanczos3 for high-quality downscaling
            let resized = image::imageops::resize(
                &rgb,
                new_width,
                new_height,
                image::imageops::FilterType::Lanczos3,
            );
            (resized, new_width, new_height)
        } else {
            (rgb, src_width, src_height)
        };

        // Encode as JPEG with 85% quality
        let mut jpeg_data = Vec::new();
        let mut encoder = image::codecs::jpeg::JpegEncoder::new_with_quality(&mut jpeg_data, 85);
        encoder.encode(&final_img, final_width, final_height, image::ColorType::Rgb8).map_err(|e| {
            RupdfError::InvalidImage(name.to_string(), format!("Failed to encode JPEG: {}", e))
        })?;

        // Write image XObject
        let mut image = pdf.image_xobject(image_ref, &jpeg_data);
        image.filter(Filter::DctDecode);
        image.width(final_width as i32);
        image.height(final_height as i32);
        image.color_space().device_rgb();
        image.bits_per_component(8);
        image.finish();

        Ok(())
    }

    /// Generate a unique key for an image at a specific display size
    /// Used to embed raster images at exactly 300 DPI for each usage
    fn image_size_key(image_ref: &str, w: f32, h: f32) -> String {
        // Round to avoid floating point comparison issues
        format!("{}_{:.0}x{:.0}", image_ref, w, h)
    }
}
