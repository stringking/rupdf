# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/), and this project adheres
to [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-05-13

### Added

- **Font fallback chains** on `text` and `textbox` elements. A new
  `font_fallback: list[str]` field accepts an ordered list of font aliases
  tried in turn for characters absent from the primary font's cmap. The
  primary font still drives metrics (baseline, ascender, descender,
  line-height, cap-height); fallback chars share that baseline. Used to
  render emoji, CJK, Arabic, Cyrillic, etc. without crashing or showing
  tofu. Wrapping in `textbox` honors per-character advances across mixed
  fonts. Fallback fonts that no character resolves to are not embedded.
- **`missing_glyph_policy`** field on `text` and `textbox` elements,
  accepting `"drop"` (default) or `"raise"`. Controls what happens when no
  font in the chain covers a character.

### Changed

- **Default behavior on uncovered characters: previously raised
  `RupdfError::MissingGlyph`; now silently drops the character.** The old
  behavior is available via `missing_glyph_policy: "raise"`. This matches
  what every other PDF renderer (browsers, ReportLab, FPDF) does by
  default and unblocks rendering of user-supplied text containing emoji
  or codepoints outside the embedded font's coverage.
- Per-character cmap lookups now live in `src/runs.rs`. Internal-only
  refactor; PDF output is byte-identical for documents that don't have
  uncovered characters or fallback chains.

### Removed

- `LoadedFont::glyph_id`, `LoadedFont::text_width`, and
  `LoadedFont::wrap_text` (Rust-only internal API). Their work moved into
  `crate::runs::{resolve, measure, wrap}`, which operate over the font
  chain rather than a single font.
- `FontEmbedder::use_char`, `use_text`, and `encode_text`. Callers now
  pre-resolve characters via `runs::resolve` and register them with the
  new `FontEmbedder::use_glyph(ch, glyph_id)`. The Python API is
  unaffected.
