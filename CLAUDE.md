# Claude Development Guide

## Project Overview

rupdf is a fast PDF renderer in Rust with Python bindings (PyO3). It takes pre-laid-out document definitions (dicts) and renders them to PDF bytes.

## Architecture

```
src/
├── lib.rs           # PyO3 module entry point
├── error.rs         # RupdfError enum + Python exception
├── types.rs         # Document/Page/Element structs, parsing from Python dicts
├── render.rs        # Main render_pdf() entry point
├── resources.rs     # Font/image loading (LoadedFont, LoadedImage)
├── pdf/
│   ├── mod.rs       # Tests
│   ├── writer.rs    # PdfGenerator - coordinates PDF generation
│   └── fonts.rs     # FontEmbedder - font subsetting and CID embedding
└── elements/
    └── svg.rs       # SVG to PDF vector conversion

python/rupdf/
├── __init__.py      # Re-exports render_pdf, RupdfError
├── _rupdf.pyi       # Type stubs for the Rust module
└── __init__.pyi     # Type stubs for the package
```

## Key Design Decisions

- **Coordinate system**: Top-left origin, y increases downward (converted to PDF's bottom-left internally)
- **Font embedding**: CIDFont Type2 with subsetting (only used glyphs)
- **Images**: Raster images re-encoded as JPEG at 300 DPI; SVGs converted to vector paths
- **Graphics state**: Each element wrapped in save_state/restore_state to isolate alpha/color changes

## Build & Test

```bash
# Development build
maturin develop

# Run tests
cargo test                    # Rust tests
pytest python/tests/ -v       # Python tests

# Generate test PDF
python scripts/generate_test_pdf.py --svg image.svg --png image.png
```

## Release Process

1. Update version in both `Cargo.toml` and `pyproject.toml`
2. Build wheels:
   ```bash
   # macOS
   maturin build --release -i python3.11 -i python3.12

   # Linux (via Docker)
   docker run --rm -v "$(pwd)":/io ghcr.io/pyo3/maturin build --release -i python3.12
   docker run --rm -v "$(pwd)":/io ghcr.io/pyo3/maturin sdist
   ```
3. Upload to PyPI:
   ```bash
   twine upload target/wheels/rupdf-VERSION*
   ```
4. Create GitHub release:
   ```bash
   gh release create vVERSION --title "vVERSION" --notes "Release notes"
   ```

## Adding New Element Types

1. Add struct to `src/types.rs` with `from_py()` parser
2. Add variant to `Element` enum
3. Add `render_*` method in `src/pdf/writer.rs`
4. Call it from `render_page_content()` match
5. Update type stubs in `python/rupdf/_rupdf.pyi`
6. Update README.md with example
7. Add to `scripts/generate_test_pdf.py`

## Dependencies

| Crate | Purpose |
|-------|---------|
| pyo3 | Python bindings |
| pdf-writer | Low-level PDF generation |
| ttf-parser | Font metrics |
| subsetter | Font subsetting |
| image | Raster image decoding |
| resvg/usvg | SVG parsing and rendering |
| barcoders | Code 128 barcodes |
| qrcode | QR code generation |
| miniz_oxide | Zlib compression |
