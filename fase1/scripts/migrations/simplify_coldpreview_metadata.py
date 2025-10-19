#!/usr/bin/env python3
"""
Migration: Simplify coldpreview metadata storage

This migration removes redundant coldpreview metadata columns from the photos table,
keeping only coldpreview_path. Width, height, and size will be read dynamically 
from the actual image files when needed.

Removes columns:
- coldpreview_width 
- coldpreview_height
- coldpreview_size

Keeps column:
- coldpreview_path (needed to locate the file)

Benefits:
- Eliminates data inconsistency (metadata always matches file)
- Reduces database size
- Simplifies maintenance
- Self-healing system (corrupt metadata fixes itself)
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import text
from database.connection import get_database_engine


def migrate_up():
    """Remove redundant coldpreview metadata columns"""
    
    engine = get_database_engine()
    
    print("🔄 Starting coldpreview metadata simplification migration...")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if columns exist before dropping
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'photos' 
                AND column_name IN ('coldpreview_width', 'coldpreview_height', 'coldpreview_size')
            """))
            
            existing_columns = [row[0] for row in result]
            print(f"📋 Found existing columns: {existing_columns}")
            
            # Drop redundant columns if they exist
            for column in ['coldpreview_width', 'coldpreview_height', 'coldpreview_size']:
                if column in existing_columns:
                    print(f"🗑️  Dropping column: {column}")
                    conn.execute(text(f"ALTER TABLE photos DROP COLUMN {column}"))
                else:
                    print(f"⏭️  Column {column} already removed, skipping")
            
            # Verify remaining structure
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'photos' 
                AND column_name LIKE '%coldpreview%'
                ORDER BY column_name
            """))
            
            remaining_columns = list(result)
            print(f"✅ Remaining coldpreview columns: {remaining_columns}")
            
            # Commit transaction
            trans.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise


def migrate_down():
    """Restore redundant coldpreview metadata columns (if needed for rollback)"""
    
    engine = get_database_engine()
    
    print("🔄 Rolling back coldpreview metadata simplification...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Add back the columns (they will be NULL initially)
            conn.execute(text("ALTER TABLE photos ADD COLUMN coldpreview_width INTEGER"))
            conn.execute(text("ALTER TABLE photos ADD COLUMN coldpreview_height INTEGER"))  
            conn.execute(text("ALTER TABLE photos ADD COLUMN coldpreview_size INTEGER"))
            
            print("⚠️  Columns restored but will contain NULL values")
            print("⚠️  Run data repair script to populate from actual files")
            
            trans.commit()
            print("✅ Rollback completed!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Rollback failed: {e}")
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Coldpreview metadata simplification migration")
    parser.add_argument("--down", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.down:
        migrate_down()
    else:
        migrate_up()