"""PDF structure and validity tests.

Tests that generated PDFs have correct structure without
comparing exact byte sequences.
"""

import pytest
import rupdf

from .conftest import inject_font_resources


class TestPdfHeader:
    """Test PDF header structure."""

    def test_starts_with_pdf_header(self, minimal_doc):
        """PDF should start with %PDF- header."""
        pdf = rupdf.render_pdf(minimal_doc)
        assert pdf[:5] == b"%PDF-"

    def test_pdf_version(self, minimal_doc):
        """PDF version should be valid."""
        pdf = rupdf.render_pdf(minimal_doc)
        # Extract version (e.g., "1.7", "2.0")
        version_line = pdf[:20].split(b"\n")[0]
        assert b"%PDF-1." in version_line or b"%PDF-2." in version_line

    def test_ends_with_eof(self, minimal_doc):
        """PDF should end with %%EOF marker."""
        pdf = rupdf.render_pdf(minimal_doc)
        assert pdf.rstrip().endswith(b"%%EOF")


class TestPdfStructure:
    """Test PDF internal structure."""

    def test_contains_catalog(self, minimal_doc):
        """PDF should contain document catalog."""
        pdf = rupdf.render_pdf(minimal_doc)
        assert b"/Type /Catalog" in pdf or b"/Type/Catalog" in pdf

    def test_contains_pages(self, minimal_doc):
        """PDF should contain pages reference."""
        pdf = rupdf.render_pdf(minimal_doc)
        assert b"/Type /Pages" in pdf or b"/Type/Pages" in pdf

    def test_contains_page(self, minimal_doc):
        """PDF should contain at least one page."""
        pdf = rupdf.render_pdf(minimal_doc)
        assert b"/Type /Page" in pdf or b"/Type/Page" in pdf

    def test_multi_page_count(self, multi_page_fixture, font_path):
        """Multi-page document should have correct page count."""
        doc = inject_font_resources(multi_page_fixture, font_path)
        pdf = rupdf.render_pdf(doc)
        # Check for page count in Pages object
        assert b"/Count 3" in pdf


class TestFontEmbedding:
    """Test font embedding in generated PDFs."""

    def test_contains_font_resources(self, text_doc):
        """Text documents should contain font resources."""
        pdf = rupdf.render_pdf(text_doc)
        # Should have font dictionary
        assert b"/Font" in pdf

    def test_contains_embedded_font(self, text_doc):
        """Font should be embedded (not just referenced)."""
        pdf = rupdf.render_pdf(text_doc)
        # Embedded fonts have font file streams
        assert b"/FontFile2" in pdf or b"/FontFile" in pdf

    def test_font_uses_postscript_name(self, font_path):
        """Fonts should use PostScript names for compatibility."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "text", "x": 72, "y": 72, "text": "Test", "font": "f", "size": 12}]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        pdf = rupdf.render_pdf(doc)
        # PostScript name should appear in BaseFont
        assert b"/BaseFont" in pdf
        # Should NOT use the alias "f" as font name (PostScript names are longer)
        # This is a heuristic check - font has a longer PostScript name
        assert b"/BaseFont /f\n" not in pdf and b"/BaseFont/f\n" not in pdf


class TestImageEmbedding:
    """Test image embedding in generated PDFs."""

    def test_svg_creates_form_xobject(self, font_path, svg_path):
        """SVG images should create Form XObjects."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "image", "x": 72, "y": 72, "w": 200, "h": 40, "image_ref": "logo"}]
            }],
            "resources": {
                "fonts": {},
                "images": {"logo": {"path": svg_path}},
            },
        }
        pdf = rupdf.render_pdf(doc)
        assert b"/Subtype /Form" in pdf or b"/Subtype/Form" in pdf

    def test_raster_creates_image_xobject(self, font_path, png_path):
        """Raster images should create Image XObjects."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "image", "x": 72, "y": 72, "w": 200, "h": 200, "image_ref": "photo"}]
            }],
            "resources": {
                "fonts": {},
                "images": {"photo": {"path": png_path}},
            },
        }
        pdf = rupdf.render_pdf(doc)
        assert b"/Subtype /Image" in pdf or b"/Subtype/Image" in pdf

    def test_raster_uses_jpeg_encoding(self, font_path, png_path):
        """Raster images should be JPEG-encoded for efficiency."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [{"type": "image", "x": 72, "y": 72, "w": 200, "h": 200, "image_ref": "photo"}]
            }],
            "resources": {
                "fonts": {},
                "images": {"photo": {"path": png_path}},
            },
        }
        pdf = rupdf.render_pdf(doc)
        assert b"/DCTDecode" in pdf or b"DCTDecode" in pdf


class TestMetadata:
    """Test document metadata embedding."""

    def test_title_in_info(self, font_path):
        """Title should appear in document info."""
        doc = {
            "metadata": {"title": "Test Document Title"},
            "pages": [{"size": (612, 792), "elements": []}],
            "resources": {"fonts": {}},
        }
        pdf = rupdf.render_pdf(doc)
        assert b"Test Document Title" in pdf

    def test_author_in_info(self, font_path):
        """Author should appear in document info."""
        doc = {
            "metadata": {"author": "Test Author Name"},
            "pages": [{"size": (612, 792), "elements": []}],
            "resources": {"fonts": {}},
        }
        pdf = rupdf.render_pdf(doc)
        assert b"Test Author Name" in pdf


class TestCompression:
    """Test PDF compression behavior."""

    def test_compressed_uses_flatedecode(self, text_doc):
        """Compressed PDFs should use FlateDecode."""
        pdf = rupdf.render_pdf(text_doc, compress=True)
        assert b"/FlateDecode" in pdf or b"FlateDecode" in pdf

    def test_compressed_smaller_or_equal(self, font_path):
        """Compressed PDF should not be larger than uncompressed."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [
                    {"type": "text", "x": 72, "y": 72 + i*15, "text": f"Line {i}: " + "x" * 50, "font": "f", "size": 10}
                    for i in range(20)
                ]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        compressed = rupdf.render_pdf(doc, compress=True)
        uncompressed = rupdf.render_pdf(doc, compress=False)
        assert len(compressed) <= len(uncompressed)


class TestBarcodes:
    """Test barcode generation in PDFs."""

    def test_barcode_without_text(self, font_path):
        """Barcode without human_readable should work."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [
                    {"type": "barcode128", "x": 72, "y": 72, "w": 200, "h": 50, "value": "TEST123"}
                ]
            }],
            "resources": {"fonts": {}},
        }
        pdf = rupdf.render_pdf(doc)
        assert len(pdf) > 0

    def test_barcode_with_text(self, font_path):
        """Barcode with human_readable should include text."""
        doc = {
            "pages": [{
                "size": (612, 792),
                "elements": [
                    {"type": "barcode128", "x": 72, "y": 72, "w": 200, "h": 60,
                     "value": "TEST123", "human_readable": True, "font": "f", "font_size": 10}
                ]
            }],
            "resources": {"fonts": {"f": {"path": font_path}}},
        }
        pdf = rupdf.render_pdf(doc)
        assert len(pdf) > 0


class TestPageDimensions:
    """Test page dimension handling."""

    def test_letter_size(self, font_path):
        """Letter size page should have correct MediaBox."""
        doc = {
            "pages": [{"size": (612, 792), "elements": []}],
            "resources": {"fonts": {}},
        }
        pdf = rupdf.render_pdf(doc)
        assert b"/MediaBox [0 0 612 792]" in pdf or b"/MediaBox[0 0 612 792]" in pdf

    def test_a4_size(self, font_path):
        """A4 size page should have correct MediaBox."""
        doc = {
            "pages": [{"size": (595, 842), "elements": []}],
            "resources": {"fonts": {}},
        }
        pdf = rupdf.render_pdf(doc)
        assert b"/MediaBox [0 0 595 842]" in pdf or b"/MediaBox[0 0 595 842]" in pdf

    def test_custom_size(self, font_path):
        """Custom page size should have correct MediaBox."""
        doc = {
            "pages": [{"size": (400, 600), "elements": []}],
            "resources": {"fonts": {}},
        }
        pdf = rupdf.render_pdf(doc)
        assert b"/MediaBox [0 0 400 600]" in pdf or b"/MediaBox[0 0 400 600]" in pdf
