#!/usr/bin/env python3
"""
Benchmark rupdf against ReportLab.

This script is NOT part of CI gating.
Results are for development reference only.

Usage:
    python benchmarks/run_benchmark.py
    python benchmarks/run_benchmark.py --iterations 100
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import rupdf

# Try to import ReportLab
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("Warning: reportlab not installed. Only rupdf benchmarks will run.")
    print("Install with: pip install reportlab\n")


# Font path (adjust as needed)
FONT_PATH = "/Users/lee/Downloads/ibm-plex-sans/fonts/complete/ttf/IBMPlexSans-Regular.ttf"


def get_font_path() -> Optional[str]:
    """Get available font path."""
    if os.path.exists(FONT_PATH):
        return FONT_PATH
    # Try system fonts on macOS
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        if os.path.exists(path):
            return path
    return None


def benchmark(func: Callable, iterations: int = 10) -> Tuple[float, float, float]:
    """Run benchmark and return (min, avg, max) times in ms."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return min(times), sum(times) / len(times), max(times)


# ============================================================================
# rupdf benchmarks
# ============================================================================

def rupdf_empty_page() -> bytes:
    """Benchmark: empty page."""
    doc = {
        "pages": [{"size": (612, 792), "elements": []}],
        "resources": {"fonts": {}},
    }
    return rupdf.render_pdf(doc)


def rupdf_text_heavy(font_path: str) -> bytes:
    """Benchmark: 50 lines of text."""
    elements = [
        {"type": "text", "x": 72, "y": 72 + i * 14,
         "text": f"Line {i}: The quick brown fox jumps over the lazy dog.",
         "font": "f", "size": 10}
        for i in range(50)
    ]
    doc = {
        "pages": [{"size": (612, 792), "elements": elements}],
        "resources": {"fonts": {"f": {"path": font_path}}},
    }
    return rupdf.render_pdf(doc)


def rupdf_graphics_heavy() -> bytes:
    """Benchmark: 100 rectangles."""
    elements = [
        {"type": "rect", "x": 50 + (i % 10) * 50, "y": 50 + (i // 10) * 50,
         "w": 40, "h": 40, "stroke": 1, "stroke_color": (0, 0, 0, 255),
         "fill_color": (100 + i % 100, 150, 200, 255)}
        for i in range(100)
    ]
    doc = {
        "pages": [{"size": (612, 792), "elements": elements}],
        "resources": {"fonts": {}},
    }
    return rupdf.render_pdf(doc)


def rupdf_mixed_content(font_path: str) -> bytes:
    """Benchmark: mixed text, graphics, barcodes."""
    elements = [
        {"type": "text", "x": 72, "y": 72, "text": "Mixed Content Document", "font": "f", "size": 18},
        {"type": "text", "x": 72, "y": 100, "text": "This document contains various element types.", "font": "f", "size": 10},
    ]
    # Add rectangles
    for i in range(20):
        elements.append({
            "type": "rect", "x": 72 + (i % 5) * 100, "y": 130 + (i // 5) * 60,
            "w": 80, "h": 40, "stroke": 1, "stroke_color": (0, 0, 0, 255)
        })
    # Add lines
    for i in range(10):
        elements.append({
            "type": "line", "x1": 72, "y1": 400 + i * 10,
            "x2": 540, "y2": 400 + i * 10, "stroke": 0.5, "color": (100, 100, 100, 255)
        })
    # Add text
    for i in range(10):
        elements.append({
            "type": "text", "x": 72, "y": 520 + i * 14,
            "text": f"Data row {i}: value_a, value_b, value_c",
            "font": "f", "size": 10
        })
    # Add barcode
    elements.append({
        "type": "barcode128", "x": 72, "y": 700, "w": 200, "h": 50,
        "value": "BENCH123", "human_readable": True, "font": "f", "font_size": 10
    })

    doc = {
        "pages": [{"size": (612, 792), "elements": elements}],
        "resources": {"fonts": {"f": {"path": font_path}}},
    }
    return rupdf.render_pdf(doc)


def rupdf_multi_page(font_path: str) -> bytes:
    """Benchmark: 10-page document."""
    pages = []
    for p in range(10):
        elements = [
            {"type": "text", "x": 72, "y": 72, "text": f"Page {p + 1} of 10", "font": "f", "size": 18},
        ]
        for i in range(30):
            elements.append({
                "type": "text", "x": 72, "y": 100 + i * 20,
                "text": f"Line {i + 1}: Content for page {p + 1}",
                "font": "f", "size": 10
            })
        pages.append({"size": (612, 792), "elements": elements})

    doc = {
        "pages": pages,
        "resources": {"fonts": {"f": {"path": font_path}}},
    }
    return rupdf.render_pdf(doc)


# ============================================================================
# ReportLab benchmarks (for comparison)
# ============================================================================

def reportlab_empty_page() -> bytes:
    """Benchmark: empty page with ReportLab."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.showPage()
    c.save()
    return buffer.getvalue()


def reportlab_text_heavy() -> bytes:
    """Benchmark: 50 lines of text with ReportLab."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    for i in range(50):
        c.drawString(72, 720 - i * 14, f"Line {i}: The quick brown fox jumps over the lazy dog.")
    c.showPage()
    c.save()
    return buffer.getvalue()


def reportlab_graphics_heavy() -> bytes:
    """Benchmark: 100 rectangles with ReportLab."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    for i in range(100):
        x = 50 + (i % 10) * 50
        y = 50 + (i // 10) * 50
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB((100 + i % 100) / 255, 150 / 255, 200 / 255)
        c.rect(x, y, 40, 40, stroke=1, fill=1)
    c.showPage()
    c.save()
    return buffer.getvalue()


def reportlab_multi_page() -> bytes:
    """Benchmark: 10-page document with ReportLab."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    for p in range(10):
        c.setFont("Helvetica", 18)
        c.drawString(72, 720, f"Page {p + 1} of 10")
        c.setFont("Helvetica", 10)
        for i in range(30):
            c.drawString(72, 692 - i * 20, f"Line {i + 1}: Content for page {p + 1}")
        c.showPage()
    c.save()
    return buffer.getvalue()


# ============================================================================
# Main
# ============================================================================

def run_benchmarks(iterations: int = 10):
    """Run all benchmarks."""
    font_path = get_font_path()
    if not font_path:
        print("Error: No font available for text benchmarks")
        sys.exit(1)

    print(f"Running benchmarks with {iterations} iterations each")
    print(f"Font: {font_path}")
    print("=" * 70)
    print()

    results = []

    # rupdf benchmarks
    benchmarks = [
        ("rupdf: empty page", lambda: rupdf_empty_page()),
        ("rupdf: text heavy (50 lines)", lambda: rupdf_text_heavy(font_path)),
        ("rupdf: graphics heavy (100 rects)", lambda: rupdf_graphics_heavy()),
        ("rupdf: mixed content", lambda: rupdf_mixed_content(font_path)),
        ("rupdf: multi-page (10 pages)", lambda: rupdf_multi_page(font_path)),
    ]

    for name, func in benchmarks:
        min_t, avg_t, max_t = benchmark(func, iterations)
        print(f"{name:40} min={min_t:7.2f}ms  avg={avg_t:7.2f}ms  max={max_t:7.2f}ms")
        results.append({"name": name, "min": min_t, "avg": avg_t, "max": max_t})

    print()

    # ReportLab benchmarks (if available)
    if HAS_REPORTLAB:
        rl_benchmarks = [
            ("reportlab: empty page", reportlab_empty_page),
            ("reportlab: text heavy (50 lines)", reportlab_text_heavy),
            ("reportlab: graphics heavy (100 rects)", reportlab_graphics_heavy),
            ("reportlab: multi-page (10 pages)", reportlab_multi_page),
        ]

        for name, func in rl_benchmarks:
            min_t, avg_t, max_t = benchmark(func, iterations)
            print(f"{name:40} min={min_t:7.2f}ms  avg={avg_t:7.2f}ms  max={max_t:7.2f}ms")
            results.append({"name": name, "min": min_t, "avg": avg_t, "max": max_t})

    print()
    print("=" * 70)
    print("Benchmark complete. Results are for reference only.")

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark rupdf vs ReportLab")
    parser.add_argument("--iterations", "-n", type=int, default=10,
                        help="Number of iterations per benchmark")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output JSON file for results")
    args = parser.parse_args()

    results = run_benchmarks(args.iterations)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
