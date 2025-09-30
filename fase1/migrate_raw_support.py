#!/usr/bin/env python3
"""
Migration script to add RAW+JPEG pairing support to the database
Adds new fields to Image table for tracking RAW companion files
"""

import os
import sys
import sqlite3
from pathlib import Path

def migrate_raw_support():
    """Add RAW companion fields to Image table"""
    # Get database path (relative to where app runs)
    db_path = Path("src/imalink.db")
    
    if not db_path.exists():
        print("❌ Database not found. Please run the application first to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Adding RAW companion support to Image table...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(images)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ("raw_file_path", "TEXT"),
            ("raw_file_size", "INTEGER"),
            ("raw_file_format", "VARCHAR(10)")
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE images ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
                    print(f"ℹ️ Column {column_name} already exists")
            else:
                print(f"ℹ️ Column {column_name} already exists")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_images_raw_format ON images(raw_file_format)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("✅ Added performance indexes for RAW fields")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("\n🎉 RAW+JPEG pairing migration completed successfully!")
        print("\nNew capabilities:")
        print("   - JPEG files can now track companion RAW files")
        print("   - Import process prioritizes JPEG over RAW for thumbnails")
        print("   - RAW file information preserved for photographer workflow")
        print("   - Frontend can show RAW availability indicators")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📸 ImaLink RAW+JPEG Pairing Migration")
    print("=" * 50)
    
    if not migrate_raw_support():
        sys.exit(1)
    
    print("\n✨ Migration complete! You can now:")
    print("   1. Import directories with RAW+JPEG pairs")
    print("   2. See RAW availability in the gallery")
    print("   3. Benefit from optimized JPEG-based thumbnails")