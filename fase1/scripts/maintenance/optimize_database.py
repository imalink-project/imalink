#!/usr/bin/env python3
"""
Final cleanup script to remove ALL RAW-related fields from database
RAW companion info will be computed dynamically from filesystem when needed
This achieves perfect database normalization with no redundant data
"""

import os
import sys
import sqlite3
from pathlib import Path

def remove_all_raw_fields():
    """Remove all RAW-related fields from Image table"""
    # Get database path
    db_path = Path("src/imalink.db")
    
    if not db_path.exists():
        print("❌ Database not found. Please run the application first to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Removing all RAW-related fields from database...")
        
        # Check current schema
        cursor.execute("PRAGMA table_info(images)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        raw_fields = ['has_raw_companion', 'raw_file_path', 'raw_file_size', 'raw_file_format']
        existing_raw_fields = [field for field in raw_fields if field in columns]
        
        if not existing_raw_fields:
            print("ℹ️ No RAW fields found - database already optimized!")
            return True
        
        print(f"📊 Found RAW fields to remove: {', '.join(existing_raw_fields)}")
        
        # Count records with RAW companions before removal
        if 'raw_file_path' in columns:
            cursor.execute("SELECT COUNT(*) FROM images WHERE raw_file_path IS NOT NULL")
            raw_count = cursor.fetchone()[0]
            print(f"   Records with RAW companions: {raw_count}")
        
        # Create new table without any RAW fields
        print("🔧 Creating optimized table schema...")
        cursor.execute("""
            CREATE TABLE images_new (
                id INTEGER PRIMARY KEY,
                image_hash VARCHAR(64) UNIQUE NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_format VARCHAR(10),
                created_at DATETIME,
                taken_at DATETIME,
                width INTEGER,
                height INTEGER,
                thumbnail BLOB,
                exif_data BLOB,
                gps_latitude REAL,
                gps_longitude REAL,
                title VARCHAR(255),
                description TEXT,
                tags TEXT,
                rating INTEGER,
                user_rotation INTEGER DEFAULT 0 NOT NULL,
                author_id INTEGER,
                import_source VARCHAR(255),
                FOREIGN KEY (author_id) REFERENCES authors (id)
            )
        """)
        
        # Copy data (excluding all RAW fields)
        cursor.execute("""
            INSERT INTO images_new SELECT
                id, image_hash, original_filename, file_path, file_size, file_format,
                created_at, taken_at, width, height, thumbnail, exif_data,
                gps_latitude, gps_longitude, title, description, tags, rating,
                user_rotation, author_id, import_source
            FROM images
        """)
        
        # Replace old table
        cursor.execute("DROP TABLE images")
        cursor.execute("ALTER TABLE images_new RENAME TO images")
        
        # Recreate essential indexes only
        indexes = [
            "CREATE UNIQUE INDEX idx_images_hash ON images(image_hash)",
            "CREATE INDEX idx_images_taken_at ON images(taken_at)",
            "CREATE INDEX idx_images_author_id ON images(author_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("✅ Successfully removed all RAW fields from database")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("\n🎉 Database optimization completed successfully!")
        print("\nBenefits achieved:")
        print("   ✅ Perfect normalization - no redundant filesystem data")
        print("   ✅ Always current - RAW info computed from actual files")
        print("   ✅ Smaller database - eliminated 3-4 fields per image")
        print("   ✅ No sync issues - database never out-of-sync with filesystem")
        print("   ✅ Simpler migrations - no RAW metadata to maintain")
        print("\nRAW companion detection:")
        print("   🔍 Computed dynamically when API called")
        print("   📁 Uses ImageProcessor.find_raw_companion(jpeg_path)")
        print("   🚀 Fast filesystem lookup by filename matching")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 ImaLink Database Optimization - Remove RAW Fields")
    print("=" * 60)
    print("This will remove all RAW-related database fields.")
    print("RAW companion info will be computed dynamically when needed.")
    print()
    
    if not remove_all_raw_fields():
        sys.exit(1)
    
    print("\n✨ Optimization complete! Database is now perfectly normalized.")
    print("   RAW companions detected dynamically from filesystem.")