// Element rendering is handled directly in pdf/writer.rs
// This module is reserved for future element-specific utilities.
//
// Barcode encoding (Code 128, GS1-128) lives in the `rubar-core` crate.
// SVG rasterization stays here since it's PDF-specific.

pub mod svg;
