# rupdf

A fast, minimal PDF renderer in Rust with Python bindings. Takes pre-laid-out pages and renders them to PDF bytes.

## Features

- **Text** with TTF/OTF fonts, horizontal/vertical alignment, and colors
- **Rectangles** with stroke, fill, and rounded corners
- **Lines** with configurable width
- **Images** (PNG, JPEG, WebP, SVG)
- **Barcodes** (Code 128) and **QR codes**
- **Font subsetting** - embeds only used glyphs
- **Compression** - optional zlib compression

## Installation

```bash
pip install rupdf
```

## Usage

```python
import rupdf

doc = {
    "metadata": {
        "title": "My Document",
        "author": "Jane Doe"
    },
    "pages": [
        {
            "size": (612, 792),  # Letter size in points
            "background": (255, 255, 255, 255),
            "elements": [
                {
                    "type": "text",
                    "x": 72,
                    "y": 72,
                    "text": "Hello, World!",
                    "font": "main",
                    "size": 24,
                    "color": (0, 0, 0, 255)
                },
                {
                    "type": "rect",
                    "x": 72,
                    "y": 120,
                    "w": 200,
                    "h": 100,
                    "stroke": 1.0,
                    "stroke_color": (0, 0, 0, 255),
                    "fill_color": (240, 240, 240, 255)
                }
            ]
        }
    ],
    "resources": {
        "fonts": {
            "main": {"path": "/path/to/font.ttf"}
            # Or: "main": {"bytes": font_bytes}
        },
        "images": {
            "logo": {"path": "/path/to/logo.png"}
            # Or: "logo": {"bytes": image_bytes}
        }
    }
}

# Render to PDF bytes
pdf_bytes = rupdf.render_pdf(doc, compress=True)

# Write to file
with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## Coordinate System

- Origin: **top-left** corner of the page
- Units: **points** (1 point = 1/72 inch)
- Y-axis: increases **downward**

Common page sizes:
- Letter: 612 x 792 points
- A4: 595 x 842 points

## Element Types

### Text

```python
{
    "type": "text",
    "x": 72,
    "y": 72,
    "text": "Hello",
    "font": "font_ref",           # Reference to fonts in resources
    "size": 12,                   # Font size in points
    "color": (0, 0, 0, 255),      # RGBA (optional, default black)
    "align": "left",              # "left", "center", or "right" (optional)
    "vertical_anchor": "baseline" # "baseline", "capline", or "center" (optional)
}
```

**Positioning:**
- `(x, y)` specifies the anchor point of the text
- `align` controls horizontal alignment relative to x:
  - `"left"` (default): text extends to the right of x
  - `"center"`: text is centered on x
  - `"right"`: text extends to the left of x
- `vertical_anchor` controls vertical alignment relative to y:
  - `"baseline"` (default): y is the text baseline
  - `"capline"`: y is the top of capital letters
  - `"center"`: y is the vertical center of capital letters

### TextBox

Multi-line text with word wrapping, like Illustrator's "area type".

```python
{
    "type": "textbox",
    "x": 72,
    "y": 72,
    "w": 200,
    "h": 100,
    "text": "Long text that will wrap within the box...",
    "font": "font_ref",
    "size": 12,
    "line_height": 14.4,          # Optional, default = size * 1.2
    "color": (0, 0, 0, 255),      # Optional, default black

    # Box alignment (how the box is positioned relative to x, y)
    "box_align_x": "left",        # "left", "center", or "right" (optional)
    "box_align_y": "top",         # "top", "center", or "bottom" (optional)

    # Text alignment (how text is positioned inside the box)
    "text_align_x": "left",       # "left", "center", or "right" (optional)
    "text_align_y": "baseline"    # "top", "capline", "center", "baseline", or "bottom" (optional)
}
```

**Two-Layer Alignment:**

1. **Box alignment** - positions the box relative to `(x, y)`:
   - `box_align_x`: left=x is left edge, center=x is center, right=x is right edge
   - `box_align_y`: top=y is top edge, center=y is center, bottom=y is bottom edge

2. **Text alignment** - positions text inside the box:
   - `text_align_x`: per-line horizontal alignment (left/center/right)
   - `text_align_y`: vertical alignment of the text block:
     - `"top"`: ascender of first line at box top
     - `"capline"`: cap height of first line at box top
     - `"center"`: text block vertically centered
     - `"baseline"` (default): last line's baseline at box bottom
     - `"bottom"`: descender of last line at box bottom

**Notes:**
- Text wraps at word boundaries to fit within `w`
- Overflow is clipped to box bounds
- Explicit `\n` in text creates line breaks

### Rectangle

```python
{
    "type": "rect",
    "x": 72,
    "y": 72,
    "w": 100,
    "h": 50,
    "stroke": 1.0,                     # Stroke width (0 for no stroke)
    "stroke_color": (0, 0, 0, 255),    # Optional
    "fill_color": (255, 255, 255, 255), # Optional
    "corner_radius": 10                # Optional, for rounded corners
}
```

**Notes:**
- `(x, y)` is the top-left corner
- `corner_radius` creates rounded corners; automatically clamped to half the smallest dimension

### Line

```python
{
    "type": "line",
    "x1": 72,
    "y1": 72,
    "x2": 200,
    "y2": 72,
    "stroke": 1.0,
    "color": (0, 0, 0, 255)
}
```

### Image

```python
{
    "type": "image",
    "x": 72,
    "y": 72,
    "w": 200,
    "h": 150,
    "image_ref": "logo"  # Reference to images in resources
}
```

Supported formats: PNG, JPEG, WebP (rasterized to 300 DPI), SVG (rendered as vectors).

### Barcode (Code 128)

```python
{
    "type": "barcode",
    "x": 72,
    "y": 72,
    "w": 200,
    "h": 60,
    "value": "ABC-123",
    "human_readable": True,  # Show text below barcode
    "font": "font_ref",      # Required if human_readable
    "font_size": 10
}
```

### QR Code

```python
{
    "type": "qrcode",
    "x": 72,
    "y": 72,
    "size": 100,             # QR codes are square
    "value": "https://example.com",
    "color": (0, 0, 0, 255),       # Foreground (dark modules)
    "background": (255, 255, 255, 255)  # Background (light modules)
}
```

## Error Handling

```python
try:
    pdf = rupdf.render_pdf(doc)
except rupdf.RupdfError as e:
    print(f"Failed to render: {e}")
```

Common errors:
- Missing font or image reference
- Invalid page dimensions
- Missing required element fields
- Character not found in font

## Performance

Benchmarks comparing rupdf to ReportLab (10 iterations each):

| Benchmark | rupdf | ReportLab | Speedup |
|-----------|-------|-----------|---------|
| Empty page | 0.02ms | 0.27ms | 13x |
| 50 text lines | 0.82ms | 0.82ms | 1x |
| 100 rectangles | 0.19ms | 1.02ms | 5x |
| 10 pages | 1.62ms | 3.80ms | 2x |

## Development

```bash
# Build
maturin develop

# Run tests
cargo test                    # Rust unit tests
pytest python/tests/ -v       # Python tests

# Generate test PDF with all element types
python scripts/generate_test_pdf.py                          # Without images
python scripts/generate_test_pdf.py --svg logo.svg --png photo.png  # With images

# Benchmarks
python benchmarks/run_benchmark.py
```

## License

MIT
