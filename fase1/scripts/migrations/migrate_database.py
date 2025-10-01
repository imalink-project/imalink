#!/usr/bin/env python3
"""
Database migration: Add user_rotation field to existing images
Run this once to update the database schema
"""

import os
import sys
import sqlite3
from pathlib import Path

def add_user_rotation_field():
    """Add user_rotation field to existing images table"""
    
    # Find the database file
    db_path = Path(__file__).parent / "src" / "imalink.db"
    
    if not db_path.exists():
        print("❌ Database file not found. Run the application first to create it.")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if user_rotation field already exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_rotation' in columns:
            print("✅ user_rotation field already exists in database")
            return True
        
        # Add the new field
        print("🔧 Adding user_rotation field to images table...")
        cursor.execute("ALTER TABLE images ADD COLUMN user_rotation INTEGER DEFAULT 0 NOT NULL")
        
        # Update all existing images to have user_rotation = 0
        cursor.execute("UPDATE images SET user_rotation = 0 WHERE user_rotation IS NULL")
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added user_rotation field to all images")
        return True
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running database migration for user_rotation field...")
    success = add_user_rotation_field()
    
    if success:
        print("🎉 Migration completed successfully!")
        print("📝 You can now start the application with rotation support.")
    else:
        print("💥 Migration failed. Check the error messages above.")
        sys.exit(1)