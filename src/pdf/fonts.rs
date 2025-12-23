use crate::error::{Result, RupdfError};
use crate::resources::LoadedFont;
use pdf_writer::types::{CidFontType, FontFlags, SystemInfo, UnicodeCmap};
use pdf_writer::{Filter, Finish, Name, Pdf, Ref, Str};
use std::collections::{BTreeMap, HashSet};

/// Handles font embedding into PDF
pub struct FontEmbedder<'a> {
    font: &'a LoadedFont,
    font_name: &'a str,
    used_glyphs: HashSet<u16>,
    char_to_glyph: BTreeMap<char, u16>,
}

impl<'a> FontEmbedder<'a> {
    pub fn new(font: &'a LoadedFont, font_name: &'a str) -> Self {
        Self {
            font,
            font_name,
            used_glyphs: HashSet::new(),
            char_to_glyph: BTreeMap::new(),
        }
    }

    /// Register a character as used (call for each char in text)
    pub fn use_char(&mut self, ch: char) -> Result<u16> {
        let glyph_id = self.font.glyph_id(ch, self.font_name)?;
        self.used_glyphs.insert(glyph_id);
        self.char_to_glyph.insert(ch, glyph_id);
        Ok(glyph_id)
    }

    /// Register all characters in a string (skips control characters like newlines)
    pub fn use_text(&mut self, text: &str) -> Result<()> {
        for ch in text.chars() {
            // Skip control characters (newlines, tabs, etc.) - they have no glyphs
            if ch.is_control() {
                continue;
            }
            self.use_char(ch)?;
        }
        Ok(())
    }

    /// Embed the font into the PDF and return the font dictionary reference
    pub fn embed(
        &self,
        pdf: &mut Pdf,
        font_ref: Ref,
        cid_font_ref: Ref,
        descriptor_ref: Ref,
        cmap_ref: Ref,
        font_file_ref: Ref,
    ) -> Result<()> {
        // Subset the font
        let subset_data = self.subset_font()?;

        // Build glyph widths array
        let widths = self.build_widths();

        // Write CMap (ToUnicode)
        let cmap_data = self.build_to_unicode_cmap();
        pdf.stream(cmap_ref, &cmap_data);

        // Write font file stream
        pdf.stream(font_file_ref, &subset_data).filter(Filter::FlateDecode);

        // Write font descriptor - use actual PostScript name for compatibility
        let ps_name = &self.font.postscript_name;
        let mut descriptor = pdf.font_descriptor(descriptor_ref);
        descriptor.name(Name(ps_name.as_bytes()));
        descriptor.flags(FontFlags::SYMBOLIC);
        descriptor.bbox(pdf_writer::Rect::new(-500.0, -300.0, 1500.0, 1000.0));
        descriptor.italic_angle(0.0);
        descriptor.ascent(self.font.ascender as f32);
        descriptor.descent(self.font.descender as f32);
        descriptor.cap_height(self.font.ascender as f32 * 0.8);
        descriptor.stem_v(80.0);
        descriptor.font_file2(font_file_ref);
        descriptor.finish();

        // Write CID font
        let mut cid_font = pdf.cid_font(cid_font_ref);
        cid_font.subtype(CidFontType::Type2);
        cid_font.base_font(Name(ps_name.as_bytes()));
        cid_font.system_info(SystemInfo {
            registry: Str(b"Adobe"),
            ordering: Str(b"Identity"),
            supplement: 0,
        });
        cid_font.font_descriptor(descriptor_ref);
        cid_font.default_width(1000.0);

        // Write widths
        if !widths.is_empty() {
            let mut w = cid_font.widths();
            for (glyph_id, width) in &widths {
                w.consecutive(*glyph_id, [*width as f32].into_iter());
            }
            w.finish();
        }
        cid_font.cid_to_gid_map_predefined(Name(b"Identity"));
        cid_font.finish();

        // Write Type0 font
        let mut type0 = pdf.type0_font(font_ref);
        type0.base_font(Name(ps_name.as_bytes()));
        type0.encoding_predefined(Name(b"Identity-H"));
        type0.descendant_font(cid_font_ref);
        type0.to_unicode(cmap_ref);
        type0.finish();

        Ok(())
    }

    fn subset_font(&self) -> Result<Vec<u8>> {
        // Collect glyph IDs to keep
        let glyph_ids: Vec<u16> = self.used_glyphs.iter().copied().collect();

        // Use subsetter to create subset
        let profile = subsetter::Profile::pdf(&glyph_ids);
        let subset = subsetter::subset(&self.font.data, 0, profile).map_err(|e| {
            RupdfError::InvalidFont(
                self.font_name.to_string(),
                format!("Failed to subset font: {:?}", e),
            )
        })?;

        // Compress with zlib (not raw deflate) - PDF FlateDecode expects zlib format
        let compressed = miniz_oxide::deflate::compress_to_vec_zlib(&subset, 6);
        Ok(compressed)
    }

    fn build_widths(&self) -> Vec<(u16, u16)> {
        let mut widths: Vec<(u16, u16)> = self
            .used_glyphs
            .iter()
            .map(|&gid| {
                let width = self.font.advance_width(gid);
                // Scale to 1000 units (PDF standard)
                let scaled = (width as f32 * 1000.0 / self.font.units_per_em as f32) as u16;
                (gid, scaled)
            })
            .collect();
        widths.sort_by_key(|(gid, _)| *gid);
        widths
    }

    fn build_to_unicode_cmap(&self) -> Vec<u8> {
        let info = SystemInfo {
            registry: Str(b"Adobe"),
            ordering: Str(b"UCS"),
            supplement: 0,
        };
        let mut cmap = UnicodeCmap::new(Name(b"Adobe-Identity-UCS"), info);
        for (&ch, &glyph_id) in &self.char_to_glyph {
            cmap.pair(glyph_id, ch);
        }
        cmap.finish()
    }

    /// Encode text as PDF hex string for CID font
    pub fn encode_text(&self, text: &str) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(text.len() * 2);
        for ch in text.chars() {
            if let Some(&glyph_id) = self.char_to_glyph.get(&ch) {
                bytes.push((glyph_id >> 8) as u8);
                bytes.push((glyph_id & 0xFF) as u8);
            }
        }
        bytes
    }
}
