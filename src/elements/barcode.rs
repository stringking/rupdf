// Barcode utilities
// Code 128 generation is done via the `barcoders` crate.
// This module hosts helpers for the GS1-128 variant (parenthesized AI parsing
// and FNC1 placement).

use crate::error::{Result, RupdfError};

// FNC1 character recognized by the `barcoders` Code 128 encoder.
pub const FNC1: char = '\u{0179}';
// Code B start character recognized by the `barcoders` Code 128 encoder.
pub const CODE_B_START: char = '\u{0181}';

/// A parsed GS1 Application Identifier and its associated data.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AiField {
    pub ai: String,
    pub data: String,
}

/// Parse a GS1-128 input string in parenthesized form, e.g.
/// `(01)12345678901234(17)260101(10)BATCH123`.
pub fn parse_gs1_value(value: &str) -> Result<Vec<AiField>> {
    let mut fields = Vec::new();
    let mut chars = value.chars().peekable();

    while let Some(&c) = chars.peek() {
        if c != '(' {
            return Err(RupdfError::InvalidBarcode {
                value: value.to_string(),
                reason: "GS1-128 value must begin with '(' and use (AI)data syntax".to_string(),
            });
        }
        chars.next(); // consume '('

        let mut ai = String::new();
        let mut closed = false;
        for ch in chars.by_ref() {
            if ch == ')' {
                closed = true;
                break;
            }
            ai.push(ch);
        }
        if !closed {
            return Err(RupdfError::InvalidBarcode {
                value: value.to_string(),
                reason: "Unterminated AI: missing ')'".to_string(),
            });
        }
        if ai.is_empty() || ai.len() > 4 || !ai.chars().all(|c| c.is_ascii_digit()) {
            return Err(RupdfError::InvalidBarcode {
                value: value.to_string(),
                reason: format!("Invalid Application Identifier '{}': must be 2-4 digits", ai),
            });
        }

        let mut data = String::new();
        while let Some(&ch) = chars.peek() {
            if ch == '(' {
                break;
            }
            data.push(ch);
            chars.next();
        }
        if data.is_empty() {
            return Err(RupdfError::InvalidBarcode {
                value: value.to_string(),
                reason: format!("AI ({}) has no data", ai),
            });
        }
        if let Some(expected) = fixed_ai_length(&ai) {
            if data.len() != expected {
                return Err(RupdfError::InvalidBarcode {
                    value: value.to_string(),
                    reason: format!(
                        "AI ({}) requires exactly {} characters of data, got {}",
                        ai,
                        expected,
                        data.len()
                    ),
                });
            }
        }

        fields.push(AiField { ai, data });
    }

    if fields.is_empty() {
        return Err(RupdfError::InvalidBarcode {
            value: value.to_string(),
            reason: "GS1-128 value must contain at least one (AI)data pair".to_string(),
        });
    }

    Ok(fields)
}

/// Build the Code 128 input string for the `barcoders` crate.
/// Starts with Code B + FNC1 (the GS1-128 designator), then each AI+data,
/// inserting FNC1 between variable-length fields.
pub fn build_code128_input(fields: &[AiField]) -> String {
    let mut out = String::new();
    out.push(CODE_B_START);
    out.push(FNC1);
    for (i, field) in fields.iter().enumerate() {
        out.push_str(&field.ai);
        out.push_str(&field.data);
        let is_last = i + 1 == fields.len();
        let is_variable = fixed_ai_length(&field.ai).is_none();
        if !is_last && is_variable {
            out.push(FNC1);
        }
    }
    out
}

/// Format the parsed fields back into the canonical parenthesized form used
/// for the human-readable text below the barcode.
pub fn format_human_readable(fields: &[AiField]) -> String {
    let mut out = String::new();
    for field in fields {
        out.push('(');
        out.push_str(&field.ai);
        out.push(')');
        out.push_str(&field.data);
    }
    out
}

/// Returns the required data length for a fixed-length GS1 AI, or `None` if
/// the AI is variable-length (and therefore needs an FNC1 terminator when
/// followed by another field).
///
/// Sourced from the GS1 General Specifications. Lengths exclude the AI itself.
pub fn fixed_ai_length(ai: &str) -> Option<usize> {
    match ai {
        "00" => Some(18),
        "01" | "02" | "03" => Some(14),
        "04" => Some(16),
        "11" | "12" | "13" | "14" | "15" | "16" | "17" | "18" | "19" => Some(6),
        "20" => Some(2),
        "41" => Some(13),
        // 31xx-36xx: measurements, all 6 digits
        s if s.len() == 4 && s.starts_with(|c: char| c == '3')
            && matches!(&s[1..2], "1" | "2" | "3" | "4" | "5" | "6")
            && s[2..].chars().all(|c| c.is_ascii_digit()) =>
        {
            Some(6)
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_single_fixed_ai() {
        let fields = parse_gs1_value("(01)12345678901234").unwrap();
        assert_eq!(fields, vec![AiField { ai: "01".into(), data: "12345678901234".into() }]);
    }

    #[test]
    fn parses_multiple_ais() {
        let fields = parse_gs1_value("(01)12345678901234(17)260101(10)BATCH123").unwrap();
        assert_eq!(fields.len(), 3);
        assert_eq!(fields[0].ai, "01");
        assert_eq!(fields[1].ai, "17");
        assert_eq!(fields[2].data, "BATCH123");
    }

    #[test]
    fn rejects_missing_open_paren() {
        assert!(parse_gs1_value("01)12345678901234").is_err());
    }

    #[test]
    fn rejects_unterminated_ai() {
        assert!(parse_gs1_value("(0112345678901234").is_err());
    }

    #[test]
    fn rejects_non_numeric_ai() {
        assert!(parse_gs1_value("(AB)foo").is_err());
    }

    #[test]
    fn rejects_empty_data() {
        assert!(parse_gs1_value("(01)").is_err());
    }

    #[test]
    fn rejects_wrong_length_for_fixed_ai() {
        // AI 01 requires exactly 14 digits
        assert!(parse_gs1_value("(01)12345").is_err());
    }

    #[test]
    fn fixed_ai_lookup() {
        assert_eq!(fixed_ai_length("01"), Some(14));
        assert_eq!(fixed_ai_length("17"), Some(6));
        assert_eq!(fixed_ai_length("3103"), Some(6));
        assert_eq!(fixed_ai_length("3920"), None); // 39xx is variable
        assert_eq!(fixed_ai_length("10"), None);
        assert_eq!(fixed_ai_length("21"), None);
    }

    #[test]
    fn builds_code128_input_no_separator_after_fixed() {
        let fields = vec![
            AiField { ai: "01".into(), data: "12345678901234".into() },
            AiField { ai: "17".into(), data: "260101".into() },
        ];
        let s = build_code128_input(&fields);
        // Code B start + FNC1 + 01 + data + 17 + data (no internal FNC1, both fixed)
        let expected = format!("{}{}0112345678901234{}", CODE_B_START, FNC1, "17260101");
        assert_eq!(s, expected);
    }

    #[test]
    fn builds_code128_input_separator_after_variable() {
        let fields = vec![
            AiField { ai: "10".into(), data: "BATCH".into() },
            AiField { ai: "01".into(), data: "12345678901234".into() },
        ];
        let s = build_code128_input(&fields);
        // After variable-length 10/BATCH there must be an FNC1 before 01
        let expected = format!(
            "{}{}10BATCH{}0112345678901234",
            CODE_B_START, FNC1, FNC1
        );
        assert_eq!(s, expected);
    }

    #[test]
    fn builds_code128_input_no_trailing_fnc1() {
        let fields = vec![
            AiField { ai: "01".into(), data: "12345678901234".into() },
            AiField { ai: "10".into(), data: "BATCH".into() },
        ];
        let s = build_code128_input(&fields);
        assert!(!s.ends_with(FNC1));
    }

    #[test]
    fn format_human_readable_roundtrips() {
        let raw = "(01)12345678901234(10)BATCH123";
        let fields = parse_gs1_value(raw).unwrap();
        assert_eq!(format_human_readable(&fields), raw);
    }
}
