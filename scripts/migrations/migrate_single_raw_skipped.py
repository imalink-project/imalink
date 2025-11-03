#!/usr/bin/env python3
"""
Migration script to add single_raw_skipped field to ImportSession table.

This migration adds tracking for single RAW files (RAW files without JPEG companions)
to distinguish them from RAW files that are part of RAW+JPEG pairs.
"""

import sqlite3
import os

def migrate_single_raw_skipped():
    """Add single_raw_skipped column to ImportSession table."""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), "src", "imalink.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(import_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'single_raw_skipped' in columns:
            print("Column 'single_raw_skipped' already exists in import_sessions table.")
            return True
        
        # Add the new column with default value 0
        cursor.execute("ALTER TABLE import_sessions ADD COLUMN single_raw_skipped INTEGER DEFAULT 0")
        
        # Update existing records to have 0 as default value
        cursor.execute("UPDATE import_sessions SET single_raw_skipped = 0 WHERE single_raw_skipped IS NULL")
        
        # Commit changes
        conn.commit()
        
        print("Successfully added 'single_raw_skipped' column to import_sessions table.")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = migrate_single_raw_skipped()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")