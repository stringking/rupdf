//! Font fallback resolution and wrapping for mixed-font text.
//!
//! A text element's font configuration is a primary font plus an ordered
//! list of fallbacks (the "chain"). For each character, the resolver picks
//! the first font in the chain whose cmap covers it. Characters covered by
//! no font in the chain are dropped or raise, per the element's
//! `MissingGlyphPolicy`.
//!
//! The output is char-aligned: a `Vec<ResolvedChar>` parallel to the input
//! string, with each char tagged by its chain index + glyph id (or None for
//! control characters and dropped characters). Downstream code groups
//! contiguous same-font chars into render runs (for `Tf`+`Tj` emission) and
//! sums per-char advances for measurement.
//!
//! Forward-compatibility: a future styled-runs API will call `resolve` per
//! user-supplied run (one resolve call per `{text, font, ...}` entry), then
//! drive wrapping over a flattened sequence of resolved chars. The
//! per-char output structure absorbs that change without breaking.

use crate::error::{Result, RupdfError};
use crate::resources::LoadedFont;
use crate::types::MissingGlyphPolicy;

/// A single character after font-chain resolution.
#[derive(Debug, Clone)]
pub struct ResolvedChar {
    pub ch: char,
    /// `(chain_index, glyph_id)` if a font in the chain covers `ch`.
    /// `None` for control characters (\n, \t, …), which carry structural
    /// meaning for wrapping but emit no glyph.
    pub glyph: Option<(usize, u16)>,
}

impl ResolvedChar {
    pub fn advance_pts(&self, chain: &[&LoadedFont], size: f32) -> f32 {
        match self.glyph {
            Some((idx, gid)) => chain[idx].advance_pts(gid, size),
            None => 0.0,
        }
    }
}

/// A contiguous run of resolved characters that share the same font.
/// Built lazily by `group_runs`.
#[derive(Debug, Clone)]
pub struct RenderRun<'a> {
    pub chain_index: usize,
    pub font_alias: &'a str,
    /// (char, glyph_id) pairs. The char is kept for ToUnicode mapping.
    pub glyphs: Vec<(char, u16)>,
}

/// Resolve every character in `text` against the font chain.
///
/// Control characters (`is_control()`) pass through with `glyph: None`.
/// Characters with no covering font:
///   - `Drop`: silently omitted.
///   - `Raise`: returns `RupdfError::MissingGlyph` naming the primary font.
pub fn resolve(
    text: &str,
    chain: &[&LoadedFont],
    chain_names: &[&str],
    policy: MissingGlyphPolicy,
) -> Result<Vec<ResolvedChar>> {
    debug_assert_eq!(chain.len(), chain_names.len());
    debug_assert!(!chain.is_empty(), "resolve called with empty chain");

    let mut out = Vec::with_capacity(text.len());
    for ch in text.chars() {
        if ch.is_control() {
            out.push(ResolvedChar { ch, glyph: None });
            continue;
        }
        let hit = chain
            .iter()
            .enumerate()
            .find_map(|(idx, font)| font.glyph_id_opt(ch).map(|gid| (idx, gid)));
        match hit {
            Some((idx, gid)) => out.push(ResolvedChar {
                ch,
                glyph: Some((idx, gid)),
            }),
            None => match policy {
                MissingGlyphPolicy::Drop => {}
                MissingGlyphPolicy::Raise => {
                    return Err(RupdfError::MissingGlyph {
                        glyph: ch,
                        font: chain_names[0].to_string(),
                    });
                }
            },
        }
    }
    Ok(out)
}

/// Group a resolved-char sequence into contiguous same-font render runs.
/// Chars with `glyph: None` (control / dropped) are excluded from runs;
/// they remain visible in the source sequence for wrapping decisions.
pub fn group_runs<'a>(
    chars: &[ResolvedChar],
    chain_names: &[&'a str],
) -> Vec<RenderRun<'a>> {
    let mut runs: Vec<RenderRun<'a>> = Vec::new();
    for c in chars {
        let Some((idx, gid)) = c.glyph else { continue };
        match runs.last_mut() {
            Some(r) if r.chain_index == idx => r.glyphs.push((c.ch, gid)),
            _ => runs.push(RenderRun {
                chain_index: idx,
                font_alias: chain_names[idx],
                glyphs: vec![(c.ch, gid)],
            }),
        }
    }
    runs
}

/// Sum the advance widths (in points) of a resolved-char slice.
pub fn measure(chars: &[ResolvedChar], chain: &[&LoadedFont], size: f32) -> f32 {
    chars.iter().map(|c| c.advance_pts(chain, size)).sum()
}

/// Word-wrap `text` against the font chain to lines that fit within
/// `max_width` points. Splits paragraphs on '\n' and words on whitespace
/// (any run of whitespace collapses to a single space — matches the
/// previous single-font wrap behavior). Returns one `Vec<ResolvedChar>`
/// per output line.
pub fn wrap(
    text: &str,
    chain: &[&LoadedFont],
    chain_names: &[&str],
    size: f32,
    max_width: f32,
    policy: MissingGlyphPolicy,
) -> Result<Vec<Vec<ResolvedChar>>> {
    // Pre-resolve a single space for inter-word spacing. Space is in every
    // reasonable font's cmap, but if all fonts in the chain somehow lack
    // it, fall back to zero-width (the policy applies only to the input
    // string's chars, not to internal spacing).
    let space_chars = resolve(" ", chain, chain_names, MissingGlyphPolicy::Drop)?;
    let space_width = measure(&space_chars, chain, size);

    let mut lines: Vec<Vec<ResolvedChar>> = Vec::new();

    for paragraph in text.split('\n') {
        if paragraph.is_empty() {
            lines.push(Vec::new());
            continue;
        }

        let words: Vec<&str> = paragraph.split_whitespace().collect();
        if words.is_empty() {
            lines.push(Vec::new());
            continue;
        }

        let mut current_line: Vec<ResolvedChar> = Vec::new();
        let mut current_width = 0.0;

        for word in words {
            let word_chars = resolve(word, chain, chain_names, policy)?;
            let word_width = measure(&word_chars, chain, size);

            if current_line.is_empty() {
                current_line = word_chars;
                current_width = word_width;
            } else if current_width + space_width + word_width <= max_width {
                current_line.extend(space_chars.iter().cloned());
                current_line.extend(word_chars);
                current_width += space_width + word_width;
            } else {
                lines.push(std::mem::take(&mut current_line));
                current_line = word_chars;
                current_width = word_width;
            }
        }

        if !current_line.is_empty() {
            lines.push(current_line);
        }
    }

    Ok(lines)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::FontSource;
    use std::path::PathBuf;

    fn assets_dir() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("assets")
    }

    fn load_sans() -> LoadedFont {
        let path = assets_dir().join("IBMPlexSans-Regular.otf");
        LoadedFont::load("sans", &FontSource::Path(path.to_str().unwrap().to_string())).unwrap()
    }

    #[test]
    fn resolve_single_font_all_covered() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let chars = resolve("Hello", &chain, &names, MissingGlyphPolicy::Drop).unwrap();
        assert_eq!(chars.len(), 5);
        for c in &chars {
            assert!(c.glyph.is_some());
            assert_eq!(c.glyph.unwrap().0, 0); // primary
        }
    }

    #[test]
    fn resolve_drops_uncovered_chars() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        // ❤ U+2764 is not in IBM Plex Sans.
        let chars = resolve("A❤B", &chain, &names, MissingGlyphPolicy::Drop).unwrap();
        // Heart dropped, A and B kept.
        assert_eq!(chars.len(), 2);
        assert_eq!(chars[0].ch, 'A');
        assert_eq!(chars[1].ch, 'B');
    }

    #[test]
    fn resolve_raises_on_uncovered_when_strict() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let err = resolve("A❤B", &chain, &names, MissingGlyphPolicy::Raise).unwrap_err();
        match err {
            RupdfError::MissingGlyph { glyph, font } => {
                assert_eq!(glyph, '❤');
                assert_eq!(font, "sans");
            }
            other => panic!("expected MissingGlyph, got {:?}", other),
        }
    }

    #[test]
    fn resolve_preserves_control_chars() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let chars = resolve("A\nB", &chain, &names, MissingGlyphPolicy::Drop).unwrap();
        assert_eq!(chars.len(), 3);
        assert_eq!(chars[1].ch, '\n');
        assert!(chars[1].glyph.is_none());
    }

    #[test]
    fn group_runs_single_font() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let chars = resolve("Hello", &chain, &names, MissingGlyphPolicy::Drop).unwrap();
        let runs = group_runs(&chars, &names);
        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].glyphs.len(), 5);
        assert_eq!(runs[0].font_alias, "sans");
    }

    #[test]
    fn group_runs_skips_control_chars() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let chars = resolve("A\nB", &chain, &names, MissingGlyphPolicy::Drop).unwrap();
        let runs = group_runs(&chars, &names);
        // \n produces no run; A and B fold into a single same-font run.
        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].glyphs.len(), 2);
    }

    #[test]
    fn wrap_no_break_when_fits() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let lines = wrap("hello world", &chain, &names, 12.0, 500.0, MissingGlyphPolicy::Drop).unwrap();
        assert_eq!(lines.len(), 1);
    }

    #[test]
    fn wrap_breaks_on_width() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let lines = wrap("hello world", &chain, &names, 12.0, 30.0, MissingGlyphPolicy::Drop).unwrap();
        assert!(lines.len() >= 2);
    }

    #[test]
    fn wrap_paragraph_break_on_newline() {
        let font = load_sans();
        let chain = vec![&font];
        let names = vec!["sans"];
        let lines = wrap("a\nb", &chain, &names, 12.0, 500.0, MissingGlyphPolicy::Drop).unwrap();
        assert_eq!(lines.len(), 2);
    }
}
