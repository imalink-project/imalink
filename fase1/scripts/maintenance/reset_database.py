#!/usr/bin/env python3
"""
Complete database reset - removes ALL data and recreates fresh schema
"""

import os
import sys
from pathlib import Path
import sqlite3

def complete_database_reset():
    """Remove all database files and recreate fresh database"""
    
    # Find all possible database files
    db_dir = Path(__file__).parent / "src"
    
    # SQLite creates multiple files
    db_patterns = ["*.db", "*.db-shm", "*.db-wal", "*.db-journal"]
    
    removed_files = []
    
    print("🗑️ Removing ALL database files...")
    
    for pattern in db_patterns:
        for db_file in db_dir.glob(pattern):
            try:
                db_file.unlink()
                removed_files.append(str(db_file))
                print(f"   ❌ Deleted: {db_file.name}")
            except Exception as e:
                print(f"   ⚠️ Could not delete {db_file.name}: {e}")
    
    if not removed_files:
        print("   ℹ️ No database files found to delete")
    
    print(f"\n✅ Removed {len(removed_files)} database files")
    
    # Create completely fresh database
    print("🆕 Creating fresh database...")
    
    try:
        # Import and initialize fresh database
        sys.path.insert(0, str(db_dir))
        
        from database.connection import init_database
        from database.models import Base
        
        # This will create a completely new database
        init_database()
        
        print("✅ Fresh database created successfully")
        
        # Verify it's empty
        from database.connection import get_db_session
        from database.models import Image, Author, ImportSession
        
        with get_db_session() as db:
            image_count = db.query(Image).count()
            author_count = db.query(Author).count()
            session_count = db.query(ImportSession).count()
            
            print(f"📊 Database verification:")
            print(f"   Images: {image_count}")
            print(f"   Authors: {author_count}")
            print(f"   Import Sessions: {session_count}")
            
            if image_count == 0 and author_count == 0 and session_count == 0:
                print("✅ Database is completely empty - ready for fresh start!")
            else:
                print("⚠️ Database contains data - reset may not have worked")
        
    except Exception as e:
        print(f"❌ Error creating fresh database: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Complete Database Reset")
    print("=" * 50)
    print("⚠️ WARNING: This will delete ALL images, authors, and import sessions!")
    
    confirm = input("\n❓ Are you sure you want to continue? (type 'YES' to confirm): ")
    
    if confirm.strip().upper() != 'YES':
        print("❌ Operation cancelled")
        sys.exit(0)
    
    success = complete_database_reset()
    
    if success:
        print("\n🎉 Database reset completed successfully!")
        print("📱 Start the application now - it will be completely empty.")
    else:
        print("\n💥 Database reset failed. Check errors above.")
        sys.exit(1)