mod fonts;
mod writer;

pub use fonts::FontEmbedder;
pub use writer::PdfGenerator;

#[cfg(test)]
mod tests {
    use super::*;
    use crate::resources::LoadedResources;
    use crate::types::*;

    fn make_empty_doc() -> Document {
        Document {
            metadata: Metadata::default(),
            pages: vec![Page {
                width: 612.0,
                height: 792.0,
                background: Color::white(),
                elements: vec![],
            }],
            resources: Resources::default(),
        }
    }

    fn make_rect_doc() -> Document {
        Document {
            metadata: Metadata::default(),
            pages: vec![Page {
                width: 612.0,
                height: 792.0,
                background: Color::white(),
                elements: vec![
                    Element::Rect(RectElement {
                        x: 72.0,
                        y: 72.0,
                        w: 100.0,
                        h: 50.0,
                        stroke: 1.0,
                        stroke_color: Color::black(),
                        fill_color: Some(Color { r: 200, g: 200, b: 255, a: 255 }),
                        corner_radius: 0.0,
                    }),
                ],
            }],
            resources: Resources::default(),
        }
    }

    fn make_line_doc() -> Document {
        Document {
            metadata: Metadata::default(),
            pages: vec![Page {
                width: 612.0,
                height: 792.0,
                background: Color::white(),
                elements: vec![
                    Element::Line(LineElement {
                        x1: 72.0,
                        y1: 72.0,
                        x2: 200.0,
                        y2: 150.0,
                        stroke: 2.0,
                        color: Color { r: 255, g: 0, b: 0, a: 255 },
                    }),
                ],
            }],
            resources: Resources::default(),
        }
    }

    fn make_multi_page_doc() -> Document {
        Document {
            metadata: Metadata {
                title: Some("Multi-Page Test".to_string()),
                author: Some("rupdf".to_string()),
                ..Default::default()
            },
            pages: vec![
                Page {
                    width: 612.0,
                    height: 792.0,
                    background: Color::white(),
                    elements: vec![],
                },
                Page {
                    width: 612.0,
                    height: 792.0,
                    background: Color { r: 240, g: 240, b: 255, a: 255 },
                    elements: vec![],
                },
                Page {
                    width: 595.0,
                    height: 842.0,
                    background: Color::white(),
                    elements: vec![],
                },
            ],
            resources: Resources::default(),
        }
    }

    #[test]
    fn test_empty_document_generates_valid_pdf() {
        let doc = make_empty_doc();
        let resources = LoadedResources::load(&doc.resources).unwrap();
        let generator = PdfGenerator::new(&doc, &resources, false);
        let pdf = generator.generate().unwrap();

        assert!(pdf.starts_with(b"%PDF-"), "Should start with PDF header");
        let pdf_str = String::from_utf8_lossy(&pdf);
        assert!(pdf_str.contains("%%EOF"), "Should end with EOF marker");
        assert!(pdf_str.contains("/Type /Catalog"), "Should have catalog");
        assert!(pdf_str.contains("/Type /Pages"), "Should have pages");
    }

    #[test]
    fn test_rect_document() {
        let doc = make_rect_doc();
        let resources = LoadedResources::load(&doc.resources).unwrap();
        let generator = PdfGenerator::new(&doc, &resources, false);
        let pdf = generator.generate().unwrap();

        assert!(pdf.starts_with(b"%PDF-"));
        assert!(pdf.len() > 500, "Rect document should have content");
    }

    #[test]
    fn test_line_document() {
        let doc = make_line_doc();
        let resources = LoadedResources::load(&doc.resources).unwrap();
        let generator = PdfGenerator::new(&doc, &resources, false);
        let pdf = generator.generate().unwrap();

        assert!(pdf.starts_with(b"%PDF-"));
    }

    #[test]
    fn test_multi_page_document() {
        let doc = make_multi_page_doc();
        let resources = LoadedResources::load(&doc.resources).unwrap();
        let generator = PdfGenerator::new(&doc, &resources, false);
        let pdf = generator.generate().unwrap();

        let pdf_str = String::from_utf8_lossy(&pdf);
        assert!(pdf_str.contains("/Count 3"), "Should have 3 pages");
        assert!(pdf_str.contains("Multi-Page Test"), "Should have title");
    }

    #[test]
    fn test_compression_uses_flatedecode() {
        let doc = make_multi_page_doc();
        let resources = LoadedResources::load(&doc.resources).unwrap();
        let compressed = PdfGenerator::new(&doc, &resources, true).generate().unwrap();

        let pdf_str = String::from_utf8_lossy(&compressed);
        assert!(pdf_str.contains("FlateDecode"), "Should use FlateDecode");
        assert!(compressed.starts_with(b"%PDF-"));
    }

    #[test]
    fn test_page_dimensions_in_mediabox() {
        let doc = Document {
            metadata: Metadata::default(),
            pages: vec![Page {
                width: 595.0,
                height: 842.0,
                background: Color::white(),
                elements: vec![],
            }],
            resources: Resources::default(),
        };
        let resources = LoadedResources::load(&doc.resources).unwrap();
        let pdf = PdfGenerator::new(&doc, &resources, false).generate().unwrap();

        let pdf_str = String::from_utf8_lossy(&pdf);
        assert!(pdf_str.contains("/MediaBox"), "Should have MediaBox");
        assert!(pdf_str.contains("595"), "Should have width");
        assert!(pdf_str.contains("842"), "Should have height");
    }

    #[test]
    fn test_background_color_generates_content() {
        let doc = Document {
            metadata: Metadata::default(),
            pages: vec![Page {
                width: 612.0,
                height: 792.0,
                background: Color { r: 200, g: 220, b: 255, a: 255 },
                elements: vec![],
            }],
            resources: Resources::default(),
        };
        let resources = LoadedResources::load(&doc.resources).unwrap();
        let pdf = PdfGenerator::new(&doc, &resources, false).generate().unwrap();

        assert!(pdf.len() > 200, "Should have background content");
    }
}
