# Legacy Tests

This directory contains old test files from before the photo-centric architecture refactoring.

## Legacy Test Files

- **`test_routes.py`** - Old API endpoint tests (before photo API)
- **`test_image_processor.py`** - Old image processing tests  
- **`test_exif.py`** - Old EXIF handling tests
- **`test_exif_full.py`** - Extended EXIF tests
- **`run_tests.py`** - Old test runner

## Status

These tests may be outdated and incompatible with the current photo-centric architecture. They are kept for reference but should not be used for current development.

## Current Tests

Use the organized tests in the parent directory:
- `models/` - Photo and Image model tests
- `services/` - ImportSession service tests
- `run_unit_tests.py` - Current test runner

## Migration Notes

Some functionality from these legacy tests may need to be migrated to the new test structure if still relevant.