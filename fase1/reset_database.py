#!/usr/bin/env python3
"""
Script to safely delete and recreate the database
"""
import os
import sys
import sqlite3
from pathlib import Path

def delete_database():
    """Delete the database file safely"""
    
    # Add the src directory to Python path
    src_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        # Import config to get database path
        from core.config import config
        
        db_path = Path(config.database_path)
        
        if db_path.exists():
            print(f"🗑️ Deleting database: {db_path}")
            
            # Ensure all connections are closed
            try:
                # Try to connect and close immediately to release any locks
                conn = sqlite3.connect(str(db_path))
                conn.close()
            except:
                pass
            
            # Delete the file
            os.unlink(db_path)
            print("✅ Database deleted successfully!")
            
            # Recreate empty database
            print("🔄 Creating new empty database...")
            from database.connection import init_database
            init_database()
            print("✅ New database created!")
            
        else:
            print("ℹ️ Database file does not exist")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Try running as administrator or manually delete: {config.database_path}")

if __name__ == "__main__":
    delete_database()