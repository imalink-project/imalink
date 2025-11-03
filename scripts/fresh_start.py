#!/usr/bin/env python3
"""
Quick Fresh Start Command

Super simple command to wipe everything and start fresh.
Run this when you want to start completely over.
"""
import os
import sys
from pathlib import Path

def quick_fresh_start():
    """Nuclear option - delete everything and start fresh"""
    
    print("💥 ImaLink Fresh Start")
    print("=" * 30)
    print("This will DELETE EVERYTHING!")
    
    # Simple confirmation
    confirm = input("Type 'YES' to continue: ").strip().upper()
    if confirm != "YES":
        print("Cancelled.")
        return
    
    # Get database path from config
    src_dir = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        from core.config import Config
        db_path = Path(Config.DATABASE_URL.replace("sqlite:///", ""))
        
        print(f"🗑️  Deleting: {db_path}")
        
        # Delete database file
        if db_path.exists():
            os.unlink(db_path)
            print("✅ Database deleted")
        
        # Recreate
        print("🔄 Creating fresh database...")
        from database.connection import init_database
        init_database()
        print("✅ Fresh database ready!")
        
        print("\n🎉 Fresh start complete!")
        print("   Start server: cd src && uv run python main.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_fresh_start()