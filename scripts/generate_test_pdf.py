#!/usr/bin/env python3
"""Generate a comprehensive test PDF demonstrating all rupdf features.

Usage:
    python scripts/generate_test_pdf.py [options]

Options:
    -o, --output PATH    Output PDF path (default: all_elements_test.pdf)
    --svg PATH           Path to an SVG image to include
    --png PATH           Path to a PNG/JPEG/WebP image to include
    -h, --help           Show this help message

Examples:
    python scripts/generate_test_pdf.py
    python scripts/generate_test_pdf.py -o test.pdf --svg logo.svg --png photo.png
    python scripts/generate_test_pdf.py --png ~/Pictures/sample.jpg
"""

import argparse
import sys
from pathlib import Path

import rupdf

# Font paths - adjust these for your system
FONT_PATHS = {
    "sans": "/Users/lee/Downloads/ibm-plex-sans/fonts/complete/ttf/IBMPlexSans-Regular.ttf",
    "sans-bold": "/Users/lee/Downloads/ibm-plex-sans/fonts/complete/ttf/IBMPlexSans-Bold.ttf",
    "mono": "/Users/lee/Downloads/ibm-plex-mono/fonts/complete/ttf/IBMPlexMono-Regular.ttf",
}


def get_available_fonts() -> dict:
    """Return dict of available fonts."""
    fonts = {}
    for name, path in FONT_PATHS.items():
        if Path(path).exists():
            fonts[name] = {"path": path}
    return fonts


def build_document(fonts: dict, images: dict) -> dict:
    """Build a comprehensive test document with all element types."""
    if not fonts:
        print("Error: No fonts available. Please update FONT_PATHS in this script.")
        sys.exit(1)

    # Use first available font as default
    default_font = list(fonts.keys())[0]

    # Page dimensions (Letter size)
    W, H = 612, 792
    MARGIN = 72

    elements_page1 = []
    elements_page2 = []
    y = MARGIN

    # === PAGE 1 ===

    # Title
    elements_page1.append({
        "type": "text",
        "x": W / 2,
        "y": y,
        "text": "rupdf - All Elements Test",
        "font": default_font,
        "size": 24,
        "color": (0, 0, 0, 255),
        "align": "center",
    })
    y += 40

    # Subtitle
    elements_page1.append({
        "type": "text",
        "x": W / 2,
        "y": y,
        "text": "Comprehensive test of all supported element types",
        "font": default_font,
        "size": 12,
        "color": (100, 100, 100, 255),
        "align": "center",
    })
    y += 40

    # --- TEXT SECTION ---
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y,
        "text": "Text Elements",
        "font": default_font,
        "size": 16,
        "color": (0, 0, 128, 255),
    })
    y += 25

    # Left-aligned text
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y,
        "text": "Left-aligned text (default)",
        "font": default_font,
        "size": 12,
        "color": (0, 0, 0, 255),
        "align": "left",
    })
    y += 18

    # Center-aligned text
    elements_page1.append({
        "type": "text",
        "x": W / 2,
        "y": y,
        "text": "Center-aligned text",
        "font": default_font,
        "size": 12,
        "color": (0, 0, 0, 255),
        "align": "center",
    })
    y += 18

    # Right-aligned text
    elements_page1.append({
        "type": "text",
        "x": W - MARGIN,
        "y": y,
        "text": "Right-aligned text",
        "font": default_font,
        "size": 12,
        "color": (0, 0, 0, 255),
        "align": "right",
    })
    y += 18

    # Colored text
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y,
        "text": "Red text",
        "font": default_font,
        "size": 12,
        "color": (200, 0, 0, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 80,
        "y": y,
        "text": "Green text",
        "font": default_font,
        "size": 12,
        "color": (0, 150, 0, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 170,
        "y": y,
        "text": "Blue text",
        "font": default_font,
        "size": 12,
        "color": (0, 0, 200, 255),
    })
    y += 35

    # --- RECTANGLE SECTION ---
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y,
        "text": "Rectangle Elements",
        "font": default_font,
        "size": 16,
        "color": (0, 0, 128, 255),
    })
    y += 25

    # Stroke only
    elements_page1.append({
        "type": "rect",
        "x": MARGIN,
        "y": y,
        "w": 80,
        "h": 50,
        "stroke": 2,
        "stroke_color": (0, 0, 0, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 40,
        "y": y + 55,
        "text": "Stroke only",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })

    # Fill only
    elements_page1.append({
        "type": "rect",
        "x": MARGIN + 100,
        "y": y,
        "w": 80,
        "h": 50,
        "stroke": 0,
        "fill_color": (100, 149, 237, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 140,
        "y": y + 55,
        "text": "Fill only",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })

    # Stroke + Fill
    elements_page1.append({
        "type": "rect",
        "x": MARGIN + 200,
        "y": y,
        "w": 80,
        "h": 50,
        "stroke": 2,
        "stroke_color": (0, 0, 0, 255),
        "fill_color": (255, 215, 0, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 240,
        "y": y + 55,
        "text": "Stroke + Fill",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })

    # 50% Alpha
    elements_page1.append({
        "type": "rect",
        "x": MARGIN + 300,
        "y": y,
        "w": 80,
        "h": 50,
        "stroke": 0,
        "fill_color": (255, 0, 0, 127),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 340,
        "y": y + 55,
        "text": "50% Alpha",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })

    # Verify alpha isolation - this rect should be fully opaque
    elements_page1.append({
        "type": "rect",
        "x": MARGIN + 400,
        "y": y,
        "w": 80,
        "h": 50,
        "stroke": 0,
        "fill_color": (0, 128, 0, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 440,
        "y": y + 55,
        "text": "Opaque after",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })
    y += 80

    # --- LINE SECTION ---
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y,
        "text": "Line Elements",
        "font": default_font,
        "size": 16,
        "color": (0, 0, 128, 255),
    })
    y += 25

    # Various lines
    elements_page1.append({
        "type": "line",
        "x1": MARGIN,
        "y1": y,
        "x2": MARGIN + 150,
        "y2": y,
        "stroke": 1,
        "color": (0, 0, 0, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 160,
        "y": y - 4,
        "text": "1pt black",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
    })
    y += 15

    elements_page1.append({
        "type": "line",
        "x1": MARGIN,
        "y1": y,
        "x2": MARGIN + 150,
        "y2": y,
        "stroke": 3,
        "color": (200, 0, 0, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 160,
        "y": y - 4,
        "text": "3pt red",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
    })
    y += 15

    elements_page1.append({
        "type": "line",
        "x1": MARGIN,
        "y1": y,
        "x2": MARGIN + 150,
        "y2": y + 20,
        "stroke": 2,
        "color": (0, 0, 200, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 160,
        "y": y + 5,
        "text": "2pt blue diagonal",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
    })
    y += 45

    # --- BARCODE SECTION ---
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y,
        "text": "Barcode Elements (Code 128)",
        "font": default_font,
        "size": 16,
        "color": (0, 0, 128, 255),
    })
    y += 25

    # Barcode without human-readable text
    elements_page1.append({
        "type": "barcode",
        "x": MARGIN,
        "y": y,
        "w": 200,
        "h": 50,
        "value": "ABC-12345",
        "human_readable": False,
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y + 55,
        "text": "Without text",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
    })

    # Barcode with human-readable text
    elements_page1.append({
        "type": "barcode",
        "x": MARGIN + 250,
        "y": y,
        "w": 200,
        "h": 60,
        "value": "XYZ-67890",
        "human_readable": True,
        "font": default_font,
        "font_size": 10,
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 250,
        "y": y + 65,
        "text": "With human-readable text",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
    })
    y += 90

    # --- QR CODE SECTION ---
    elements_page1.append({
        "type": "text",
        "x": MARGIN,
        "y": y,
        "text": "QR Code Elements",
        "font": default_font,
        "size": 16,
        "color": (0, 0, 128, 255),
    })
    y += 25

    # Default QR code
    elements_page1.append({
        "type": "qrcode",
        "x": MARGIN,
        "y": y,
        "size": 80,
        "value": "Hello, World!",
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 40,
        "y": y + 85,
        "text": "Default colors",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })

    # Custom colored QR code
    elements_page1.append({
        "type": "qrcode",
        "x": MARGIN + 120,
        "y": y,
        "size": 80,
        "value": "Custom colors",
        "color": (0, 100, 0, 255),
        "background": (220, 255, 220, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 160,
        "y": y + 85,
        "text": "Green on light green",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })

    # URL QR code
    elements_page1.append({
        "type": "qrcode",
        "x": MARGIN + 240,
        "y": y,
        "size": 80,
        "value": "https://github.com",
        "color": (0, 0, 139, 255),
        "background": (255, 255, 255, 255),
    })
    elements_page1.append({
        "type": "text",
        "x": MARGIN + 280,
        "y": y + 85,
        "text": "URL (dark blue)",
        "font": default_font,
        "size": 9,
        "color": (0, 0, 0, 255),
        "align": "center",
    })

    # === PAGE 2 ===
    y2 = MARGIN

    # Title
    elements_page2.append({
        "type": "text",
        "x": W / 2,
        "y": y2,
        "text": "Page 2 - Images",
        "font": default_font,
        "size": 24,
        "color": (0, 0, 0, 255),
        "align": "center",
    })
    y2 += 50

    # --- IMAGE SECTION ---
    if images:
        elements_page2.append({
            "type": "text",
            "x": MARGIN,
            "y": y2,
            "text": "Image Elements",
            "font": default_font,
            "size": 16,
            "color": (0, 0, 128, 255),
        })
        y2 += 25

        if "svg" in images:
            elements_page2.append({
                "type": "text",
                "x": MARGIN,
                "y": y2,
                "text": "SVG (vector):",
                "font": default_font,
                "size": 12,
                "color": (0, 0, 0, 255),
            })
            y2 += 20

            elements_page2.append({
                "type": "image",
                "x": MARGIN,
                "y": y2,
                "w": 200,
                "h": 100,
                "image_ref": "svg",
            })
            y2 += 120

        if "raster" in images:
            elements_page2.append({
                "type": "text",
                "x": MARGIN,
                "y": y2,
                "text": "Raster image (PNG/JPEG/WebP) at different sizes:",
                "font": default_font,
                "size": 12,
                "color": (0, 0, 0, 255),
            })
            y2 += 20

            # Small
            elements_page2.append({
                "type": "image",
                "x": MARGIN,
                "y": y2,
                "w": 50,
                "h": 50,
                "image_ref": "raster",
            })

            # Medium
            elements_page2.append({
                "type": "image",
                "x": MARGIN + 70,
                "y": y2,
                "w": 100,
                "h": 100,
                "image_ref": "raster",
            })

            # Large
            elements_page2.append({
                "type": "image",
                "x": MARGIN + 190,
                "y": y2,
                "w": 150,
                "h": 150,
                "image_ref": "raster",
            })
            y2 += 170
    else:
        elements_page2.append({
            "type": "text",
            "x": MARGIN,
            "y": y2,
            "text": "(No images provided - use --svg and --png to include images)",
            "font": default_font,
            "size": 12,
            "color": (150, 150, 150, 255),
        })
        y2 += 30

    # Footer on page 2
    elements_page2.append({
        "type": "text",
        "x": W / 2,
        "y": H - MARGIN,
        "text": "Generated by rupdf",
        "font": default_font,
        "size": 10,
        "color": (150, 150, 150, 255),
        "align": "center",
    })

    return {
        "metadata": {
            "title": "rupdf All Elements Test",
            "author": "rupdf test suite",
            "subject": "Comprehensive test of all PDF element types",
        },
        "pages": [
            {
                "size": (W, H),
                "background": (255, 255, 255, 255),
                "elements": elements_page1,
            },
            {
                "size": (W, H),
                "background": (255, 255, 255, 255),
                "elements": elements_page2,
            },
        ],
        "resources": {
            "fonts": fonts,
            "images": images,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive test PDF demonstrating all rupdf features.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s
    %(prog)s -o test.pdf --svg logo.svg --png photo.png
    %(prog)s --png ~/Pictures/sample.jpg
        """,
    )
    parser.add_argument(
        "-o", "--output",
        default="all_elements_test.pdf",
        help="Output PDF path (default: all_elements_test.pdf)",
    )
    parser.add_argument(
        "--svg",
        metavar="PATH",
        help="Path to an SVG image to include",
    )
    parser.add_argument(
        "--png",
        metavar="PATH",
        help="Path to a raster image (PNG/JPEG/WebP) to include",
    )

    args = parser.parse_args()

    # Gather fonts
    fonts = get_available_fonts()
    if not fonts:
        print("Error: No fonts available. Please update FONT_PATHS in this script.")
        sys.exit(1)

    # Gather images from arguments
    images = {}
    if args.svg:
        svg_path = Path(args.svg)
        if not svg_path.exists():
            print(f"Error: SVG file not found: {args.svg}")
            sys.exit(1)
        images["svg"] = {"path": str(svg_path.resolve())}

    if args.png:
        png_path = Path(args.png)
        if not png_path.exists():
            print(f"Error: Raster image not found: {args.png}")
            sys.exit(1)
        images["raster"] = {"path": str(png_path.resolve())}

    print("Building document...")
    doc = build_document(fonts, images)

    print(f"Rendering PDF with {len(doc['pages'])} pages...")
    pdf_bytes = rupdf.render_pdf(doc, compress=True)

    print(f"Writing {len(pdf_bytes):,} bytes to {args.output}")
    with open(args.output, "wb") as f:
        f.write(pdf_bytes)

    print("Done!")


if __name__ == "__main__":
    main()
