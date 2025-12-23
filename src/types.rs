use crate::error::{Result, RupdfError};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList, PyTuple};
use std::collections::HashMap;

/// RGBA color with values 0-255
#[derive(Debug, Clone, Copy)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
}

impl Color {
    pub fn black() -> Self {
        Self { r: 0, g: 0, b: 0, a: 255 }
    }

    pub fn white() -> Self {
        Self { r: 255, g: 255, b: 255, a: 255 }
    }

    /// Convert to RGB floats (0.0-1.0) for PDF
    pub fn to_rgb_floats(&self) -> (f32, f32, f32) {
        (
            self.r as f32 / 255.0,
            self.g as f32 / 255.0,
            self.b as f32 / 255.0,
        )
    }

    /// Get alpha as float (0.0-1.0)
    #[allow(dead_code)]
    pub fn alpha(&self) -> f32 {
        self.a as f32 / 255.0
    }
}

impl<'source> FromPyObject<'source> for Color {
    fn extract(ob: &'source PyAny) -> PyResult<Self> {
        let tuple = ob.downcast::<PyTuple>()?;
        if tuple.len() != 4 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Color must be a 4-tuple (r, g, b, a)",
            ));
        }
        Ok(Self {
            r: tuple.get_item(0)?.extract()?,
            g: tuple.get_item(1)?.extract()?,
            b: tuple.get_item(2)?.extract()?,
            a: tuple.get_item(3)?.extract()?,
        })
    }
}

/// Text alignment
#[derive(Debug, Clone, Copy, Default)]
pub enum TextAlign {
    #[default]
    Left,
    Center,
    Right,
}

impl<'source> FromPyObject<'source> for TextAlign {
    fn extract(ob: &'source PyAny) -> PyResult<Self> {
        let s: String = ob.extract()?;
        match s.as_str() {
            "left" => Ok(TextAlign::Left),
            "center" => Ok(TextAlign::Center),
            "right" => Ok(TextAlign::Right),
            _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid alignment: '{}'. Must be 'left', 'center', or 'right'",
                s
            ))),
        }
    }
}

/// Vertical anchor for text positioning
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub enum VerticalAnchor {
    #[default]
    Baseline,  // y is the text baseline
    Capline,   // y is the top of capital letters (cap height)
    Center,    // y is the midpoint between baseline and capline
}

impl<'source> FromPyObject<'source> for VerticalAnchor {
    fn extract(ob: &'source PyAny) -> PyResult<Self> {
        let s: String = ob.extract()?;
        match s.as_str() {
            "baseline" => Ok(VerticalAnchor::Baseline),
            "capline" => Ok(VerticalAnchor::Capline),
            "center" => Ok(VerticalAnchor::Center),
            _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid vertical_anchor: '{}'. Must be 'baseline', 'capline', or 'center'",
                s
            ))),
        }
    }
}

/// Box horizontal alignment (determines how x relates to box position)
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub enum BoxAlignX {
    #[default]
    Left,   // x is left edge of box
    Center, // x is center of box
    Right,  // x is right edge of box
}

impl<'source> FromPyObject<'source> for BoxAlignX {
    fn extract(ob: &'source PyAny) -> PyResult<Self> {
        let s: String = ob.extract()?;
        match s.as_str() {
            "left" => Ok(BoxAlignX::Left),
            "center" => Ok(BoxAlignX::Center),
            "right" => Ok(BoxAlignX::Right),
            _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid box_align_x: '{}'. Must be 'left', 'center', or 'right'",
                s
            ))),
        }
    }
}

/// Box vertical alignment (determines how y relates to box position)
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub enum BoxAlignY {
    #[default]
    Top,    // y is top edge of box
    Center, // y is center of box
    Bottom, // y is bottom edge of box
}

impl<'source> FromPyObject<'source> for BoxAlignY {
    fn extract(ob: &'source PyAny) -> PyResult<Self> {
        let s: String = ob.extract()?;
        match s.as_str() {
            "top" => Ok(BoxAlignY::Top),
            "center" => Ok(BoxAlignY::Center),
            "bottom" => Ok(BoxAlignY::Bottom),
            _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid box_align_y: '{}'. Must be 'top', 'center', or 'bottom'",
                s
            ))),
        }
    }
}

/// Text vertical alignment inside a TextBox
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub enum TextAlignY {
    Top,      // ascender of first line at box top
    Capline,  // cap height of first line at box top
    Center,   // text block vertically centered in box
    #[default]
    Baseline, // last baseline at box bottom
    Bottom,   // descender of last line at box bottom
}

impl<'source> FromPyObject<'source> for TextAlignY {
    fn extract(ob: &'source PyAny) -> PyResult<Self> {
        let s: String = ob.extract()?;
        match s.as_str() {
            "top" => Ok(TextAlignY::Top),
            "capline" => Ok(TextAlignY::Capline),
            "center" => Ok(TextAlignY::Center),
            "baseline" => Ok(TextAlignY::Baseline),
            "bottom" => Ok(TextAlignY::Bottom),
            _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid text_align_y: '{}'. Must be 'top', 'capline', 'center', 'baseline', or 'bottom'",
                s
            ))),
        }
    }
}

/// Text element
#[derive(Debug, Clone)]
pub struct TextElement {
    pub x: f32,
    pub y: f32,
    pub text: String,
    pub font: String,
    pub size: f32,
    pub color: Color,
    pub align: TextAlign,
    pub vertical_anchor: VerticalAnchor,
}

/// Rectangle element
#[derive(Debug, Clone)]
pub struct RectElement {
    pub x: f32,
    pub y: f32,
    pub w: f32,
    pub h: f32,
    pub stroke: f32,
    pub stroke_color: Color,
    pub fill_color: Option<Color>,
    pub corner_radius: f32,
}

/// Line element
#[derive(Debug, Clone)]
pub struct LineElement {
    pub x1: f32,
    pub y1: f32,
    pub x2: f32,
    pub y2: f32,
    pub stroke: f32,
    pub color: Color,
}

/// Image element
#[derive(Debug, Clone)]
pub struct ImageElement {
    pub x: f32,
    pub y: f32,
    pub w: Option<f32>,  // If only w provided, scale preserving aspect ratio
    pub h: Option<f32>,  // If only h provided, scale preserving aspect ratio
    pub image_ref: String,
    pub align: TextAlign,  // Horizontal alignment: left (default), center, right
}

/// Barcode element (Code 128)
#[derive(Debug, Clone)]
pub struct BarcodeElement {
    pub x: f32,
    pub y: f32,
    pub w: f32,
    pub h: f32,
    pub value: String,
    pub human_readable: bool,
    pub font: String,
    pub font_size: f32,
}

/// QR Code element
#[derive(Debug, Clone)]
pub struct QRCodeElement {
    pub x: f32,
    pub y: f32,
    pub size: f32,  // QR codes are square
    pub value: String,
    pub color: Color,       // Foreground color (dark modules)
    pub background: Color,  // Background color (light modules)
}

/// TextBox element - multi-line text with word wrapping
#[derive(Debug, Clone)]
pub struct TextBoxElement {
    pub x: f32,
    pub y: f32,
    pub w: f32,
    pub h: f32,
    pub box_align_x: BoxAlignX,
    pub box_align_y: BoxAlignY,
    pub text_align_x: TextAlign,
    pub text_align_y: TextAlignY,
    pub text: String,
    pub font: String,
    pub size: f32,
    pub line_height: f32,
    pub color: Color,
}

/// All element types
#[derive(Debug, Clone)]
pub enum Element {
    Text(TextElement),
    TextBox(TextBoxElement),
    Rect(RectElement),
    Line(LineElement),
    Image(ImageElement),
    Barcode(BarcodeElement),
    QRCode(QRCodeElement),
}

/// A single page
#[derive(Debug, Clone)]
pub struct Page {
    pub width: f32,
    pub height: f32,
    pub background: Color,
    pub elements: Vec<Element>,
}

/// Document metadata
#[derive(Debug, Clone, Default)]
pub struct Metadata {
    pub title: Option<String>,
    pub author: Option<String>,
    pub subject: Option<String>,
    pub creator: Option<String>,
    pub creation_date: Option<String>,
}

/// Font resource - either path or bytes
#[derive(Debug, Clone)]
pub enum FontSource {
    Path(String),
    Bytes(Vec<u8>),
}

/// Image resource - either path or bytes
#[derive(Debug, Clone)]
pub enum ImageSource {
    Path(String),
    Bytes(Vec<u8>),
}

/// All resources for a document
#[derive(Debug, Clone, Default)]
pub struct Resources {
    pub fonts: HashMap<String, FontSource>,
    pub images: HashMap<String, ImageSource>,
}

/// Complete document
#[derive(Debug, Clone)]
pub struct Document {
    pub metadata: Metadata,
    pub pages: Vec<Page>,
    pub resources: Resources,
}

// Parsing helpers

fn get_optional<'py, T: FromPyObject<'py>>(
    dict: &'py PyDict,
    key: &str,
) -> PyResult<Option<T>> {
    match dict.get_item(key) {
        Some(val) if !val.is_none() => Ok(Some(val.extract()?)),
        _ => Ok(None),
    }
}

fn get_required<'py, T: FromPyObject<'py>>(
    dict: &'py PyDict,
    key: &str,
) -> PyResult<T> {
    dict.get_item(key)
        .ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("Missing required key: '{}'", key))
        })?
        .extract()
}

/// Convert PyResult to our Result, wrapping errors in InvalidDocument
fn to_doc_err<T>(result: PyResult<T>) -> Result<T> {
    result.map_err(|e| RupdfError::InvalidDocument(e.to_string()))
}

/// Get a required field from dict, returning InvalidDocument error on failure
fn req<'py, T: FromPyObject<'py>>(dict: &'py PyDict, key: &str) -> Result<T> {
    to_doc_err(get_required(dict, key))
}

/// Get an optional field from dict with a default value
fn opt_or<'py, T: FromPyObject<'py>>(dict: &'py PyDict, key: &str, default: T) -> Result<T> {
    to_doc_err(get_optional(dict, key)).map(|o| o.unwrap_or(default))
}

/// Get an optional field from dict with Default::default()
fn opt_default<'py, T: FromPyObject<'py> + Default>(dict: &'py PyDict, key: &str) -> Result<T> {
    to_doc_err(get_optional(dict, key)).map(|o| o.unwrap_or_default())
}

/// Get an optional field from dict
fn opt<'py, T: FromPyObject<'py>>(dict: &'py PyDict, key: &str) -> Result<Option<T>> {
    to_doc_err(get_optional(dict, key))
}

/// Helper to add element index context to errors
fn with_element_context<T>(result: Result<T>, index: usize) -> Result<T> {
    result.map_err(|e| {
        RupdfError::InvalidDocument(format!("Element {}: {}", index, e))
    })
}

impl Element {
    #[allow(dead_code)]
    pub fn from_py(dict: &PyDict) -> Result<Self> {
        Self::from_py_indexed(dict, 0)
    }

    pub fn from_py_indexed(dict: &PyDict, index: usize) -> Result<Self> {
        let element_type: String = with_element_context(req(dict, "type"), index)?;

        match element_type.as_str() {
            "text" => Ok(Element::Text(TextElement {
                x: with_element_context(req(dict, "x"), index)?,
                y: with_element_context(req(dict, "y"), index)?,
                text: with_element_context(req(dict, "text"), index)?,
                font: with_element_context(req(dict, "font"), index)?,
                size: with_element_context(req(dict, "size"), index)?,
                color: with_element_context(opt_or(dict, "color", Color::black()), index)?,
                align: with_element_context(opt_default(dict, "align"), index)?,
                vertical_anchor: with_element_context(opt_default(dict, "vertical_anchor"), index)?,
            })),

            "textbox" => {
                let size: f32 = with_element_context(req(dict, "size"), index)?;
                let line_height: f32 = with_element_context(opt_or(dict, "line_height", size * 1.2), index)?;
                Ok(Element::TextBox(TextBoxElement {
                    x: with_element_context(req(dict, "x"), index)?,
                    y: with_element_context(req(dict, "y"), index)?,
                    w: with_element_context(req(dict, "w"), index)?,
                    h: with_element_context(req(dict, "h"), index)?,
                    box_align_x: with_element_context(opt_default(dict, "box_align_x"), index)?,
                    box_align_y: with_element_context(opt_default(dict, "box_align_y"), index)?,
                    text_align_x: with_element_context(opt_default(dict, "text_align_x"), index)?,
                    text_align_y: with_element_context(opt_default(dict, "text_align_y"), index)?,
                    text: with_element_context(req(dict, "text"), index)?,
                    font: with_element_context(req(dict, "font"), index)?,
                    size,
                    line_height,
                    color: with_element_context(opt_or(dict, "color", Color::black()), index)?,
                }))
            }

            "rect" => Ok(Element::Rect(RectElement {
                x: with_element_context(req(dict, "x"), index)?,
                y: with_element_context(req(dict, "y"), index)?,
                w: with_element_context(req(dict, "w"), index)?,
                h: with_element_context(req(dict, "h"), index)?,
                stroke: with_element_context(opt_or(dict, "stroke", 1.0), index)?,
                stroke_color: with_element_context(opt_or(dict, "stroke_color", Color::black()), index)?,
                fill_color: with_element_context(opt(dict, "fill_color"), index)?,
                corner_radius: with_element_context(opt_or(dict, "corner_radius", 0.0), index)?,
            })),

            "line" => Ok(Element::Line(LineElement {
                x1: with_element_context(req(dict, "x1"), index)?,
                y1: with_element_context(req(dict, "y1"), index)?,
                x2: with_element_context(req(dict, "x2"), index)?,
                y2: with_element_context(req(dict, "y2"), index)?,
                stroke: with_element_context(opt_or(dict, "stroke", 1.0), index)?,
                color: with_element_context(opt_or(dict, "color", Color::black()), index)?,
            })),

            "image" => {
                let align_str: String = with_element_context(opt_or(dict, "align", "left".to_string()), index)?;
                let align = match align_str.as_str() {
                    "center" => TextAlign::Center,
                    "right" => TextAlign::Right,
                    _ => TextAlign::Left,
                };
                Ok(Element::Image(ImageElement {
                    x: with_element_context(req(dict, "x"), index)?,
                    y: with_element_context(req(dict, "y"), index)?,
                    w: with_element_context(opt(dict, "w"), index)?,
                    h: with_element_context(opt(dict, "h"), index)?,
                    image_ref: with_element_context(req(dict, "image_ref"), index)?,
                    align,
                }))
            }

            "barcode" | "barcode128" => Ok(Element::Barcode(BarcodeElement {
                x: with_element_context(req(dict, "x"), index)?,
                y: with_element_context(req(dict, "y"), index)?,
                w: with_element_context(req(dict, "w"), index)?,
                h: with_element_context(req(dict, "h"), index)?,
                value: with_element_context(req(dict, "value"), index)?,
                human_readable: with_element_context(opt_or(dict, "human_readable", false), index)?,
                font: with_element_context(opt_or(dict, "font", "mono".to_string()), index)?,
                font_size: with_element_context(opt_or(dict, "font_size", 10.0), index)?,
            })),

            "qrcode" | "qr" => Ok(Element::QRCode(QRCodeElement {
                x: with_element_context(req(dict, "x"), index)?,
                y: with_element_context(req(dict, "y"), index)?,
                size: with_element_context(req(dict, "size"), index)?,
                value: with_element_context(req(dict, "value"), index)?,
                color: with_element_context(opt_or(dict, "color", Color::black()), index)?,
                background: with_element_context(opt_or(dict, "background", Color::white()), index)?,
            })),

            _ => Err(RupdfError::UnknownElementType(format!("Element {}: {}", index, element_type))),
        }
    }
}

impl Page {
    pub fn from_py(dict: &PyDict) -> Result<Self> {
        let size: (f32, f32) = req(dict, "size")?;

        if size.0 <= 0.0 || size.1 <= 0.0 {
            return Err(RupdfError::InvalidPageSize {
                width: size.0,
                height: size.1,
            });
        }

        let background = opt_or(dict, "background", Color::white())?;
        let elements_list: Option<&PyList> = opt(dict, "elements")?;

        let mut elements = Vec::new();
        if let Some(list) = elements_list {
            for (i, item) in list.iter().enumerate() {
                let elem_dict = item.downcast::<PyDict>()
                    .map_err(|_| RupdfError::InvalidDocument(format!("Element {} must be a dict", i)))?;
                elements.push(Element::from_py_indexed(elem_dict, i)?);
            }
        }

        Ok(Self {
            width: size.0,
            height: size.1,
            background,
            elements,
        })
    }
}

impl Metadata {
    pub fn from_py(dict: &PyDict) -> Result<Self> {
        Ok(Self {
            title: opt(dict, "title")?,
            author: opt(dict, "author")?,
            subject: opt(dict, "subject")?,
            creator: opt(dict, "creator")?,
            creation_date: opt(dict, "creation_date")?,
        })
    }
}

impl Resources {
    pub fn from_py(dict: &PyDict) -> Result<Self> {
        let mut resources = Self::default();

        // Parse fonts
        if let Some(fonts_dict) = opt::<&PyDict>(dict, "fonts")? {
            for (key, value) in fonts_dict.iter() {
                let name: String = key.extract()
                    .map_err(|e| RupdfError::InvalidDocument(format!("Font key must be string: {}", e)))?;
                let font_dict = value.downcast::<PyDict>()
                    .map_err(|_| RupdfError::InvalidDocument("Font value must be a dict".to_string()))?;

                let path: Option<String> = opt(font_dict, "path")?;
                let bytes: Option<&PyBytes> = opt(font_dict, "bytes")?;

                let source = match (path, bytes) {
                    (Some(p), None) => FontSource::Path(p),
                    (None, Some(b)) => FontSource::Bytes(b.as_bytes().to_vec()),
                    (Some(_), Some(_)) => {
                        return Err(RupdfError::ResourceError(format!(
                            "Font '{}' has both 'path' and 'bytes'; only one is allowed", name
                        )));
                    }
                    (None, None) => {
                        return Err(RupdfError::ResourceError(format!(
                            "Font '{}' must have either 'path' or 'bytes'", name
                        )));
                    }
                };
                resources.fonts.insert(name, source);
            }
        }

        // Parse images
        if let Some(images_dict) = opt::<&PyDict>(dict, "images")? {
            for (key, value) in images_dict.iter() {
                let name: String = key.extract()
                    .map_err(|e| RupdfError::InvalidDocument(format!("Image key must be string: {}", e)))?;
                let image_dict = value.downcast::<PyDict>()
                    .map_err(|_| RupdfError::InvalidDocument("Image value must be a dict".to_string()))?;

                let path: Option<String> = opt(image_dict, "path")?;
                let bytes: Option<&PyBytes> = opt(image_dict, "bytes")?;

                let source = match (path, bytes) {
                    (Some(p), None) => ImageSource::Path(p),
                    (None, Some(b)) => ImageSource::Bytes(b.as_bytes().to_vec()),
                    (Some(_), Some(_)) => {
                        return Err(RupdfError::ResourceError(format!(
                            "Image '{}' has both 'path' and 'bytes'; only one is allowed", name
                        )));
                    }
                    (None, None) => {
                        return Err(RupdfError::ResourceError(format!(
                            "Image '{}' must have either 'path' or 'bytes'", name
                        )));
                    }
                };
                resources.images.insert(name, source);
            }
        }

        Ok(resources)
    }
}

impl Document {
    pub fn from_py(dict: &PyDict) -> Result<Self> {
        // Parse metadata (optional)
        let metadata = match opt::<&PyDict>(dict, "metadata")? {
            Some(meta_dict) => Metadata::from_py(meta_dict)?,
            None => Metadata::default(),
        };

        // Parse pages (required)
        let pages_list: &PyList = req(dict, "pages")?;
        let mut pages = Vec::with_capacity(pages_list.len());
        for (i, item) in pages_list.iter().enumerate() {
            let page_dict = item.downcast::<PyDict>()
                .map_err(|_| RupdfError::InvalidDocument(format!("Page {} must be a dict", i)))?;
            pages.push(Page::from_py(page_dict)?);
        }

        // Parse resources (optional)
        let resources = match opt::<&PyDict>(dict, "resources")? {
            Some(res_dict) => Resources::from_py(res_dict)?,
            None => Resources::default(),
        };

        Ok(Self { metadata, pages, resources })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_color_black() {
        let c = Color::black();
        assert_eq!(c.r, 0);
        assert_eq!(c.g, 0);
        assert_eq!(c.b, 0);
        assert_eq!(c.a, 255);
    }

    #[test]
    fn test_color_white() {
        let c = Color::white();
        assert_eq!(c.r, 255);
        assert_eq!(c.g, 255);
        assert_eq!(c.b, 255);
        assert_eq!(c.a, 255);
    }

    #[test]
    fn test_color_to_rgb_floats() {
        let c = Color { r: 255, g: 128, b: 0, a: 255 };
        let (r, g, b) = c.to_rgb_floats();
        assert!((r - 1.0).abs() < 0.001);
        assert!((g - 0.502).abs() < 0.01);
        assert!((b - 0.0).abs() < 0.001);
    }

    #[test]
    fn test_color_alpha() {
        let c = Color { r: 0, g: 0, b: 0, a: 127 };
        let alpha = c.alpha();
        assert!((alpha - 0.498).abs() < 0.01);
    }

    #[test]
    fn test_text_align_default() {
        let align = TextAlign::default();
        assert!(matches!(align, TextAlign::Left));
    }

    #[test]
    fn test_metadata_default() {
        let meta = Metadata::default();
        assert!(meta.title.is_none());
        assert!(meta.author.is_none());
        assert!(meta.subject.is_none());
        assert!(meta.creator.is_none());
    }

    #[test]
    fn test_resources_default() {
        let res = Resources::default();
        assert!(res.fonts.is_empty());
        assert!(res.images.is_empty());
    }
}
