#!/usr/bin/env python3
"""
Migration script to add raw_files_skipped field to ImportSession table
This improves import statistics by separating RAW files from true duplicates
"""

import os
import sys
import sqlite3
from pathlib import Path

def add_raw_files_skipped_field():
    """Add raw_files_skipped field to ImportSession table"""
    # Get database path
    db_path = Path("src/imalink.db")
    
    if not db_path.exists():
        print("❌ Database not found. Please run the application first to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Adding raw_files_skipped field to ImportSession table...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(import_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "raw_files_skipped" not in columns:
            cursor.execute("ALTER TABLE import_sessions ADD COLUMN raw_files_skipped INTEGER DEFAULT 0")
            print("✅ Added raw_files_skipped column")
        else:
            print("ℹ️ raw_files_skipped column already exists")
        
        # Create index for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_sessions_raw_files ON import_sessions(raw_files_skipped)")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("\n🎉 Import statistics migration completed successfully!")
        print("\nImproved import reporting:")
        print("   ✅ Bildefiler funnet: total_files_found")
        print("   ✅ Bilder importert: images_imported")
        print("   ✅ Duplikater hoppet over: duplicates_skipped (actual duplicates)")
        print("   ✅ Råbilder funnet: raw_files_skipped (RAW with JPEG companions)")
        print("   ✅ Feil: errors_count")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📊 ImaLink Import Statistics Improvement")
    print("=" * 50)
    
    if not add_raw_files_skipped_field():
        sys.exit(1)
    
    print("\n✨ Migration complete! Import statistics now properly categorize files.")