#!/usr/bin/env python3
"""
Generate a comprehensive demonstration PDF showcasing all rupdf capabilities.

This serves as both:
1. A test to verify all features work correctly
2. A visual reference for all element types and options
"""

import sys
import os

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rupdf import render_pdf

# Page dimensions (Letter size)
PAGE_W = 612
PAGE_H = 792

# Margins
MARGIN = 50
CONTENT_W = PAGE_W - 2 * MARGIN

# Project paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

# Font paths (IBM Plex)
FONT_SANS = os.path.join(ASSETS_DIR, "IBMPlexSans-Regular.otf")
FONT_SANS_BOLD = os.path.join(ASSETS_DIR, "IBMPlexSans-Bold.otf")
FONT_MONO = os.path.join(ASSETS_DIR, "IBMPlexMono-Regular.otf")
FONT_MONO_BOLD = os.path.join(ASSETS_DIR, "IBMPlexMono-Bold.otf")

# Image paths
SVG_PATH = os.path.join(ASSETS_DIR, "test-svg.svg")
PNG_PATH = os.path.join(ASSETS_DIR, "test-png.png")


def page_header(title: str, subtitle: str = "") -> list:
    """Create a consistent page header."""
    elements = [
        # Title
        {
            "type": "text",
            "x": PAGE_W / 2, "y": 50,
            "text": title,
            "font": "sans-bold", "size": 24,
            "align": "center",
            "vertical_anchor": "capline"
        },
    ]
    if subtitle:
        elements.append({
            "type": "text",
            "x": PAGE_W / 2, "y": 88,
            "text": subtitle,
            "font": "sans", "size": 11,
            "align": "center",
            "color": (100, 100, 100, 255)
        })
    # Divider line
    elements.append({
        "type": "line",
        "x1": MARGIN, "y1": 108,
        "x2": PAGE_W - MARGIN, "y2": 108,
        "stroke": 0.5, "color": (200, 200, 200, 255)
    })
    return elements


def section_label(x: float, y: float, text: str) -> dict:
    """Create a section label."""
    return {
        "type": "text",
        "x": x, "y": y,
        "text": text,
        "font": "sans-bold", "size": 9,
        "color": (100, 100, 100, 255)
    }


# =============================================================================
# PAGE 1: Title Page
# =============================================================================
def make_title_page() -> dict:
    elements = [
        # Main title
        {
            "type": "text",
            "x": PAGE_W / 2, "y": 220,
            "text": "rupdf",
            "font": "sans-bold", "size": 72,
            "align": "center",
            "vertical_anchor": "capline"
        },
        # Subtitle with nice gap
        {
            "type": "text",
            "x": PAGE_W / 2, "y": 310,
            "text": "A fast, minimal PDF renderer",
            "font": "sans", "size": 18,
            "align": "center",
            "color": (80, 80, 80, 255)
        },
        # Feature list
        {
            "type": "textbox",
            "x": PAGE_W / 2, "y": 380,
            "w": 300, "h": 220,
            "box_align_x": "center",
            "text_align_x": "center",
            "text_align_y": "top",
            "text": "TextBox with word wrapping\nRectangles with rounded corners\nLines\nImages (PNG, JPEG, WebP, SVG)\nBarcodes (Code 128)\nQR Codes\nFont subsetting\nCompression",
            "font": "sans", "size": 14,
            "line_height": 24,
            "color": (60, 60, 60, 255)
        },
        # PyPI URL
        {
            "type": "text",
            "x": PAGE_W / 2, "y": PAGE_H - 80,
            "text": "pypi.org/project/rupdf",
            "font": "mono", "size": 10,
            "align": "center",
            "color": (150, 150, 150, 255)
        },
        # GitHub URL
        {
            "type": "text",
            "x": PAGE_W / 2, "y": PAGE_H - 60,
            "text": "github.com/stringking/rupdf",
            "font": "mono", "size": 10,
            "align": "center",
            "color": (150, 150, 150, 255)
        },
    ]
    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 2: Text Element
# =============================================================================
def make_text_page() -> dict:
    elements = page_header("Text Element", "Single-line text with alignment options")
    y = 130

    # Horizontal alignment
    elements.append(section_label(MARGIN, y, "Horizontal Alignment (align)"))
    y += 15

    # Reference line at x=306 (center)
    center_x = PAGE_W / 2
    elements.append({
        "type": "line",
        "x1": center_x, "y1": y, "x2": center_x, "y2": y + 60,
        "stroke": 1, "color": (200, 200, 200, 255)
    })
    elements.append({
        "type": "text", "x": center_x + 5, "y": y - 3,
        "text": f"x = {center_x}", "font": "sans", "size": 8,
        "color": (150, 150, 150, 255)
    })

    for i, align in enumerate(["left", "center", "right"]):
        ty = y + 15 + i * 20
        elements.append({
            "type": "text",
            "x": center_x, "y": ty,
            "text": f'align="{align}"',
            "font": "sans", "size": 14,
            "align": align
        })

    y += 125  # Extra spacing between sections

    # Vertical anchor
    elements.append(section_label(MARGIN, y, "Vertical Anchor (vertical_anchor)"))
    y += 20

    # Reference line
    ref_y = y + 10
    elements.append({
        "type": "line",
        "x1": MARGIN, "y1": ref_y, "x2": PAGE_W - MARGIN, "y2": ref_y,
        "stroke": 2, "color": (255, 100, 100, 255)
    })
    elements.append({
        "type": "text", "x": MARGIN, "y": ref_y - 12,
        "text": f"y = {ref_y} (red line)", "font": "sans", "size": 8,
        "color": (255, 100, 100, 255)
    })

    anchors = [
        ("baseline", MARGIN + 20),
        ("capline", MARGIN + 140),
        ("center", MARGIN + 260),
    ]
    for anchor, x in anchors:
        elements.append({
            "type": "text",
            "x": x, "y": ref_y,
            "text": anchor.capitalize(),
            "font": "sans", "size": 18,
            "vertical_anchor": anchor
        })

    y += 100  # Extra spacing between sections

    # Font sizes
    elements.append(section_label(MARGIN, y, "Font Sizes"))
    y += 15
    sizes = [8, 10, 12, 14, 18, 24, 36]
    x = MARGIN
    for size in sizes:
        elements.append({
            "type": "text",
            "x": x, "y": y,
            "text": f"{size}pt",
            "font": "sans", "size": size,
            "vertical_anchor": "capline"
        })
        x += size * 3 + 10

    y += 90  # Extra spacing between sections

    # Colors
    elements.append(section_label(MARGIN, y, "Colors (RGBA)"))
    y += 15
    colors = [
        ((0, 0, 0, 255), "Black"),
        ((255, 0, 0, 255), "Red"),
        ((0, 128, 0, 255), "Green"),
        ((0, 0, 255, 255), "Blue"),
        ((128, 0, 128, 255), "Purple"),
        ((0, 0, 0, 128), "50% Alpha"),
    ]
    x = MARGIN
    for color, name in colors:
        elements.append({
            "type": "text",
            "x": x, "y": y,
            "text": name,
            "font": "sans", "size": 12,
            "color": color
        })
        x += 80

    y += 80  # Extra spacing between sections

    # Combined example
    elements.append(section_label(MARGIN, y, "Combined Example"))
    y += 15
    # Crosshair at anchor point
    anchor_x, anchor_y = 200, y + 20
    elements.append({
        "type": "line",
        "x1": anchor_x - 20, "y1": anchor_y, "x2": anchor_x + 20, "y2": anchor_y,
        "stroke": 1, "color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "line",
        "x1": anchor_x, "y1": anchor_y - 20, "x2": anchor_x, "y2": anchor_y + 20,
        "stroke": 1, "color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "text",
        "x": anchor_x, "y": anchor_y,
        "text": "Center/Center",
        "font": "sans", "size": 16,
        "align": "center",
        "vertical_anchor": "center",
        "color": (0, 100, 200, 255)
    })
    elements.append({
        "type": "text", "x": anchor_x + 25, "y": anchor_y - 25,
        "text": f"({anchor_x}, {anchor_y})", "font": "sans", "size": 8,
        "color": (255, 0, 0, 255)
    })

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 3: TextBox Element
# =============================================================================
def make_textbox_page() -> dict:
    elements = page_header("TextBox Element", "Multi-line text with word wrapping")
    y = 130

    sample_text = "This is a TextBox with automatic word wrapping. Text flows within the box boundaries."

    # Box alignment
    elements.append(section_label(MARGIN, y, "Box Alignment (box_align_x, box_align_y) - positions box relative to (x, y)"))
    y += 20

    # Reference point
    ref_x = 150
    # Vertical line
    elements.append({
        "type": "line",
        "x1": ref_x, "y1": y, "x2": ref_x, "y2": y + 80,
        "stroke": 1, "color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "text", "x": ref_x + 5, "y": y - 3,
        "text": f"x = {ref_x}", "font": "sans", "size": 8,
        "color": (255, 0, 0, 255)
    })

    box_aligns = ["left", "center", "right"]
    for i, align in enumerate(box_aligns):
        bx = ref_x
        by = y + 5 + i * 25
        bw, bh = 100, 20
        # Ghost rect showing actual box position
        if align == "left":
            rect_x = bx
        elif align == "center":
            rect_x = bx - bw / 2
        else:
            rect_x = bx - bw
        elements.append({
            "type": "rect",
            "x": rect_x, "y": by, "w": bw, "h": bh,
            "stroke": 0.5, "stroke_color": (200, 200, 200, 255)
        })
        elements.append({
            "type": "textbox",
            "x": bx, "y": by, "w": bw, "h": bh,
            "box_align_x": align,
            "text_align_y": "center",
            "text": f'box_align_x="{align}"',
            "font": "sans", "size": 9
        })

    # Text alignment inside box
    y += 140  # Extra spacing between sections
    elements.append(section_label(MARGIN, y, "Text Alignment (text_align_x, text_align_y) - positions text inside box"))
    y += 20

    # Horizontal text alignment
    aligns_x = ["left", "center", "right"]
    bw, bh = 140, 60
    for i, align in enumerate(aligns_x):
        bx = MARGIN + i * (bw + 20)
        elements.append({
            "type": "rect",
            "x": bx, "y": y, "w": bw, "h": bh,
            "stroke": 1, "stroke_color": (180, 180, 180, 255)
        })
        elements.append({
            "type": "textbox",
            "x": bx, "y": y, "w": bw, "h": bh,
            "text_align_x": align,
            "text_align_y": "center",
            "text": f'text_align_x=\n"{align}"',
            "font": "sans", "size": 11,
            "line_height": 14
        })

    y += bh + 40  # Extra spacing between sections

    # Vertical text alignment
    aligns_y = ["top", "capline", "center", "baseline", "bottom"]
    bw, bh = 95, 70
    for i, align in enumerate(aligns_y):
        bx = MARGIN + i * (bw + 5)
        elements.append({
            "type": "rect",
            "x": bx, "y": y, "w": bw, "h": bh,
            "stroke": 1, "stroke_color": (180, 180, 180, 255)
        })
        elements.append({
            "type": "textbox",
            "x": bx, "y": y, "w": bw, "h": bh,
            "text_align_x": "center",
            "text_align_y": align,
            "text": f'"{align}"',
            "font": "sans", "size": 10
        })

    y += bh + 50  # Extra spacing between sections

    # Word wrapping demonstration
    elements.append(section_label(MARGIN, y, "Word Wrapping"))
    y += 15

    long_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation."
    bw, bh = 200, 100
    elements.append({
        "type": "rect",
        "x": MARGIN, "y": y, "w": bw, "h": bh,
        "stroke": 1, "stroke_color": (180, 180, 180, 255)
    })
    elements.append({
        "type": "textbox",
        "x": MARGIN, "y": y, "w": bw, "h": bh,
        "text_align_y": "top",
        "text": long_text,
        "font": "sans", "size": 10,
        "line_height": 13
    })

    # Line height comparison
    elements.append(section_label(MARGIN + bw + 40, y - 15, "Line Height"))
    line_heights = [12, 16, 20]
    for i, lh in enumerate(line_heights):
        bx = MARGIN + bw + 40 + i * 100
        elements.append({
            "type": "rect",
            "x": bx, "y": y, "w": 90, "h": 100,
            "stroke": 0.5, "stroke_color": (200, 200, 200, 255)
        })
        elements.append({
            "type": "textbox",
            "x": bx, "y": y, "w": 90, "h": 100,
            "text_align_y": "top",
            "text": f"line_height={lh}\nLine 2\nLine 3\nLine 4",
            "font": "sans", "size": 10,
            "line_height": lh
        })

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 4: Rectangle Element
# =============================================================================
def make_rect_page() -> dict:
    elements = page_header("Rectangle Element", "Rectangles with stroke, fill, and rounded corners")
    y = 130

    # Basic rectangles
    elements.append(section_label(MARGIN, y, "Stroke and Fill"))
    y += 20

    rects = [
        {"stroke": 1, "stroke_color": (0, 0, 0, 255), "label": "Stroke only"},
        {"fill_color": (200, 220, 255, 255), "stroke": 0, "label": "Fill only"},
        {"stroke": 2, "stroke_color": (0, 0, 0, 255), "fill_color": (255, 240, 200, 255), "label": "Stroke + Fill"},
    ]
    for i, r in enumerate(rects):
        rx = MARGIN + i * 170
        elements.append({
            "type": "rect",
            "x": rx, "y": y, "w": 150, "h": 60,
            **{k: v for k, v in r.items() if k != "label"}
        })
        elements.append({
            "type": "text",
            "x": rx + 75, "y": y + 75,
            "text": r["label"],
            "font": "sans", "size": 9,
            "align": "center"
        })

    y += 130  # Extra spacing

    # Stroke widths
    elements.append(section_label(MARGIN, y, "Stroke Widths"))
    y += 20

    widths = [0.5, 1, 2, 4, 8]
    for i, w in enumerate(widths):
        rx = MARGIN + i * 100
        elements.append({
            "type": "rect",
            "x": rx, "y": y, "w": 80, "h": 40,
            "stroke": w, "stroke_color": (0, 0, 0, 255)
        })
        elements.append({
            "type": "text",
            "x": rx + 40, "y": y + 50,
            "text": f"stroke={w}",
            "font": "sans", "size": 8,
            "align": "center"
        })

    y += 100  # Extra spacing

    # Corner radius
    elements.append(section_label(MARGIN, y, "Corner Radius"))
    y += 20

    radii = [0, 5, 10, 20, 30]
    for i, r in enumerate(radii):
        rx = MARGIN + i * 100
        elements.append({
            "type": "rect",
            "x": rx, "y": y, "w": 80, "h": 50,
            "stroke": 1, "stroke_color": (0, 0, 0, 255),
            "fill_color": (220, 240, 255, 255),
            "corner_radius": r
        })
        elements.append({
            "type": "text",
            "x": rx + 40, "y": y + 60,
            "text": f"r={r}",
            "font": "sans", "size": 8,
            "align": "center"
        })

    y += 110  # Extra spacing

    # Alpha/transparency
    elements.append(section_label(MARGIN, y, "Alpha Transparency"))
    y += 20

    alphas = [255, 200, 150, 100, 50]
    # Background pattern
    for i in range(10):
        elements.append({
            "type": "rect",
            "x": MARGIN + i * 50, "y": y,
            "w": 25, "h": 50,
            "fill_color": (200, 200, 200, 255), "stroke": 0
        })
    # Overlay with varying alpha
    for i, a in enumerate(alphas):
        rx = MARGIN + i * 100
        elements.append({
            "type": "rect",
            "x": rx, "y": y, "w": 80, "h": 50,
            "fill_color": (0, 100, 200, a),
            "stroke": 0
        })
        elements.append({
            "type": "text",
            "x": rx + 40, "y": y + 60,
            "text": f"alpha={a}",
            "font": "sans", "size": 8,
            "align": "center"
        })

    y += 110  # Extra spacing

    # Colors
    elements.append(section_label(MARGIN, y, "Colors"))
    y += 20

    colors = [
        (255, 99, 71, 255),    # Tomato
        (255, 165, 0, 255),   # Orange
        (255, 215, 0, 255),   # Gold
        (50, 205, 50, 255),   # Lime Green
        (0, 191, 255, 255),   # Deep Sky Blue
        (138, 43, 226, 255),  # Blue Violet
    ]
    for i, c in enumerate(colors):
        rx = MARGIN + i * 85
        elements.append({
            "type": "rect",
            "x": rx, "y": y, "w": 70, "h": 40,
            "fill_color": c, "stroke": 0,
            "corner_radius": 5
        })

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 5: Line Element
# =============================================================================
def make_line_page() -> dict:
    elements = page_header("Line Element", "Lines with configurable stroke")
    y = 130

    # Basic lines
    elements.append(section_label(MARGIN, y, "Stroke Widths"))
    y += 20

    widths = [0.25, 0.5, 1, 2, 4, 8]
    for i, w in enumerate(widths):
        ly = y + i * 25
        elements.append({
            "type": "line",
            "x1": MARGIN, "y1": ly, "x2": MARGIN + 200, "y2": ly,
            "stroke": w, "color": (0, 0, 0, 255)
        })
        elements.append({
            "type": "text",
            "x": MARGIN + 220, "y": ly - 4,
            "text": f"stroke={w}",
            "font": "sans", "size": 9
        })

    y += 190  # Extra spacing

    # Colors
    elements.append(section_label(MARGIN, y, "Colors"))
    y += 20

    colors = [
        ((0, 0, 0, 255), "Black"),
        ((255, 0, 0, 255), "Red"),
        ((0, 128, 0, 255), "Green"),
        ((0, 0, 255, 255), "Blue"),
        ((128, 128, 128, 255), "Gray"),
    ]
    for i, (c, name) in enumerate(colors):
        ly = y + i * 20
        elements.append({
            "type": "line",
            "x1": MARGIN, "y1": ly, "x2": MARGIN + 150, "y2": ly,
            "stroke": 2, "color": c
        })
        elements.append({
            "type": "text",
            "x": MARGIN + 170, "y": ly - 4,
            "text": name,
            "font": "sans", "size": 9
        })

    y += 140  # Extra spacing

    # Diagonal lines
    elements.append(section_label(MARGIN, y, "Diagonal Lines"))
    y += 20

    # Grid of diagonal lines
    for i in range(5):
        x1 = MARGIN + i * 80
        elements.append({
            "type": "line",
            "x1": x1, "y1": y, "x2": x1 + 60, "y2": y + 60,
            "stroke": 1, "color": (0, 0, 0, 255)
        })
        elements.append({
            "type": "line",
            "x1": x1 + 60, "y1": y, "x2": x1, "y2": y + 60,
            "stroke": 1, "color": (150, 150, 150, 255)
        })

    y += 120  # Extra spacing

    # Alpha
    elements.append(section_label(MARGIN, y, "Alpha Transparency"))
    y += 20

    alphas = [255, 200, 150, 100, 50]
    for i, a in enumerate(alphas):
        ly = y + i * 15
        elements.append({
            "type": "line",
            "x1": MARGIN, "y1": ly, "x2": MARGIN + 200, "y2": ly,
            "stroke": 4, "color": (0, 0, 200, a)
        })
        elements.append({
            "type": "text",
            "x": MARGIN + 220, "y": ly - 4,
            "text": f"alpha={a}",
            "font": "sans", "size": 9
        })

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 6: Image Element
# =============================================================================
def make_image_page() -> dict:
    elements = page_header("Image Element", "PNG, JPEG, WebP, and SVG images")
    y = 130

    # Check if images exist
    svg_exists = SVG_PATH and os.path.exists(SVG_PATH)
    png_exists = PNG_PATH and os.path.exists(PNG_PATH)

    if not svg_exists and not png_exists:
        elements.append({
            "type": "text",
            "x": PAGE_W / 2, "y": 300,
            "text": "No images available in assets/ directory",
            "font": "sans", "size": 14,
            "align": "center",
            "color": (255, 0, 0, 255)
        })
        return {"size": (PAGE_W, PAGE_H), "elements": elements}

    # SVG images (vector) - these maintain aspect ratio
    if svg_exists:
        elements.append(section_label(MARGIN, y, "SVG Image (vector) - maintains aspect ratio"))
        y += 20

        # SVG logo is wide (1472x256), so heights will be small
        widths = [100, 200, 300]
        for i, w in enumerate(widths):
            # Calculate expected height based on aspect ratio 1472:256 = 5.75:1
            expected_h = w / 5.75
            elements.append({
                "type": "image",
                "x": MARGIN, "y": y,
                "w": w,
                "image_ref": "logo_svg"
            })
            elements.append({
                "type": "text",
                "x": MARGIN + w + 10, "y": y + expected_h / 2,
                "text": f"w={w}",
                "font": "mono", "size": 9,
                "vertical_anchor": "center"
            })
            y += expected_h + 20

        y += 20

    # PNG images (raster)
    if png_exists:
        elements.append(section_label(MARGIN, y, "PNG Image (raster) - square image"))
        y += 20

        # Different sizes - PNG is 3200x3200 (square)
        sizes = [60, 90, 120]
        x = MARGIN
        for size in sizes:
            elements.append({
                "type": "rect",
                "x": x - 2, "y": y - 2,
                "w": size + 4, "h": size + 4,
                "stroke": 0.5, "stroke_color": (200, 200, 200, 255)
            })
            elements.append({
                "type": "image",
                "x": x, "y": y,
                "w": size, "h": size,
                "image_ref": "photo_png"
            })
            elements.append({
                "type": "text",
                "x": x + size / 2, "y": y + size + 15,
                "text": f"{size}x{size}",
                "font": "mono", "size": 8,
                "align": "center"
            })
            x += size + 50

        y += 120 + 30

        # Explicit dimensions
        elements.append(section_label(MARGIN, y, "Explicit width and height"))
        y += 20

        dims = [(100, 60), (80, 100), (120, 80)]
        x = MARGIN
        for w, h in dims:
            elements.append({
                "type": "rect",
                "x": x - 2, "y": y - 2,
                "w": w + 4, "h": h + 4,
                "stroke": 0.5, "stroke_color": (200, 200, 200, 255)
            })
            elements.append({
                "type": "image",
                "x": x, "y": y,
                "w": w, "h": h,
                "image_ref": "photo_png"
            })
            elements.append({
                "type": "text",
                "x": x + w / 2, "y": y + h + 15,
                "text": f"{w}x{h}",
                "font": "mono", "size": 8,
                "align": "center"
            })
            x += w + 50

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 7: Barcode Element
# =============================================================================
def make_barcode_page() -> dict:
    elements = page_header("Barcode Element", "Code 128 barcodes")
    y = 130

    # Basic barcode
    elements.append(section_label(MARGIN, y, "Basic Barcode"))
    y += 20

    elements.append({
        "type": "barcode",
        "x": MARGIN, "y": y,
        "w": 200, "h": 50,
        "value": "ABC-12345"
    })
    elements.append({
        "type": "text",
        "x": MARGIN + 220, "y": y + 25,
        "text": 'value="ABC-12345"',
        "font": "mono", "size": 9,
        "vertical_anchor": "center"
    })

    y += 70

    # With human readable text
    elements.append(section_label(MARGIN, y, "Human Readable Text"))
    y += 20

    elements.append({
        "type": "barcode",
        "x": MARGIN, "y": y,
        "w": 200, "h": 50,
        "value": "SKU-98765",
        "human_readable": True,
        "font": "mono",
        "font_size": 10
    })
    elements.append({
        "type": "text",
        "x": MARGIN + 220, "y": y + 25,
        "text": "human_readable=True",
        "font": "mono", "size": 9,
        "vertical_anchor": "center"
    })

    y += 80

    # Different sizes (stacked vertically to fit on page)
    elements.append(section_label(MARGIN, y, "Different Sizes"))
    y += 20

    sizes = [(160, 40), (200, 50), (240, 60)]
    for w, h in sizes:
        elements.append({
            "type": "barcode",
            "x": MARGIN, "y": y,
            "w": w, "h": h,
            "value": "12345",
            "human_readable": True,
            "font": "mono",
            "font_size": 9
        })
        elements.append({
            "type": "text",
            "x": MARGIN + w + 20, "y": y + h / 2,
            "text": f"w={w}, h={h}",
            "font": "mono", "size": 9,
            "vertical_anchor": "center"
        })
        y += h + 25

    y += 10

    # Different values
    elements.append(section_label(MARGIN, y, "Different Values"))
    y += 20

    values = ["HELLO-WORLD", "1234567890", "ABC123XYZ"]
    for v in values:
        elements.append({
            "type": "barcode",
            "x": MARGIN, "y": y,
            "w": 220, "h": 45,
            "value": v,
            "human_readable": True,
            "font": "mono",
            "font_size": 9
        })
        y += 60

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 8: QR Code Element
# =============================================================================
def make_qrcode_page() -> dict:
    elements = page_header("QR Code Element", "QR codes with customizable colors")
    y = 130

    # Basic QR code
    elements.append(section_label(MARGIN, y, "Basic QR Code"))
    y += 20

    elements.append({
        "type": "qrcode",
        "x": MARGIN, "y": y,
        "size": 100,
        "value": "https://github.com/stringking/rupdf"
    })
    elements.append({
        "type": "text",
        "x": MARGIN + 120, "y": y + 40,
        "text": 'value="https://github.com/stringking/rupdf"',
        "font": "sans", "size": 9
    })

    y += 130

    # Different sizes
    elements.append(section_label(MARGIN, y, "Different Sizes"))
    y += 20

    sizes = [50, 80, 120]
    x = MARGIN
    for s in sizes:
        elements.append({
            "type": "qrcode",
            "x": x, "y": y,
            "size": s,
            "value": "Hello"
        })
        elements.append({
            "type": "text",
            "x": x + s / 2, "y": y + s + 15,
            "text": f"size={s}",
            "font": "sans", "size": 8,
            "align": "center"
        })
        x += s + 40

    y += 160

    # Colors
    elements.append(section_label(MARGIN, y, "Custom Colors"))
    y += 20

    color_combos = [
        ((0, 0, 0, 255), (255, 255, 255, 255), "Default"),
        ((0, 0, 128, 255), (240, 248, 255, 255), "Navy/AliceBlue"),
        ((139, 0, 0, 255), (255, 250, 240, 255), "DarkRed/FloralWhite"),
        ((0, 100, 0, 255), (240, 255, 240, 255), "DarkGreen/Honeydew"),
    ]
    x = MARGIN
    for fg, bg, name in color_combos:
        elements.append({
            "type": "qrcode",
            "x": x, "y": y,
            "size": 80,
            "value": "Color",
            "color": fg,
            "background": bg
        })
        elements.append({
            "type": "text",
            "x": x + 40, "y": y + 95,
            "text": name,
            "font": "sans", "size": 8,
            "align": "center"
        })
        x += 120

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# PAGE 9: Coordinate System
# =============================================================================
def make_coordinate_page() -> dict:
    elements = page_header("Coordinate System", "Origin at top-left, y increases downward")
    y = 130

    # Explanation
    elements.append({
        "type": "textbox",
        "x": MARGIN, "y": y,
        "w": CONTENT_W, "h": 60,
        "text_align_y": "top",
        "text": "rupdf uses a coordinate system with the origin at the top-left corner of the page. The x-axis increases to the right, and the y-axis increases downward. Units are in points (1 point = 1/72 inch).",
        "font": "sans", "size": 11,
        "line_height": 15,
        "color": (60, 60, 60, 255)
    })

    y += 80

    # Visual grid
    elements.append(section_label(MARGIN, y, "Grid (every 50 points)"))
    y += 15

    grid_x, grid_y = MARGIN, y
    grid_w, grid_h = 400, 300

    # Grid background
    elements.append({
        "type": "rect",
        "x": grid_x, "y": grid_y, "w": grid_w, "h": grid_h,
        "fill_color": (250, 250, 250, 255), "stroke": 1, "stroke_color": (0, 0, 0, 255)
    })

    # Grid lines
    for i in range(1, 8):
        gx = grid_x + i * 50
        if gx < grid_x + grid_w:
            elements.append({
                "type": "line",
                "x1": gx, "y1": grid_y, "x2": gx, "y2": grid_y + grid_h,
                "stroke": 0.25, "color": (180, 180, 180, 255)
            })
            elements.append({
                "type": "text",
                "x": gx, "y": grid_y + grid_h + 12,
                "text": str(i * 50),
                "font": "sans", "size": 7,
                "align": "center", "color": (100, 100, 100, 255)
            })

    for i in range(1, 6):
        gy = grid_y + i * 50
        if gy < grid_y + grid_h:
            elements.append({
                "type": "line",
                "x1": grid_x, "y1": gy, "x2": grid_x + grid_w, "y2": gy,
                "stroke": 0.25, "color": (180, 180, 180, 255)
            })
            elements.append({
                "type": "text",
                "x": grid_x - 5, "y": gy - 3,
                "text": str(i * 50),
                "font": "sans", "size": 7,
                "align": "right", "color": (100, 100, 100, 255)
            })

    # Origin marker
    elements.append({
        "type": "rect",
        "x": grid_x - 3, "y": grid_y - 3, "w": 6, "h": 6,
        "fill_color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "text",
        "x": grid_x + 10, "y": grid_y + 5,
        "text": "(0, 0)",
        "font": "sans", "size": 9,
        "color": (255, 0, 0, 255)
    })

    # Sample points
    points = [(100, 100), (200, 150), (300, 200), (150, 250)]
    for px, py in points:
        ax, ay = grid_x + px, grid_y + py
        elements.append({
            "type": "rect",
            "x": ax - 3, "y": ay - 3, "w": 6, "h": 6,
            "fill_color": (0, 100, 200, 255)
        })
        elements.append({
            "type": "text",
            "x": ax + 8, "y": ay - 3,
            "text": f"({px}, {py})",
            "font": "sans", "size": 8,
            "color": (0, 100, 200, 255)
        })

    # Page sizes reference
    y = grid_y + grid_h + 50
    elements.append(section_label(MARGIN, y, "Common Page Sizes"))
    y += 15

    page_sizes = [
        ("Letter", 612, 792),
        ("A4", 595, 842),
        ("Legal", 612, 1008),
        ("A5", 420, 595),
    ]
    for i, (name, w, h) in enumerate(page_sizes):
        elements.append({
            "type": "text",
            "x": MARGIN + i * 130, "y": y,
            "text": f"{name}: {w} x {h}",
            "font": "sans", "size": 10
        })

    return {"size": (PAGE_W, PAGE_H), "elements": elements}


# =============================================================================
# MAIN
# =============================================================================
def main():
    # Verify assets exist
    for path in [FONT_SANS, FONT_SANS_BOLD, FONT_MONO, FONT_MONO_BOLD]:
        if not os.path.exists(path):
            print(f"Error: Missing font file: {path}")
            sys.exit(1)

    # Build resources
    resources = {
        "fonts": {
            "sans": {"path": FONT_SANS},
            "sans-bold": {"path": FONT_SANS_BOLD},
            "mono": {"path": FONT_MONO},
            "mono-bold": {"path": FONT_MONO_BOLD},
        },
        "images": {}
    }

    if os.path.exists(SVG_PATH):
        resources["images"]["logo_svg"] = {"path": SVG_PATH}
    if os.path.exists(PNG_PATH):
        resources["images"]["photo_png"] = {"path": PNG_PATH}

    # Build pages
    pages = [
        make_title_page(),
        make_text_page(),
        make_textbox_page(),
        make_rect_page(),
        make_line_page(),
        make_image_page(),
        make_barcode_page(),
        make_qrcode_page(),
        make_coordinate_page(),
    ]

    doc = {
        "metadata": {
            "title": "rupdf Demonstration",
            "author": "rupdf"
        },
        "pages": pages,
        "resources": resources
    }

    pdf_bytes = render_pdf(doc, compress=True)

    output_path = os.path.join(PROJECT_DIR, "demo.pdf")
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"Generated {output_path} ({len(pdf_bytes):,} bytes)")
    print(f"Pages: {len(pages)}")
    print("\nPage contents:")
    print("  1. Title Page")
    print("  2. Text Element")
    print("  3. TextBox Element")
    print("  4. Rectangle Element")
    print("  5. Line Element")
    print("  6. Image Element")
    print("  7. Barcode Element")
    print("  8. QR Code Element")
    print("  9. Coordinate System")


if __name__ == "__main__":
    main()
