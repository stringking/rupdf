use crate::error::{Result, RupdfError};
use crate::types::{FontSource, ImageSource, Resources};
use std::collections::HashMap;
use std::fs;

/// Loaded font data with parsed metrics
pub struct LoadedFont {
    pub data: Vec<u8>,
    pub postscript_name: String,           // Actual PostScript name from font file
    pub units_per_em: u16,
    pub ascender: i16,
    pub descender: i16,
    pub cap_height: i16,                   // Height of capital letters
    pub glyph_widths: HashMap<u16, u16>, // glyph_id -> advance width
    pub cmap: HashMap<char, u16>,         // char -> glyph_id
}

impl LoadedFont {
    pub fn load(name: &str, source: &FontSource) -> Result<Self> {
        let data = match source {
            FontSource::Path(path) => fs::read(path).map_err(|e| {
                RupdfError::InvalidFont(name.to_string(), format!("Failed to read file: {}", e))
            })?,
            FontSource::Bytes(bytes) => bytes.clone(),
        };

        let face = ttf_parser::Face::parse(&data, 0).map_err(|e| {
            RupdfError::InvalidFont(name.to_string(), format!("Failed to parse font: {}", e))
        })?;

        let units_per_em = face.units_per_em();
        let ascender = face.ascender();
        let descender = face.descender();

        // Get cap height from OS/2 table, or estimate from 'H' glyph, or fallback to 70% of ascender
        let cap_height = face.capital_height()
            .map(|h| h as i16)
            .or_else(|| {
                // Try to get height of 'H' glyph
                face.glyph_index('H')
                    .and_then(|gid| face.glyph_bounding_box(gid))
                    .map(|bbox| bbox.y_max)
            })
            .unwrap_or_else(|| (ascender as f32 * 0.7) as i16);

        // Extract PostScript name from name table (name_id 6)
        let postscript_name = face
            .names()
            .into_iter()
            .find(|n| n.name_id == 6 && n.is_unicode())
            .and_then(|n| n.to_string())
            .unwrap_or_else(|| name.to_string()); // Fall back to user's name

        // Build character to glyph mapping
        let mut cmap = HashMap::new();
        let mut glyph_widths = HashMap::new();

        if let Some(subtable) = face.tables().cmap {
            for subtable in subtable.subtables {
                if subtable.is_unicode() {
                    subtable.codepoints(|cp| {
                        if let Some(ch) = char::from_u32(cp) {
                            if let Some(glyph_id) = subtable.glyph_index(cp) {
                                cmap.insert(ch, glyph_id.0);
                            }
                        }
                    });
                }
            }
        }

        // Get advance widths for all glyphs
        for glyph_id in 0..face.number_of_glyphs() {
            if let Some(advance) = face.glyph_hor_advance(ttf_parser::GlyphId(glyph_id)) {
                glyph_widths.insert(glyph_id, advance);
            }
        }

        Ok(Self {
            data,
            postscript_name,
            units_per_em,
            ascender,
            descender,
            cap_height,
            glyph_widths,
            cmap,
        })
    }

    /// Get glyph ID for a character, returns error if missing
    pub fn glyph_id(&self, ch: char, font_name: &str) -> Result<u16> {
        self.cmap.get(&ch).copied().ok_or_else(|| RupdfError::MissingGlyph {
            glyph: ch,
            font: font_name.to_string(),
        })
    }

    /// Get advance width for a glyph
    pub fn advance_width(&self, glyph_id: u16) -> u16 {
        self.glyph_widths.get(&glyph_id).copied().unwrap_or(0)
    }

    /// Calculate text width in points
    pub fn text_width(&self, text: &str, size: f32, font_name: &str) -> Result<f32> {
        let scale = size / self.units_per_em as f32;
        let mut width = 0.0;
        for ch in text.chars() {
            let glyph_id = self.glyph_id(ch, font_name)?;
            width += self.advance_width(glyph_id) as f32 * scale;
        }
        Ok(width)
    }

    /// Get ascender in points for given font size
    pub fn ascender_pts(&self, size: f32) -> f32 {
        self.ascender as f32 * size / self.units_per_em as f32
    }

    /// Get cap height in points for given font size
    pub fn cap_height_pts(&self, size: f32) -> f32 {
        self.cap_height as f32 * size / self.units_per_em as f32
    }

    /// Get descender in points for given font size (returns negative value)
    pub fn descender_pts(&self, size: f32) -> f32 {
        self.descender as f32 * size / self.units_per_em as f32
    }

    /// Wrap text to fit within max_width, returning lines
    pub fn wrap_text(&self, text: &str, size: f32, max_width: f32, font_name: &str) -> Result<Vec<String>> {
        let mut lines = Vec::new();

        for paragraph in text.split('\n') {
            if paragraph.is_empty() {
                lines.push(String::new());
                continue;
            }

            let words: Vec<&str> = paragraph.split_whitespace().collect();
            if words.is_empty() {
                lines.push(String::new());
                continue;
            }

            let mut current_line = String::new();
            let mut current_width = 0.0;
            let space_width = self.text_width(" ", size, font_name)?;

            for word in words {
                let word_width = self.text_width(word, size, font_name)?;

                if current_line.is_empty() {
                    // First word on line - always add it (even if too wide)
                    current_line = word.to_string();
                    current_width = word_width;
                } else if current_width + space_width + word_width <= max_width {
                    // Word fits
                    current_line.push(' ');
                    current_line.push_str(word);
                    current_width += space_width + word_width;
                } else {
                    // Word doesn't fit - start new line
                    lines.push(current_line);
                    current_line = word.to_string();
                    current_width = word_width;
                }
            }

            if !current_line.is_empty() {
                lines.push(current_line);
            }
        }

        Ok(lines)
    }
}

/// Loaded image data
pub enum LoadedImage {
    Svg {
        tree: usvg::Tree,
        width: f32,
        height: f32,
    },
    Raster {
        data: Vec<u8>,
        width: u32,
        height: u32,
    },
}

impl LoadedImage {
    pub fn load(name: &str, source: &ImageSource) -> Result<Self> {
        let data = match source {
            ImageSource::Path(path) => fs::read(path).map_err(|e| {
                RupdfError::InvalidImage(name.to_string(), format!("Failed to read file: {}", e))
            })?,
            ImageSource::Bytes(bytes) => bytes.clone(),
        };

        // Check if it's SVG by looking for XML/SVG markers
        if Self::is_svg(&data) {
            let tree = usvg::Tree::from_data(&data, &usvg::Options::default()).map_err(|e| {
                RupdfError::InvalidImage(name.to_string(), format!("Failed to parse SVG: {}", e))
            })?;
            let size = tree.size;
            return Ok(LoadedImage::Svg {
                tree,
                width: size.width() as f32,
                height: size.height() as f32,
            });
        }

        // Try to decode as raster image
        let img = image::load_from_memory(&data).map_err(|e| {
            RupdfError::InvalidImage(name.to_string(), format!("Failed to decode image: {}", e))
        })?;

        Ok(LoadedImage::Raster {
            data,
            width: img.width(),
            height: img.height(),
        })
    }

    fn is_svg(data: &[u8]) -> bool {
        // Check for SVG file markers
        let s = std::str::from_utf8(data).unwrap_or("");
        let trimmed = s.trim_start();
        trimmed.starts_with("<?xml") || trimmed.starts_with("<svg") || trimmed.starts_with("<!DOCTYPE svg")
    }

    /// Get the source dimensions of the image in points
    /// For SVGs, returns the viewBox/size dimensions
    /// For raster images, returns pixel dimensions (1 pixel = 1 point at 72 DPI)
    pub fn dimensions(&self) -> (f32, f32) {
        match self {
            LoadedImage::Svg { width, height, .. } => (*width, *height),
            LoadedImage::Raster { width, height, .. } => (*width as f32, *height as f32),
        }
    }
}

/// All loaded resources for rendering
pub struct LoadedResources {
    pub fonts: HashMap<String, LoadedFont>,
    pub images: HashMap<String, LoadedImage>,
}

impl LoadedResources {
    pub fn load(resources: &Resources) -> Result<Self> {
        let mut fonts = HashMap::new();
        let mut images = HashMap::new();

        for (name, source) in &resources.fonts {
            fonts.insert(name.clone(), LoadedFont::load(name, source)?);
        }

        for (name, source) in &resources.images {
            images.insert(name.clone(), LoadedImage::load(name, source)?);
        }

        Ok(Self { fonts, images })
    }

    pub fn get_font(&self, name: &str) -> Result<&LoadedFont> {
        self.fonts
            .get(name)
            .ok_or_else(|| RupdfError::MissingFont(name.to_string()))
    }

    pub fn get_image(&self, name: &str) -> Result<&LoadedImage> {
        self.images
            .get(name)
            .ok_or_else(|| RupdfError::MissingImage(name.to_string()))
    }
}
