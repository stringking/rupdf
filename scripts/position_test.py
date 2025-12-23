#!/usr/bin/env python3
"""Generate a test PDF with elements at specific positions for verification."""

import sys
import os

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rupdf import render_pdf

# Page size: Letter (612 x 792 points)
PAGE_W = 612
PAGE_H = 792

# Font path - using a system font
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

def main():
    elements = []

    # Draw page border for reference
    elements.append({
        "type": "rect",
        "x": 0, "y": 0, "w": PAGE_W, "h": PAGE_H,
        "stroke": 0.5, "stroke_color": (200, 200, 200, 255)
    })

    # === GRID LINES ===
    # Vertical lines every 100 points
    for x in range(0, PAGE_W + 1, 100):
        elements.append({
            "type": "line",
            "x1": x, "y1": 0, "x2": x, "y2": PAGE_H,
            "stroke": 0.25, "color": (220, 220, 220, 255)
        })
        # Label at top
        elements.append({
            "type": "text",
            "x": x + 2, "y": 5,
            "text": str(x),
            "font": "helvetica", "size": 8,
            "color": (150, 150, 150, 255)
        })

    # Horizontal lines every 100 points
    for y in range(0, PAGE_H + 1, 100):
        elements.append({
            "type": "line",
            "x1": 0, "y1": y, "x2": PAGE_W, "y2": y,
            "stroke": 0.25, "color": (220, 220, 220, 255)
        })
        # Label at left
        elements.append({
            "type": "text",
            "x": 5, "y": y + 2,
            "text": str(y),
            "font": "helvetica", "size": 8,
            "color": (150, 150, 150, 255)
        })

    # === TEST POINTS ===
    # Red dots at specific coordinates with labels
    test_points = [
        (100, 100),
        (200, 200),
        (300, 300),
        (400, 400),
        (500, 500),
        (306, 396),  # Center of page
    ]

    for x, y in test_points:
        # Small red dot (4x4 rect centered on point)
        elements.append({
            "type": "rect",
            "x": x - 2, "y": y - 2, "w": 4, "h": 4,
            "fill_color": (255, 0, 0, 255)
        })
        # Label
        elements.append({
            "type": "text",
            "x": x + 5, "y": y - 3,
            "text": f"({x}, {y})",
            "font": "helvetica", "size": 10,
            "color": (255, 0, 0, 255)
        })

    # === TEXT ALIGNMENT TEST ===
    # All text at x=306 (center of page)
    text_y = 150
    elements.append({
        "type": "text",
        "x": 306, "y": text_y,
        "text": "align=left (default) x=306",
        "font": "helvetica", "size": 12,
        "align": "left"
    })
    # Vertical line at x=306
    elements.append({
        "type": "line",
        "x1": 306, "y1": text_y - 5, "x2": 306, "y2": text_y + 20,
        "stroke": 1, "color": (0, 0, 255, 255)
    })

    text_y = 180
    elements.append({
        "type": "text",
        "x": 306, "y": text_y,
        "text": "align=center x=306",
        "font": "helvetica", "size": 12,
        "align": "center"
    })
    elements.append({
        "type": "line",
        "x1": 306, "y1": text_y - 5, "x2": 306, "y2": text_y + 20,
        "stroke": 1, "color": (0, 0, 255, 255)
    })

    text_y = 210
    elements.append({
        "type": "text",
        "x": 306, "y": text_y,
        "text": "align=right x=306",
        "font": "helvetica", "size": 12,
        "align": "right"
    })
    elements.append({
        "type": "line",
        "x1": 306, "y1": text_y - 5, "x2": 306, "y2": text_y + 20,
        "stroke": 1, "color": (0, 0, 255, 255)
    })

    # === VERTICAL ANCHOR TEST ===
    # Test all three vertical anchor modes at y=260
    anchor_y = 260
    font_size = 18

    # Horizontal reference line at y=260
    elements.append({
        "type": "line",
        "x1": 40, "y1": anchor_y, "x2": 280, "y2": anchor_y,
        "stroke": 2, "color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "text",
        "x": 45, "y": anchor_y - 15,
        "text": "y = 260 (red line)",
        "font": "helvetica", "size": 10,
        "color": (255, 0, 0, 255)
    })

    # baseline anchor (default) - baseline sits on the line
    elements.append({
        "type": "text",
        "x": 50, "y": anchor_y,
        "text": "Baseline",
        "font": "helvetica", "size": font_size,
        "vertical_anchor": "baseline"
    })

    # capline anchor - top of caps sits on the line
    elements.append({
        "type": "text",
        "x": 140, "y": anchor_y,
        "text": "Capline",
        "font": "helvetica", "size": font_size,
        "vertical_anchor": "capline"
    })

    # center anchor - vertical center sits on the line
    elements.append({
        "type": "text",
        "x": 220, "y": anchor_y,
        "text": "Center",
        "font": "helvetica", "size": font_size,
        "vertical_anchor": "center"
    })

    # === COMBINED ALIGNMENT TEST ===
    # Test horizontal + vertical alignment at (450, 320)
    combo_x, combo_y = 450, 320

    # Crosshair at anchor point
    elements.append({
        "type": "line",
        "x1": combo_x - 30, "y1": combo_y, "x2": combo_x + 30, "y2": combo_y,
        "stroke": 1, "color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "line",
        "x1": combo_x, "y1": combo_y - 30, "x2": combo_x, "y2": combo_y + 30,
        "stroke": 1, "color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "text",
        "x": combo_x + 5, "y": combo_y - 35,
        "text": f"({combo_x}, {combo_y})",
        "font": "helvetica", "size": 9,
        "color": (255, 0, 0, 255)
    })

    # Center-aligned text at the crosshair
    elements.append({
        "type": "text",
        "x": combo_x, "y": combo_y,
        "text": "CENTER",
        "font": "helvetica", "size": 16,
        "align": "center",
        "vertical_anchor": "center",
        "color": (0, 100, 200, 255)
    })

    # === RECTANGLE POSITIONING TEST ===
    # Rectangle at (100, 450) with size 100x50
    elements.append({
        "type": "rect",
        "x": 100, "y": 450, "w": 100, "h": 50,
        "fill_color": (0, 150, 255, 100),
        "stroke": 1, "stroke_color": (0, 100, 200, 255)
    })
    elements.append({
        "type": "text",
        "x": 100, "y": 440,
        "text": "rect @ (100, 450) 100x50",
        "font": "helvetica", "size": 10
    })
    # Mark top-left corner
    elements.append({
        "type": "rect",
        "x": 98, "y": 448, "w": 4, "h": 4,
        "fill_color": (255, 0, 0, 255)
    })

    # === ROUNDED RECTANGLE TEST ===
    # Rounded rect at (100, 520) with size 100x50, corner_radius=10
    elements.append({
        "type": "rect",
        "x": 100, "y": 520, "w": 100, "h": 50,
        "fill_color": (255, 200, 100, 200),
        "stroke": 2, "stroke_color": (200, 100, 0, 255),
        "corner_radius": 10
    })
    elements.append({
        "type": "text",
        "x": 100, "y": 510,
        "text": "rounded rect r=10",
        "font": "helvetica", "size": 10
    })

    # Pill-shaped rect (radius = half height)
    elements.append({
        "type": "rect",
        "x": 220, "y": 520, "w": 80, "h": 30,
        "fill_color": (100, 200, 100, 200),
        "stroke": 1, "stroke_color": (0, 150, 0, 255),
        "corner_radius": 15
    })
    elements.append({
        "type": "text",
        "x": 220, "y": 510,
        "text": "pill r=15 (h=30)",
        "font": "helvetica", "size": 10
    })

    # === LINE POSITIONING TEST ===
    # Line from (300, 450) to (400, 520)
    elements.append({
        "type": "line",
        "x1": 300, "y1": 450, "x2": 400, "y2": 520,
        "stroke": 2, "color": (0, 128, 0, 255)
    })
    elements.append({
        "type": "text",
        "x": 300, "y": 440,
        "text": "line (300,450) to (400,520)",
        "font": "helvetica", "size": 10
    })
    # Mark endpoints
    elements.append({
        "type": "rect",
        "x": 298, "y": 448, "w": 4, "h": 4,
        "fill_color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "rect",
        "x": 398, "y": 518, "w": 4, "h": 4,
        "fill_color": (255, 0, 0, 255)
    })

    # === CORNER TESTS ===
    # Small rects at each corner
    corner_size = 20
    corners = [
        (0, 0, "top-left (0,0)"),
        (PAGE_W - corner_size, 0, f"top-right ({PAGE_W - corner_size},0)"),
        (0, PAGE_H - corner_size, f"bottom-left (0,{PAGE_H - corner_size})"),
        (PAGE_W - corner_size, PAGE_H - corner_size, f"bottom-right"),
    ]

    for x, y, label in corners:
        elements.append({
            "type": "rect",
            "x": x, "y": y, "w": corner_size, "h": corner_size,
            "fill_color": (255, 200, 0, 200)
        })

    # Labels for corners (positioned to be visible)
    elements.append({
        "type": "text", "x": 25, "y": 25,
        "text": "top-left (0,0)", "font": "helvetica", "size": 9
    })
    elements.append({
        "type": "text", "x": PAGE_W - 25, "y": 25,
        "text": f"top-right ({PAGE_W},0)", "font": "helvetica", "size": 9, "align": "right"
    })
    elements.append({
        "type": "text", "x": 25, "y": PAGE_H - 30,
        "text": f"bottom-left (0,{PAGE_H})", "font": "helvetica", "size": 9
    })
    elements.append({
        "type": "text", "x": PAGE_W - 25, "y": PAGE_H - 30,
        "text": f"bottom-right ({PAGE_W},{PAGE_H})", "font": "helvetica", "size": 9, "align": "right"
    })

    # === TITLE ===
    elements.append({
        "type": "text",
        "x": 306, "y": 60,
        "text": "rupdf Position Test",
        "font": "helvetica", "size": 24,
        "align": "center"
    })
    elements.append({
        "type": "text",
        "x": 306, "y": 85,
        "text": f"Page size: {PAGE_W} x {PAGE_H} points (Letter)",
        "font": "helvetica", "size": 12,
        "align": "center",
        "color": (100, 100, 100, 255)
    })
    elements.append({
        "type": "text",
        "x": 306, "y": 105,
        "text": "Origin (0,0) is top-left, y increases downward",
        "font": "helvetica", "size": 10,
        "align": "center",
        "color": (100, 100, 100, 255)
    })

    # === QR CODE POSITIONING TEST ===
    elements.append({
        "type": "qrcode",
        "x": 450, "y": 600,
        "size": 80,
        "value": "https://github.com/stringking/rupdf"
    })
    elements.append({
        "type": "text",
        "x": 450, "y": 590,
        "text": "QR @ (450, 600) size=80",
        "font": "helvetica", "size": 9
    })
    elements.append({
        "type": "rect",
        "x": 448, "y": 598, "w": 4, "h": 4,
        "fill_color": (255, 0, 0, 255)
    })

    # === BARCODE POSITIONING TEST ===
    elements.append({
        "type": "barcode",
        "x": 100, "y": 600,
        "w": 150, "h": 50,
        "value": "12345",
        "font": "helvetica",
        "font_size": 10,
        "human_readable": True
    })
    elements.append({
        "type": "text",
        "x": 100, "y": 590,
        "text": "barcode @ (100, 600) 150x50",
        "font": "helvetica", "size": 9
    })
    elements.append({
        "type": "rect",
        "x": 98, "y": 598, "w": 4, "h": 4,
        "fill_color": (255, 0, 0, 255)
    })

    # === TEXTBOX TESTS ===
    # Basic TextBox with wrapping
    elements.append({
        "type": "rect",
        "x": 300, "y": 580, "w": 180, "h": 80,
        "stroke": 1, "stroke_color": (150, 150, 150, 255)
    })
    elements.append({
        "type": "textbox",
        "x": 300, "y": 580,
        "w": 180, "h": 80,
        "text": "This is a TextBox with word wrapping. The text should wrap at word boundaries.",
        "font": "helvetica",
        "size": 11,
        "color": (0, 0, 0, 255)
    })
    elements.append({
        "type": "text",
        "x": 300, "y": 570,
        "text": "textbox @ (300, 580) 180x80",
        "font": "helvetica", "size": 9
    })

    # TextBox with center alignment
    elements.append({
        "type": "rect",
        "x": 300, "y": 690, "w": 180, "h": 60,
        "stroke": 1, "stroke_color": (150, 150, 150, 255)
    })
    elements.append({
        "type": "textbox",
        "x": 300, "y": 690,
        "w": 180, "h": 60,
        "text": "Centered text in box",
        "font": "helvetica",
        "size": 12,
        "text_align_x": "center",
        "text_align_y": "center",
        "color": (0, 100, 200, 255)
    })
    elements.append({
        "type": "text",
        "x": 300, "y": 680,
        "text": "textbox center/center",
        "font": "helvetica", "size": 9
    })

    # TextBox with box_align_x=center (box centered on x)
    elements.append({
        "type": "line",
        "x1": 510, "y1": 580, "x2": 510, "y2": 680,
        "stroke": 1, "color": (255, 0, 0, 255)
    })
    elements.append({
        "type": "rect",
        "x": 510 - 80, "y": 600, "w": 160, "h": 60,
        "stroke": 1, "stroke_color": (200, 200, 200, 255)
    })
    elements.append({
        "type": "textbox",
        "x": 510, "y": 600,
        "w": 160, "h": 60,
        "box_align_x": "center",
        "text": "Box centered on x=510",
        "font": "helvetica",
        "size": 11,
        "text_align_x": "center",
        "text_align_y": "capline"
    })
    elements.append({
        "type": "text",
        "x": 510, "y": 590,
        "text": "box_align_x=center, x=510",
        "font": "helvetica", "size": 8, "align": "center"
    })

    doc = {
        "pages": [{
            "size": (PAGE_W, PAGE_H),
            "elements": elements
        }],
        "resources": {
            "fonts": {
                "helvetica": {"path": FONT_PATH}
            }
        }
    }

    pdf_bytes = render_pdf(doc)

    output_path = "position_test.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"Generated {output_path} ({len(pdf_bytes)} bytes)")
    print(f"Page size: {PAGE_W} x {PAGE_H} points")
    print("\nVerification points:")
    print("- Grid lines at every 100 points")
    print("- Red dots at specific coordinates")
    print("- Text alignment test at x=306 (page center)")
    print("- Rectangle and line position tests")
    print("- Corner markers")

if __name__ == "__main__":
    main()
