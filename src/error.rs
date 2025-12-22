use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use thiserror::Error;

/// All errors raised by rupdf
#[derive(Error, Debug)]
pub enum RupdfError {
    #[error("Missing font: '{0}'")]
    MissingFont(String),

    #[error("Missing image: '{0}'")]
    MissingImage(String),

    #[error("Missing glyph '{glyph}' in font '{font}'")]
    MissingGlyph { glyph: char, font: String },

    #[error("Invalid font data for '{0}': {1}")]
    InvalidFont(String, String),

    #[error("Invalid image data for '{0}': {1}")]
    InvalidImage(String, String),

    #[error("Invalid page size: width={width}, height={height}")]
    InvalidPageSize { width: f32, height: f32 },

    #[error("Invalid barcode value '{value}': {reason}")]
    InvalidBarcode { value: String, reason: String },

    #[error("Unknown element type: '{0}'")]
    UnknownElementType(String),

    #[error("Invalid document structure: {0}")]
    InvalidDocument(String),

    #[error("Resource error: {0}")]
    ResourceError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("PDF generation error: {0}")]
    PdfError(String),
}

pyo3::create_exception!(rupdf, PyRupdfError, PyException);

impl From<RupdfError> for PyErr {
    fn from(err: RupdfError) -> PyErr {
        PyRupdfError::new_err(err.to_string())
    }
}

pub type Result<T> = std::result::Result<T, RupdfError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_display_missing_font() {
        let err = RupdfError::MissingFont("Arial".to_string());
        assert_eq!(err.to_string(), "Missing font: 'Arial'");
    }

    #[test]
    fn test_error_display_missing_glyph() {
        let err = RupdfError::MissingGlyph { glyph: '中', font: "Arial".to_string() };
        assert_eq!(err.to_string(), "Missing glyph '中' in font 'Arial'");
    }

    #[test]
    fn test_error_display_invalid_page_size() {
        let err = RupdfError::InvalidPageSize { width: -10.0, height: 792.0 };
        assert_eq!(err.to_string(), "Invalid page size: width=-10, height=792");
    }

    #[test]
    fn test_error_display_invalid_barcode() {
        let err = RupdfError::InvalidBarcode {
            value: "test\x00".to_string(),
            reason: "null bytes not allowed".to_string()
        };
        assert!(err.to_string().contains("null bytes not allowed"));
    }

    #[test]
    fn test_error_display_unknown_element() {
        let err = RupdfError::UnknownElementType("circle".to_string());
        assert_eq!(err.to_string(), "Unknown element type: 'circle'");
    }
}
