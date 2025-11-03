# Scripts Directory

This directory contains utility scripts for ImaLink development and maintenance.

## Structure

### `migrations/`
Database migration scripts for schema updates:
- `migrate_authors.py` - Add email/bio fields to authors table
- `migrate_database.py` - General database migrations
- `migrate_import_stats.py` - Add import statistics tracking
- `migrate_raw_support.py` - Add RAW file format support
- `migrate_single_raw_skipped.py` - Handle single RAW file skip logic

### `maintenance/`
Database and system maintenance tools:
- `cleanup_redundant_field.py` - Clean up unused database fields
- `optimize_database.py` - Optimize database performance and storage
- `reset_database.py` - Reset database to clean state (⚠️ DESTRUCTIVE)

### `debug/`
Debugging and diagnostic tools:
- `diagnose_exif.py` - Analyze EXIF data in images
- `fix_image_dimensions.py` - Fix image dimension issues

### `testing/`
Development testing scripts:
- `test_exif_rotation.py` - Test EXIF rotation handling
- `test_exif_stripping.py` - Test EXIF data stripping
- `test_rotation_hash.py` - Test rotation hash calculation
- `test_thumbnail_direct.py` - Test direct hotpreview generation
- `test_thumbnail_rotation.py` - Test hotpreview rotation

## Usage

All scripts should be run from the `fase1/` directory to ensure proper import paths:

```bash
cd fase1
python scripts/maintenance/optimize_database.py
python scripts/testing/test_exif_rotation.py
```

## Important Notes

- ⚠️ **Always backup your database** before running migration or maintenance scripts
- Scripts in `maintenance/` can modify or delete data - use with caution
- Testing scripts are safe to run and won't modify production data
- Scripts assume the database is located at `C:\temp\imalink.db`