#!/usr/bin/env python3
"""
Fresh Database Reset Script

Completely deletes the database file and recreates it from scratch with current model definitions.
Perfect for experimentation when you don't want to deal with migrations.
"""
import os
import sys
import sqlite3
from pathlib import Path
import shutil

def fresh_database_reset():
    """Delete database file and recreate from current models - NO MIGRATIONS!"""
    
    print("🔄 ImaLink Fresh Database Reset")
    print("=" * 50)
    print("⚠️  This will PERMANENTLY DELETE all data!")
    print("⚠️  This creates a fresh database from current models")
    print("⚠️  NO migration - direct schema creation")
    
    # Ask for confirmation
    confirm = input("\n❓ Type 'FRESH_START' to confirm: ").strip()
    if confirm != "FRESH_START":
        print("❌ Reset cancelled")
        return False
    
    # Add the src directory to Python path for imports
    src_dir = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        # Import config to get database path
        from core.config import Config
        
        db_path = Path(Config.DATABASE_URL.replace("sqlite:///", ""))
        data_dir = db_path.parent
        
        print(f"\n🎯 Target database: {db_path}")
        print(f"📁 Data directory: {data_dir}")
        
        # Step 1: Stop any existing connections
        print("\n1️⃣ Closing existing connections...")
        try:
            # Force close any SQLite connections
            conn = sqlite3.connect(str(db_path))
            conn.close()
        except:
            pass
        
        # Step 2: Backup if exists (optional safety)
        if db_path.exists():
            backup_path = db_path.with_suffix('.db.backup')
            print(f"2️⃣ Creating backup: {backup_path}")
            shutil.copy2(db_path, backup_path)
            print(f"   ✅ Backup created (remove manually if not needed)")
        
        # Step 3: Delete database file
        if db_path.exists():
            print("3️⃣ Deleting database file...")
            os.unlink(db_path)
            print("   ✅ Database file deleted")
        else:
            print("3️⃣ No existing database file found")
        
        # Step 4: Ensure data directory exists
        print("4️⃣ Ensuring data directory exists...")
        data_dir.mkdir(parents=True, exist_ok=True)
        print("   ✅ Data directory ready")
        
        # Step 5: Create fresh database with current models
        print("5️⃣ Creating fresh database from current models...")
        from database.connection import init_database
        init_database()
        print("   ✅ Fresh database created!")
        
        # Step 6: Verify creation
        print("6️⃣ Verifying database...")
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            print(f"   ✅ Database verified! Found {len(tables)} tables:")
            for table in tables:
                print(f"      • {table[0]}")
        else:
            print("   ❌ Database verification failed!")
            return False
        
        print("\n🎉 Fresh database reset completed successfully!")
        print("   💡 All data has been wiped - fresh start ready!")
        print("   💡 Models reflect current code definitions")
        return True
            
    except Exception as e:
        print(f"\n❌ Error during reset: {e}")
        print("💡 Check that no applications are using the database")
        print("💡 Try stopping the FastAPI server and try again")
        return False

if __name__ == "__main__":
    success = fresh_database_reset()
    sys.exit(0 if success else 1)