#!/usr/bin/env python3
"""
Database migration: Add Author table and foreign keys
Run this once to update the database schema for Author support
"""

import os
import sys
import sqlite3
from pathlib import Path

def add_author_tables():
    """Add Author table and update Image/ImportSession tables"""
    
    # Find the database file
    db_path = Path(__file__).parent / "src" / "imalink.db"
    
    if not db_path.exists():
        print("❌ Database file not found. Run the application first to create it.")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🔧 Adding Author support to database...")
        
        # 1. Create authors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                created_at DATETIME,
                CONSTRAINT authors_name_unique UNIQUE (name)
            )
        """)
        
        # 2. Add author_id to images table (if not exists)
        try:
            cursor.execute("ALTER TABLE images ADD COLUMN author_id INTEGER")
            print("✅ Added author_id to images table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️ author_id column already exists in images table")
            else:
                raise
        
        # 3. Add default_author_id to import_sessions table (if not exists)
        try:
            cursor.execute("ALTER TABLE import_sessions ADD COLUMN default_author_id INTEGER")
            print("✅ Added default_author_id to import_sessions table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️ default_author_id column already exists in import_sessions table")
            else:
                raise
        
        # 4. Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_author_id ON images(author_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_sessions_author_id ON import_sessions(default_author_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name)")
        
        # 5. Create a default "Unknown" author if no authors exist
        cursor.execute("SELECT COUNT(*) FROM authors")
        author_count = cursor.fetchone()[0]
        
        if author_count == 0:
            cursor.execute("""
                INSERT INTO authors (name, created_at) 
                VALUES ('Unknown', datetime('now'))
            """)
            print("✅ Created default 'Unknown' author")
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added Author support to database")
        print("\n📝 New features available:")
        print("   - Authors can be managed via /api/authors")
        print("   - Images can be assigned to authors")
        print("   - Import sessions can have default authors")
        print("   - Author information preserved during imports")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running Author database migration...")
    success = add_author_tables()
    
    if success:
        print("🎉 Migration completed successfully!")
        print("📱 Restart the application to use Author features.")
    else:
        print("💥 Migration failed. Check the error messages above.")
        sys.exit(1)