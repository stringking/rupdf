mod elements;
mod error;
mod pdf;
mod resources;
mod types;

use error::PyRupdfError;
use pdf::PdfGenerator;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use resources::LoadedResources;
use types::Document;

/// Render a document to PDF bytes
///
/// Args:
///     document: A dictionary containing the document structure with pages and elements
///     compress: Whether to compress the output (default: True)
///
/// Returns:
///     bytes: The rendered PDF as bytes
///
/// Raises:
///     RupdfError: If rendering fails
#[pyfunction]
#[pyo3(signature = (document, compress = true))]
fn render_pdf<'py>(py: Python<'py>, document: &'py PyDict, compress: bool) -> PyResult<&'py PyBytes> {
    // Parse document from Python dict
    let doc = Document::from_py(document).map_err(PyErr::from)?;

    // Load resources
    let resources = LoadedResources::load(&doc.resources).map_err(PyErr::from)?;

    // Generate PDF
    let generator = PdfGenerator::new(&doc, &resources, compress);
    let pdf_bytes = generator.generate().map_err(PyErr::from)?;

    Ok(PyBytes::new(py, &pdf_bytes))
}

/// The rupdf Python module
#[pymodule]
fn _rupdf(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(render_pdf, m)?)?;
    m.add("RupdfError", py.get_type::<PyRupdfError>())?;
    Ok(())
}
