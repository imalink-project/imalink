# Deprecated Tests

**Moved:** October 16, 2025  
**Reason:** Architecture change from frontend-driven to desktop-first

## Contents

This directory contains tests for deprecated functionality removed during the architecture shift:

### Test Files:

1. **`test_storage_api.py`** (271 lines)
   - Tests for deprecated storage API endpoints
   - Frontend-driven file storage system
   - Reason: Client now handles file operations directly

2. **`test_storage_service.py`** (419 lines)
   - Tests for deprecated StorageService methods
   - `generate_storage_path()`, `validate_storage_path()`, etc.
   - Reason: Storage logic moved to client application

3. **`test_image.py`** (203 lines)
   - Tests for removed Image factory methods
   - `Image.create_from_file()`, `_extract_raw_exif()`, etc.
   - Reason: Frontend-driven architecture removed

4. **`test_import_session.py`** (173 lines)
   - Tests using deprecated `errors` field in ImportSession
   - Frontend-driven import workflow tests
   - Reason: Import workflow changed for desktop client

5. **`test_routes.py`** (from legacy/)
   - Tests for old API structure
   - Deprecated endpoint format tests
   - Reason: API structure modernized

## Why Deprecated?

The Svelte frontend architecture required:
- **Browser-based file processing** → Now done in desktop client
- **Factory methods on models** → Now use repositories/services
- **Complex storage API** → Now direct file system access
- **Frontend-driven workflows** → Now desktop-driven workflows

## Current Test Structure

Active tests are in:
- `tests/integration/` - Full workflow integration tests
- `tests/models/` - Model unit tests (updated for new architecture)
- `tests/services/` - Service layer tests (updated for new architecture)
- `tests/legacy/` - Legacy manual test scripts (still useful)

## Test Results Before Deprecation

- **Total tests:** 80
- **Passing:** 59
- **Failing:** 21 (these files)

After moving deprecated tests:
- **Total tests:** 59
- **Passing:** 59
- **Failing:** 0

## Historical Note

These tests represented valuable functionality that:
1. Validated frontend-driven file processing
2. Tested browser File System Access API integration
3. Verified storage directory generation and validation
4. Ensured factory method correctness

The patterns and logic inform the new desktop client implementation, but the specific test cases are no longer applicable.

## Future Work

New tests needed for:
1. Desktop client file import workflows
2. Direct database access patterns
3. Desktop-driven photo management
4. Client-side EXIF processing
