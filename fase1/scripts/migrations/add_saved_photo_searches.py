"""
Add SavedPhotoSearch table

This migration adds the saved_photo_searches table for storing reusable photo search queries.

Run manually with:
    python scripts/migrations/add_saved_photo_searches.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database.connection import engine
from models.base import Base
from models.saved_photo_search import SavedPhotoSearch


def migrate():
    """Create the saved_photo_searches table"""
    print("Creating saved_photo_searches table...")
    
    # Create only the SavedPhotoSearch table
    SavedPhotoSearch.__table__.create(engine, checkfirst=True)
    
    print("✓ Migration completed successfully")
    print("  - saved_photo_searches table created")


if __name__ == "__main__":
    migrate()
