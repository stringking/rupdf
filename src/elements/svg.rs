//! SVG to PDF vector conversion

use crate::error::Result;
use pdf_writer::{Content, Finish, Pdf, Rect, Ref};
use usvg::{NodeKind, Paint, PathSegment, Tree};

/// Log a warning about an unsupported SVG feature (to stderr)
fn warn_unsupported(feature: &str) {
    eprintln!("rupdf warning: SVG feature not supported: {}", feature);
}

/// Convert an SVG tree to a PDF Form XObject containing vector paths
pub fn write_svg_form(
    pdf: &mut Pdf,
    form_ref: Ref,
    tree: &Tree,
    _name: &str,
) -> Result<()> {
    let size = tree.size;
    let width = size.width() as f32;
    let height = size.height() as f32;

    // Generate content stream with SVG paths
    let content_data = render_svg_to_content(tree, height)?;

    // Compress the content
    let compressed = miniz_oxide::deflate::compress_to_vec_zlib(&content_data, 6);

    // Write as Form XObject
    let mut form = pdf.form_xobject(form_ref, &compressed);
    form.filter(pdf_writer::Filter::FlateDecode);
    form.bbox(Rect::new(0.0, 0.0, width, height));
    form.finish();

    Ok(())
}

/// Render SVG tree to PDF content stream bytes
fn render_svg_to_content(tree: &Tree, svg_height: f32) -> Result<Vec<u8>> {
    let mut content = Content::new();

    // Walk the SVG tree and render each node
    render_node(&tree.root, &mut content, svg_height);

    Ok(content.finish())
}

/// Recursively render a usvg node to PDF content
fn render_node(node: &usvg::Node, content: &mut Content, svg_height: f32) {
    match &*node.borrow() {
        NodeKind::Path(path) => {
            render_path(path, content, svg_height);
        }
        NodeKind::Group(group) => {
            // Save state if there's a transform
            let has_transform = group.transform != usvg::Transform::default();
            if has_transform {
                content.save_state();
                apply_transform(&group.transform, content);
            }

            // Render children
            for child in node.children() {
                render_node(&child, content, svg_height);
            }

            if has_transform {
                content.restore_state();
            }
        }
        NodeKind::Image(_) => {
            warn_unsupported("embedded image in SVG");
        }
        NodeKind::Text(_) => {
            warn_unsupported("text element in SVG (convert text to paths for best results)");
        }
    }
}

/// Render a single SVG path to PDF
fn render_path(path: &usvg::Path, content: &mut Content, svg_height: f32) {
    // Apply path-level transform if present
    let has_transform = path.transform != usvg::Transform::default();
    if has_transform {
        content.save_state();
        apply_transform(&path.transform, content);
    }

    // Build the path
    let data = &path.data;
    for segment in data.segments() {
        match segment {
            PathSegment::MoveTo { x, y } => {
                content.move_to(x as f32, svg_height - y as f32);
            }
            PathSegment::LineTo { x, y } => {
                content.line_to(x as f32, svg_height - y as f32);
            }
            PathSegment::CurveTo { x1, y1, x2, y2, x, y } => {
                content.cubic_to(
                    x1 as f32, svg_height - y1 as f32,
                    x2 as f32, svg_height - y2 as f32,
                    x as f32, svg_height - y as f32,
                );
            }
            PathSegment::ClosePath => {
                content.close_path();
            }
        }
    }

    // Determine fill and stroke
    let has_fill = path.fill.is_some();
    let has_stroke = path.stroke.is_some();

    // Set fill color if present
    if let Some(ref fill) = path.fill {
        match fill.paint {
            Paint::Color(color) => {
                let r = color.red as f32 / 255.0;
                let g = color.green as f32 / 255.0;
                let b = color.blue as f32 / 255.0;
                content.set_fill_rgb(r, g, b);
            }
            Paint::LinearGradient(_) => warn_unsupported("linear gradient fill"),
            Paint::RadialGradient(_) => warn_unsupported("radial gradient fill"),
            Paint::Pattern(_) => warn_unsupported("pattern fill"),
        }
    }

    // Set stroke properties if present
    if let Some(ref stroke) = path.stroke {
        match stroke.paint {
            Paint::Color(color) => {
                let r = color.red as f32 / 255.0;
                let g = color.green as f32 / 255.0;
                let b = color.blue as f32 / 255.0;
                content.set_stroke_rgb(r, g, b);
            }
            Paint::LinearGradient(_) => warn_unsupported("linear gradient stroke"),
            Paint::RadialGradient(_) => warn_unsupported("radial gradient stroke"),
            Paint::Pattern(_) => warn_unsupported("pattern stroke"),
        }
        content.set_line_width(stroke.width.get() as f32);
    }

    // Apply fill and/or stroke
    match (has_fill, has_stroke) {
        (true, true) => {
            content.fill_nonzero_and_stroke();
        }
        (true, false) => {
            content.fill_nonzero();
        }
        (false, true) => {
            content.stroke();
        }
        (false, false) => {
            // No fill or stroke, just define the path (shouldn't normally happen)
            content.end_path();
        }
    }

    if has_transform {
        content.restore_state();
    }
}

/// Apply a usvg transform to PDF content
fn apply_transform(transform: &usvg::Transform, content: &mut Content) {
    // usvg transform is [a, b, c, d, e, f] which maps to:
    // | a c e |
    // | b d f |
    // | 0 0 1 |
    // PDF transform uses the same matrix format
    content.transform([
        transform.a as f32,
        transform.b as f32,
        transform.c as f32,
        transform.d as f32,
        transform.e as f32,
        transform.f as f32,
    ]);
}
