"""Shared pytest fixtures for rupdf tests."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Font paths - use assets directory
FONT_PATHS = {
    "sans": ASSETS_DIR / "IBMPlexSans-Regular.otf",
    "sans-bold": ASSETS_DIR / "IBMPlexSans-Bold.otf",
    "mono": ASSETS_DIR / "IBMPlexMono-Regular.otf",
    "mono-bold": ASSETS_DIR / "IBMPlexMono-Bold.otf",
}

# Test assets
SVG_PATH = ASSETS_DIR / "test-svg.svg"
PNG_PATH = ASSETS_DIR / "test-png.png"


def get_available_font() -> Optional[str]:
    """Return path to first available font, or None."""
    for path in FONT_PATHS.values():
        if path.exists():
            return str(path)
    return None


@pytest.fixture
def font_path() -> str:
    """Get a valid font path, skip test if none available."""
    path = get_available_font()
    if path is None:
        pytest.skip("No test fonts available")
    return path


@pytest.fixture
def font_bytes(font_path: str) -> bytes:
    """Get font data as bytes."""
    with open(font_path, "rb") as f:
        return f.read()


@pytest.fixture
def svg_path() -> str:
    """Get SVG test file path, skip if not available."""
    if not SVG_PATH.exists():
        pytest.skip("SVG test file not available")
    return str(SVG_PATH)


@pytest.fixture
def png_path() -> str:
    """Get PNG test file path, skip if not available."""
    if not PNG_PATH.exists():
        pytest.skip("PNG test file not available")
    return str(PNG_PATH)


@pytest.fixture
def svg_bytes(svg_path: str) -> bytes:
    """Get SVG data as bytes."""
    with open(svg_path, "rb") as f:
        return f.read()


@pytest.fixture
def png_bytes(png_path: str) -> bytes:
    """Get PNG data as bytes."""
    with open(png_path, "rb") as f:
        return f.read()


def convert_lists_to_tuples(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON lists to tuples where PyO3 expects tuples."""
    doc = doc.copy()
    if "pages" in doc:
        new_pages = []
        for page in doc["pages"]:
            page = page.copy()
            if "size" in page and isinstance(page["size"], list):
                page["size"] = tuple(page["size"])
            if "background" in page and isinstance(page["background"], list):
                page["background"] = tuple(page["background"])
            if "elements" in page:
                new_elements = []
                for elem in page["elements"]:
                    elem = elem.copy()
                    if "color" in elem and isinstance(elem["color"], list):
                        elem["color"] = tuple(elem["color"])
                    if "stroke_color" in elem and isinstance(elem["stroke_color"], list):
                        elem["stroke_color"] = tuple(elem["stroke_color"])
                    if "fill_color" in elem and isinstance(elem["fill_color"], list):
                        elem["fill_color"] = tuple(elem["fill_color"])
                    new_elements.append(elem)
                page["elements"] = new_elements
            new_pages.append(page)
        doc["pages"] = new_pages
    return doc


def load_fixture(name: str) -> Dict[str, Any]:
    """Load a JSON fixture file and convert lists to tuples where needed."""
    path = FIXTURES_DIR / name
    with open(path) as f:
        data = json.load(f)
    return convert_lists_to_tuples(data)


@pytest.fixture
def simple_text_fixture() -> Dict[str, Any]:
    """Load simple_text.json fixture."""
    return load_fixture("simple_text.json")


@pytest.fixture
def multi_page_fixture() -> Dict[str, Any]:
    """Load multi_page.json fixture."""
    return load_fixture("multi_page.json")


@pytest.fixture
def all_elements_fixture() -> Dict[str, Any]:
    """Load all_elements.json fixture."""
    return load_fixture("all_elements.json")


@pytest.fixture
def stress_test_fixture() -> Dict[str, Any]:
    """Load stress_test.json fixture."""
    return load_fixture("stress_test.json")


def inject_font_resources(doc: Dict[str, Any], font_path: str) -> Dict[str, Any]:
    """Inject actual font path into document that uses 'default' font."""
    doc = doc.copy()
    doc["resources"] = doc.get("resources", {}).copy()
    doc["resources"]["fonts"] = {"default": {"path": font_path}}
    return doc


@pytest.fixture
def minimal_doc(font_path: str) -> Dict[str, Any]:
    """Minimal valid document for testing."""
    return {
        "pages": [{"size": (612, 792), "elements": []}],
        "resources": {"fonts": {"default": {"path": font_path}}},
    }


@pytest.fixture
def text_doc(font_path: str) -> Dict[str, Any]:
    """Document with a single text element."""
    return {
        "pages": [{
            "size": (612, 792),
            "elements": [
                {"type": "text", "x": 72, "y": 72, "text": "Hello World", "font": "default", "size": 12}
            ]
        }],
        "resources": {"fonts": {"default": {"path": font_path}}},
    }
