# Legacy Test Scripts

**Note:** These are legacy test scripts kept for reference. 

## Modern Unit Tests
The main test suite has moved to `/fase1/tests/`. Please use:
```bash
cd /home/kjell/git_prosjekt/imalink/fase1/tests
python run_unit_tests.py
```

## Files in this directory

### test_image_service.py
Legacy test script for ImageService. 

**Status:** Reference only - use modern tests in `tests/services/` instead.

### test_modernized_api.py
Legacy API test script.

**Status:** Reference only - use modern tests in `tests/api/` instead.

## Recommendation
These files are kept for reference during development but should not be used for regular testing. All active tests are in the `tests/` directory with proper pytest integration.
