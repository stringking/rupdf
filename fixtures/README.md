# rupdf Test Fixtures

Shared JSON document definitions used by both Rust and Python tests/benchmarks.

## Fixture Files

| File | Description |
|------|-------------|
| `simple_text.json` | Single page with basic text elements |
| `multi_page.json` | Multi-page document with varied content |
| `all_elements.json` | All element types (text, rect, line, image, barcode) |
| `stress_test.json` | Large document for benchmarking |

## Schema

All fixtures follow the rupdf document schema:

```json
{
  "metadata": {
    "title": "optional",
    "author": "optional",
    "subject": "optional",
    "creator": "optional"
  },
  "pages": [
    {
      "width": 612.0,
      "height": 792.0,
      "background": [255, 255, 255, 255],
      "elements": [...]
    }
  ],
  "resources": {
    "fonts": {
      "name": {"path": "/path/to/font.ttf"} | {"bytes": [...]}
    },
    "images": {
      "name": {"path": "/path/to/image"} | {"bytes": [...]}
    }
  }
}
```

## Usage

### Rust Tests
```rust
let fixture = include_str!("../../fixtures/simple_text.json");
let doc: serde_json::Value = serde_json::from_str(fixture)?;
```

### Python Tests
```python
import json
from pathlib import Path

fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
with open(fixtures_dir / "simple_text.json") as f:
    doc = json.load(f)
```

## Notes

- Fixtures use placeholder paths for fonts/images that must be resolved at runtime
- Tests should provide actual font/image data or skip if resources unavailable
- Benchmark fixtures should be deterministic for reproducible results
