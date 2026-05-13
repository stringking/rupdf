"""Tests for font fallback chains and missing_glyph_policy.

Uses the IBM Plex Sans / Mono asset pair to exercise the fallback path:
- '─' (U+2500, box drawing) is in IBM Plex Mono's cmap but not Plex Sans's.
- '❤' (U+2764, heart) is in neither.
"""

from pathlib import Path

import pytest
import rupdf


ASSETS = Path(__file__).parent.parent.parent / "assets"
SANS_PATH = ASSETS / "IBMPlexSans-Regular.otf"
MONO_PATH = ASSETS / "IBMPlexMono-Regular.otf"

HEART = "❤"          # in neither font
BOX_DRAWING = "─"    # in Mono only


def _check_assets():
    if not SANS_PATH.exists() or not MONO_PATH.exists():
        pytest.skip("Required test fonts not present in assets/")


def _doc(elements, *, with_mono=True):
    _check_assets()
    fonts = {"sans": {"path": str(SANS_PATH)}}
    if with_mono:
        fonts["mono"] = {"path": str(MONO_PATH)}
    return {
        "pages": [{"size": (612.0, 792.0), "elements": elements}],
        "resources": {"fonts": fonts},
    }


class TestMissingGlyphDefault:
    """Default policy is 'drop' — uncovered chars are silently omitted."""

    def test_text_with_uncovered_char_renders_by_default(self):
        doc = _doc([
            {"type": "text", "x": 50, "y": 100,
             "text": f"Tony {HEART} Dorn",
             "font": "sans", "size": 12},
        ], with_mono=False)
        pdf = rupdf.render_pdf(doc)
        assert pdf.startswith(b"%PDF-")

    def test_textbox_with_uncovered_char_renders_by_default(self):
        doc = _doc([
            {"type": "textbox", "x": 50, "y": 100, "w": 400, "h": 200,
             "text": f"Tony {HEART} Dorn",
             "font": "sans", "size": 12},
        ], with_mono=False)
        pdf = rupdf.render_pdf(doc)
        assert pdf.startswith(b"%PDF-")


class TestMissingGlyphRaise:
    """policy='raise' preserves the legacy MissingGlyph error."""

    def test_text_with_raise_policy_errors(self):
        doc = _doc([
            {"type": "text", "x": 50, "y": 100,
             "text": f"Tony {HEART} Dorn",
             "font": "sans", "size": 12,
             "missing_glyph_policy": "raise"},
        ], with_mono=False)
        with pytest.raises(rupdf.RupdfError) as exc:
            rupdf.render_pdf(doc)
        assert HEART in str(exc.value)
        assert "sans" in str(exc.value)

    def test_textbox_with_raise_policy_errors(self):
        doc = _doc([
            {"type": "textbox", "x": 50, "y": 100, "w": 400, "h": 200,
             "text": f"Tony {HEART} Dorn",
             "font": "sans", "size": 12,
             "missing_glyph_policy": "raise"},
        ], with_mono=False)
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)

    def test_invalid_policy_name_rejected(self):
        doc = _doc([
            {"type": "text", "x": 50, "y": 100, "text": "hello",
             "font": "sans", "size": 12,
             "missing_glyph_policy": "ignore"},
        ], with_mono=False)
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)


class TestFontFallbackChain:
    """Fallback resolves chars the primary font doesn't cover."""

    def test_fallback_covers_uncovered_char(self):
        # '─' is in Mono but not Sans. Without fallback, raise policy fires.
        # With Mono as fallback, the char is resolved via the fallback and
        # the render succeeds.
        doc = _doc([
            {"type": "text", "x": 50, "y": 100,
             "text": f"A{BOX_DRAWING}B",
             "font": "sans", "font_fallback": ["mono"], "size": 12,
             "missing_glyph_policy": "raise"},
        ])
        pdf = rupdf.render_pdf(doc)
        assert pdf.startswith(b"%PDF-")

    def test_fallback_misses_still_drops(self):
        # Heart isn't in either; drop policy lets the render proceed.
        doc = _doc([
            {"type": "text", "x": 50, "y": 100,
             "text": f"Tony {HEART} Dorn",
             "font": "sans", "font_fallback": ["mono"], "size": 12,
             "missing_glyph_policy": "drop"},
        ])
        pdf = rupdf.render_pdf(doc)
        assert pdf.startswith(b"%PDF-")

    def test_fallback_misses_raises_with_raise_policy(self):
        # Heart isn't in either font; raise policy fires after the chain.
        doc = _doc([
            {"type": "text", "x": 50, "y": 100,
             "text": f"Tony {HEART} Dorn",
             "font": "sans", "font_fallback": ["mono"], "size": 12,
             "missing_glyph_policy": "raise"},
        ])
        with pytest.raises(rupdf.RupdfError) as exc:
            rupdf.render_pdf(doc)
        # Error names the primary font, not whichever fallback was tried last.
        assert "sans" in str(exc.value)

    def test_fallback_in_textbox_wraps_correctly(self):
        # Box drawing chars hit the fallback inside a wrapped paragraph.
        doc = _doc([
            {"type": "textbox", "x": 50, "y": 100, "w": 300, "h": 200,
             "text": f"line one {BOX_DRAWING} mid {BOX_DRAWING} end",
             "font": "sans", "font_fallback": ["mono"], "size": 12},
        ])
        pdf = rupdf.render_pdf(doc)
        assert pdf.startswith(b"%PDF-")

    def test_unknown_fallback_alias_raises(self):
        # Fallback referencing an unregistered font should fail with the
        # standard MissingFont error, not silently ignore.
        doc = _doc([
            {"type": "text", "x": 50, "y": 100, "text": "hello",
             "font": "sans", "font_fallback": ["does_not_exist"], "size": 12},
        ])
        with pytest.raises(rupdf.RupdfError):
            rupdf.render_pdf(doc)

    def test_empty_fallback_is_no_op(self):
        doc = _doc([
            {"type": "text", "x": 50, "y": 100, "text": "hello world",
             "font": "sans", "font_fallback": [], "size": 12},
        ], with_mono=False)
        pdf = rupdf.render_pdf(doc)
        assert pdf.startswith(b"%PDF-")


class TestFallbackEmbedsBothFonts:
    """Both primary and fallback fonts should embed when both are used."""

    def test_both_fonts_appear_in_pdf(self):
        doc = _doc([
            {"type": "text", "x": 50, "y": 100,
             "text": f"A{BOX_DRAWING}B",
             "font": "sans", "font_fallback": ["mono"], "size": 12},
        ])
        pdf = rupdf.render_pdf(doc, compress=False)
        # Both PostScript names should appear in the font resource dict.
        assert b"IBMPlexSans" in pdf
        assert b"IBMPlexMono" in pdf

    def test_unused_fallback_not_embedded(self):
        # Text fits entirely in Sans; Mono fallback is declared but unused.
        doc = _doc([
            {"type": "text", "x": 50, "y": 100, "text": "all ASCII here",
             "font": "sans", "font_fallback": ["mono"], "size": 12},
        ])
        pdf = rupdf.render_pdf(doc, compress=False)
        assert b"IBMPlexSans" in pdf
        # Mono shouldn't be embedded since no char resolved to it.
        assert b"IBMPlexMono" not in pdf
