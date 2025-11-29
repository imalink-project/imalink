# PhotoCreateSchema Test Fixtures

Pre-generated PhotoCreateSchema JSON files for testing imalink backend.

## Overview

These fixtures are in **OLD format** (imalink-core v1) and are automatically converted to the new format by `load_photo_create_schema()`.

**TODO:** Regenerate these fixtures in the new format when imalink-core is rewritten.

## Files

| File | Description | Features |
|------|-------------|----------|
| `basic.json` | Standard JPEG | Full EXIF, no GPS, hotpreview only |
| `basic_with_coldpreview.json` | Standard JPEG | Same as basic + coldpreview |
| `no_exif.json` | JPEG without EXIF | Minimal metadata |
| `gps.json` | JPEG with GPS | GPS coordinates (Tuscany, Italy) |
| `rotated.json` | Portrait photo | EXIF rotation applied |
| `landscape.json` | Landscape photo | Wide format, hotpreview only |
| `landscape_with_coldpreview.json` | Landscape photo | Wide format + coldpreview |
| `png.json` | PNG format | No EXIF support |
| `tiny.json` | Very small image | 100x100 pixels |
| `canon.json` | Canon camera | Canon 40D EXIF |
| `fuji.json` | Fuji camera | Full EXIF metadata |
| `fuji_with_coldpreview.json` | Fuji camera | Full EXIF + coldpreview |

## Usage

```python
from tests.fixtures.photo_eggs import load_photoegg

# Load a specific fixture
photoegg = load_photoegg("basic")

# Use in tests
response = client.post(
    "/api/v1/photos/new-photo",
    json=photoegg,
    headers=auth_headers
)
```

## Regenerating Fixtures

If PhotoEgg schema changes in imalink-core:

```bash
# Start imalink-core service
cd ../imalink-core
uv run python -m service.main

# Generate fixtures (in separate terminal)
cd ../imalink
uv run python scripts/generate_photoegg_fixtures.py
```

## Contract

PhotoEgg schema is defined in `imalink-core` - this is the **source of truth**.
Backend must accept whatever structure imalink-core produces.

See: `docs/CONTRACTS.md` for PhotoEgg specification.
