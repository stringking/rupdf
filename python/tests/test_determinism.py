"""Identical input must render to byte-identical PDFs, within and across processes."""

import hashlib
import subprocess
import sys

import pytest
import rupdf

from .conftest import ASSETS_DIR, FONT_PATHS, PNG_PATH, SVG_PATH, inject_font_resources

RENDERS = 5

FONTS = {name: {"path": str(path)} for name, path in FONT_PATHS.items()}

# Classed CSS, group opacity and fill/stroke alpha exercise the SVG path end to end.
STYLED_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
<defs><style>.a{fill:#1d1b19;}.b{fill:#c8102e;opacity:.5;}.c{stroke:#003;fill:none;stroke-opacity:.25;}</style></defs>
<g opacity="0.75"><rect class="a" x="0" y="0" width="80" height="40"/></g>
<circle class="b" cx="120" cy="50" r="30"/>
<path class="c" d="M10 90 L190 10" stroke-width="4"/>
</svg>"""


def svg_doc():
    return {
        "pages": [{"size": (432.08, 432.5), "elements": [
            {"type": "image", "x": 0, "y": 0, "w": 432.08, "h": 432.5, "image_ref": "logo"},
            {"type": "image", "x": 20, "y": 300, "w": 200, "h": 100, "image_ref": "styled"},
        ]}],
        "resources": {"fonts": {}, "images": {
            "logo": {"bytes": SVG_PATH.read_bytes()},
            "styled": {"bytes": STYLED_SVG},
        }},
    }


def text_doc():
    return {
        "pages": [{"size": (612, 792), "elements": [
            {"type": "text", "x": 72, "y": 72, "text": "Hello World 0123", "font": "sans", "size": 12},
            {"type": "text", "x": 72, "y": 96, "text": "Quick brown fox", "font": "sans-bold",
             "size": 14, "color": (0, 0, 0, 159)},
            {"type": "text", "x": 72, "y": 120, "text": "{mono} [text]", "font": "mono", "size": 10},
            {"type": "textbox", "x": 72, "y": 150, "w": 200, "h": 80,
             "text": "Wrapped paragraph text across several lines", "font": "mono-bold", "size": 11},
        ]}],
        "resources": {"fonts": FONTS, "images": {}},
    }


def barcode_doc():
    return {
        "pages": [{"size": (400, 300), "elements": [
            {"type": "barcode", "x": 10, "y": 10, "w": 250, "h": 60, "value": "ABC12345678",
             "human_readable": True, "font": "mono"},
            {"type": "gs1_128", "x": 10, "y": 100, "w": 300, "h": 60,
             "value": "(01)00012345678905(10)LOT42", "human_readable": True, "font": "sans"},
            {"type": "qrcode", "x": 10, "y": 180, "size": 80, "value": "https://example.com"},
            {"type": "datamatrix", "x": 120, "y": 180, "size": 80, "value": "DM-123"},
        ]}],
        "resources": {"fonts": FONTS, "images": {}},
    }


def mixed_doc():
    return {
        "pages": [
            {"size": (612, 792), "elements": [
                {"type": "image", "x": 0, "y": 0, "w": 100, "h": 50, "image_ref": "logo"},
                {"type": "image", "x": 0, "y": 100, "w": 50, "h": 50, "image_ref": "png"},
                {"type": "image", "x": 0, "y": 200, "w": 80, "h": 80, "image_ref": "png"},
                {"type": "text", "x": 72, "y": 400, "text": "Page one", "font": "sans", "size": 12},
            ]},
            {"size": (612, 792), "elements": [
                {"type": "text", "x": 72, "y": 72, "text": "Page two", "font": "sans-bold", "size": 12},
                {"type": "rect", "x": 72, "y": 100, "w": 50, "h": 50, "fill_color": (255, 0, 0, 100)},
            ]},
        ],
        "resources": {"fonts": FONTS, "images": {
            "logo": {"path": str(SVG_PATH)},
            "png": {"path": str(PNG_PATH)},
        }},
    }


def plain_doc():
    return {"pages": [{"size": (612, 792), "elements": [
        {"type": "rect", "x": 72, "y": 72, "w": 100, "h": 50},
        {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100},
    ]}], "resources": {"fonts": {}, "images": {}}}


DOCS = {
    "svg": svg_doc,
    "text": text_doc,
    "barcode": barcode_doc,
    "mixed": mixed_doc,
    "plain": plain_doc,
}

CHILD = """
import hashlib, sys
sys.path.insert(0, {tests_parent!r})
from tests.test_determinism import DOCS
import rupdf
print(hashlib.sha256(rupdf.render_pdf(DOCS[sys.argv[1]]())).hexdigest())
"""


@pytest.fixture(autouse=True)
def require_assets():
    missing = [p for p in [SVG_PATH, PNG_PATH, *FONT_PATHS.values()] if not p.exists()]
    if missing:
        pytest.skip(f"test assets missing from {ASSETS_DIR}")


@pytest.mark.parametrize("name", DOCS)
def test_repeated_renders_identical(name):
    doc = DOCS[name]()
    first = rupdf.render_pdf(doc)
    for _ in range(RENDERS):
        assert rupdf.render_pdf(doc) == first


@pytest.mark.parametrize("name", DOCS)
def test_renders_identical_across_processes(name):
    script = CHILD.format(tests_parent=str(ASSETS_DIR.parent / "python"))
    digests = {
        subprocess.run(
            [sys.executable, "-c", script, name], check=True, capture_output=True, text=True,
        ).stdout.strip()
        for _ in range(3)
    }
    digests.add(hashlib.sha256(rupdf.render_pdf(DOCS[name]())).hexdigest())
    assert len(digests) == 1


def test_all_elements_fixture_identical(all_elements_fixture, font_path):
    doc = inject_font_resources(all_elements_fixture, font_path)
    first = rupdf.render_pdf(doc)
    for _ in range(RENDERS):
        assert rupdf.render_pdf(doc) == first
