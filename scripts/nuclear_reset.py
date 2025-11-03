#!/usr/bin/env python3
"""
Nuclear Reset - Delete and Recreate Database

Simple script that deletes the database file and recreates it.
No migrations, no complications - just fresh start.
"""
import os
import sys
from pathlib import Path

def nuclear_reset():
    """Delete database and recreate - nuclear option for development"""
    
    print("💥 Nuclear Database Reset")
    print("=" * 40)
    print("⚠️  WARNING: This deletes ALL data!")
    print("⚠️  Creates fresh database from current models")
    print("⚠️  NO migrations - direct schema creation")
    
    # Default database path
    db_path = Path("/mnt/c/temp/00imalink_data/imalink.db")
    
    print(f"\n🎯 Target: {db_path}")
    
    # Check if server is running
    server_running = False
    try:
        import requests
        health = requests.get("http://localhost:8000/health", timeout=2)
        if health.ok:
            server_running = True
            print("⚠️  Server is currently RUNNING!")
            print("   This may cause SQLite lock issues")
    except:
        print("ℹ️  Server appears to be stopped")
    
    confirm = input("Type 'DELETE' to confirm: ").strip()
    if confirm != "DELETE":
        print("❌ Cancelled")
        return False
    
    try:
        # Step 1: Try to delete database file
        if db_path.exists():
            print("🗑️  Deleting database file...")
            
            # If server is running, warn about potential issues
            if server_running:
                print("⚠️  Attempting deletion while server is running...")
                try:
                    os.unlink(db_path)
                    print("✅ Database deleted successfully!")
                except PermissionError:
                    print("❌ Cannot delete - file is locked by running server")
                    print("💡 Solutions:")
                    print("   1. Stop server first, then run nuclear reset")
                    print("   2. Use API reset: uv run python scripts/api_fresh_start.py")
                    return False
                except Exception as e:
                    print(f"❌ Deletion failed: {e}")
                    return False
            else:
                os.unlink(db_path)
                print("✅ Database deleted")
        else:
            print("ℹ️  No database file found")
        
        # Step 2: Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Step 3: Next steps depend on server status
        print("\n🔄 Fresh database ready!")
        print("\n📋 Next steps:")
        
        if server_running:
            print("   🔄 Server is still running with old database connection")
            print("   ⚠️  You MUST restart the server to use fresh database:")
            print("      1. Stop server (Ctrl+C)")
            print("      2. Start server: cd fase1/src && uv run python main.py")
            print("      3. Server will auto-create tables from current models")
            print("   Or use API reset instead for seamless reset")
        else:
            print("   1. Start server: cd fase1/src && uv run python main.py")
            print("   2. Server will auto-create tables from current models")
        
        print("   3. Use demos to test: uv run python python_demos/health_demo.py")
        
        print("\n🎉 Nuclear reset complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = nuclear_reset()
    sys.exit(0 if success else 1)