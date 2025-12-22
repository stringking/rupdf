"""PyO3 interface boundary tests.

Tests the Python-Rust interface: argument parsing, error handling,
return types, and edge cases.
"""

import pytest
import rupdf


class TestRenderPdfSignature:
    """Test render_pdf function signature and argument handling."""

    def test_returns_bytes(self, minimal_doc):
        """render_pdf should return bytes."""
        result = rupdf.render_pdf(minimal_doc)
        assert isinstance(result, bytes)

    def test_accepts_compress_kwarg(self, minimal_doc):
        """render_pdf should accept compress keyword argument."""
        compressed = rupdf.render_pdf(minimal_doc, compress=True)
        uncompressed = rupdf.render_pdf(minimal_doc, compress=False)
        assert isinstance(compressed, bytes)
        assert isinstance(uncompressed, bytes)

    def test_missing_pages_raises(self):
        """Missing 'pages' key should raise error."""
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf({"resources": {}})

    def test_empty_pages_allowed(self):
        """Empty pages list should produce valid PDF (no pages)."""
        # Note: Empty document is valid - produces PDF with 0 pages
        result = rupdf.render_pdf({"pages": [], "resources": {}})
        assert result[:5] == b"%PDF-"

    def test_invalid_page_size_raises(self, font_path):
        """Invalid page dimensions should raise error."""
        doc = {
            "pages": [{"size": (0, 792), "elements": []}],
            "resources": {"fonts": {}},
        }
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)

    def test_negative_page_size_raises(self, font_path):
        """Negative page dimensions should raise error."""
        doc = {
            "pages": [{"size": (-100, 792), "elements": []}],
            "resources": {"fonts": {}},
        }
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)


class TestElementParsing:
    """Test element dict parsing at the interface boundary."""

    def test_text_requires_font(self, font_path):
        """Text element should require font reference."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "text", "x": 72, "y": 72, "text": "Test", "size": 12}]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)

    def test_unknown_element_type_raises(self, font_path):
        """Unknown element type should raise error."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "circle", "x": 100, "y": 100, "r": 50}]
            }],
            "resources": {"fonts": {}},
        }
        with pytest.raises(rupdf.RupdfError) as exc_info:
            rupdf.render_pdf(doc)
        assert "circle" in str(exc_info.value).lower()

    def test_missing_required_field_raises(self, font_path):
        """Missing required element fields should raise error."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "rect", "x": 72, "y": 72}]  # missing w, h
            }],
            "resources": {"fonts": {}},
        }
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)


class TestResourceParsing:
    """Test resource dict parsing at the interface boundary."""

    def test_font_path_loading(self, font_path):
        """Font from path should load successfully."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "text", "x": 72, "y": 72, "text": "Test", "font": "f", "size": 12}]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        result = rupdf.render_pdf(doc)
        assert len(result) > 0

    def test_font_bytes_loading(self, font_bytes):
        """Font from bytes should load successfully."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "text", "x": 72, "y": 72, "text": "Test", "font": "f", "size": 12}]
            }],
            "resources": {"fonts": {"f": {"bytes": font_bytes}}},
        }
        result = rupdf.render_pdf(doc)
        assert len(result) > 0

    def test_font_path_and_bytes_raises(self, font_path, font_bytes):
        """Font with both path and bytes should raise error."""
        doc = {
            "pages": [{"size": (612, 792), "elements": []}],
            "resources": {"fonts": {"f": {"path": font_path, "bytes": font_bytes}}},
        }
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)

    def test_missing_font_raises(self, font_path):
        """Reference to undefined font should raise error."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "text", "x": 72, "y": 72, "text": "Test", "font": "undefined", "size": 12}]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        with pytest.raises(rupdf.RupdfError) as exc_info:
            rupdf.render_pdf(doc)
        assert "undefined" in str(exc_info.value).lower() or "font" in str(exc_info.value).lower()

    def test_missing_image_raises(self):
        """Reference to undefined image should raise error."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "image", "x": 72, "y": 72, "w": 100, "h": 100, "image_ref": "undefined"}]
            }],
            "resources": {"fonts": {}, "images": {}},
        }
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)


class TestColorParsing:
    """Test color tuple parsing at the interface boundary."""

    def test_valid_rgba_color(self, font_path):
        """Valid RGBA tuple should work."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [
                    {"type": "text", "x": 72, "y": 72, "text": "Test", "font": "f", "size": 12, "color": (255, 0, 0, 255)}
                ]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        result = rupdf.render_pdf(doc)
        assert len(result) > 0

    def test_invalid_color_tuple_length(self, font_path):
        """Color with wrong tuple length should raise error."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [
                    {"type": "text", "x": 72, "y": 72, "text": "Test", "font": "f", "size": 12, "color": (255, 0, 0)}
                ]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        with pytest.raises((rupdf.RupdfError, TypeError, ValueError)):
            rupdf.render_pdf(doc)


class TestErrorType:
    """Test that RupdfError is properly exported."""

    def test_rupdf_error_exists(self):
        """RupdfError should be accessible from module."""
        assert hasattr(rupdf, "RupdfError")
        assert issubclass(rupdf.RupdfError, Exception)

    def test_error_message_content(self, font_path):
        """Error messages should be descriptive."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "text", "x": 72, "y": 72, "text": "Test", "font": "missing", "size": 12}]
            }],
            "resources": {"fonts": {}},
        }
        with pytest.raises(rupdf.RupdfError) as exc_info:
            rupdf.render_pdf(doc)
        # Error should mention the missing font
        assert "missing" in str(exc_info.value).lower() or "font" in str(exc_info.value).lower()
