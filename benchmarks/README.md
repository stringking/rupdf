# rupdf Benchmarks

Performance benchmarks for rupdf. These are NOT part of CI gating.

## Running Benchmarks

### Rust Benchmarks (Criterion)

```bash
cargo bench
```

Results are saved to `target/criterion/`.

### Python Benchmarks

```bash
# Install dependencies
pip install reportlab

# Run comparison benchmark
python benchmarks/run_benchmark.py
```

## Benchmark Scenarios

1. **Empty document** - Minimal PDF generation overhead
2. **Text-heavy** - Many text elements (simulates reports)
3. **Graphics-heavy** - Rectangles, lines, shapes
4. **Mixed content** - Text, graphics, barcodes
5. **Multi-page** - 10-page document

## Notes

- Benchmark results depend heavily on hardware and system load
- First run may be slower due to font loading/caching
- ReportLab comparison requires `reportlab` package installed
- Results are for reference only - not used for CI gating
