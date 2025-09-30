#!/usr/bin/env python3
"""
Migration script to remove redundant has_raw_companion field
The has_raw_companion field is redundant since it can be computed as (raw_file_path IS NOT NULL)
"""

import os
import sys
import sqlite3
from pathlib import Path

def cleanup_redundant_field():
    """Remove redundant has_raw_companion field from Image table"""
    # Get database path
    db_path = Path("src/imalink.db")
    
    if not db_path.exists():
        print("❌ Database not found. Please run the application first to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Cleaning up redundant has_raw_companion field...")
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "has_raw_companion" in columns:
            print("📊 Analyzing field redundancy...")
            
            # Check data consistency before removal
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN has_raw_companion = 1 AND raw_file_path IS NOT NULL THEN 1 ELSE 0 END) as consistent_true,
                    SUM(CASE WHEN has_raw_companion = 0 AND raw_file_path IS NULL THEN 1 ELSE 0 END) as consistent_false,
                    SUM(CASE WHEN (has_raw_companion = 1) != (raw_file_path IS NOT NULL) THEN 1 ELSE 0 END) as inconsistent
                FROM images
            """)
            
            stats = cursor.fetchone()
            total, consistent_true, consistent_false, inconsistent = stats
            
            print(f"   Total records: {total}")
            print(f"   Consistent (TRUE): {consistent_true}")  
            print(f"   Consistent (FALSE): {consistent_false}")
            print(f"   Inconsistent: {inconsistent}")
            
            if inconsistent > 0:
                print(f"⚠️  Found {inconsistent} inconsistent records - fixing...")
                # Fix inconsistent data before dropping column
                cursor.execute("""
                    UPDATE images 
                    SET has_raw_companion = (raw_file_path IS NOT NULL)
                    WHERE (has_raw_companion = 1) != (raw_file_path IS NOT NULL)
                """)
                print(f"✅ Fixed {cursor.rowcount} inconsistent records")
            
            # Drop the redundant column
            # SQLite doesn't support DROP COLUMN directly, so we recreate the table
            print("🔧 Removing redundant column...")
            
            # Create new table without has_raw_companion
            cursor.execute("""
                CREATE TABLE images_new (
                    id INTEGER PRIMARY KEY,
                    image_hash VARCHAR(64) UNIQUE NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    file_format VARCHAR(10),
                    raw_file_path TEXT,
                    raw_file_size INTEGER,
                    raw_file_format VARCHAR(10),
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
            
            # Copy data (excluding has_raw_companion)
            cursor.execute("""
                INSERT INTO images_new SELECT
                    id, image_hash, original_filename, file_path, file_size, file_format,
                    raw_file_path, raw_file_size, raw_file_format,
                    created_at, taken_at, width, height, thumbnail, exif_data,
                    gps_latitude, gps_longitude, title, description, tags, rating,
                    user_rotation, author_id, import_source
                FROM images
            """)
            
            # Replace old table
            cursor.execute("DROP TABLE images")
            cursor.execute("ALTER TABLE images_new RENAME TO images")
            
            # Recreate indexes
            indexes = [
                "CREATE UNIQUE INDEX idx_images_hash ON images(image_hash)",
                "CREATE INDEX idx_images_taken_at ON images(taken_at)",
                "CREATE INDEX idx_images_author_id ON images(author_id)",
                "CREATE INDEX idx_images_raw_format ON images(raw_file_format)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            print("✅ Successfully removed redundant has_raw_companion field")
            
        else:
            print("ℹ️ has_raw_companion field not found - already clean!")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("\n🎉 Database cleanup completed successfully!")
        print("\nBenefits:")
        print("   - Eliminated redundant data storage")
        print("   - Reduced database size")
        print("   - Simplified logic: use (raw_file_path IS NOT NULL)")
        print("   - Better database normalization")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧹 ImaLink Database Cleanup - Remove Redundant Field")
    print("=" * 60)
    
    if not cleanup_redundant_field():
        sys.exit(1)
    
    print("\n✨ Cleanup complete! The API now computes has_raw_companion dynamically.")