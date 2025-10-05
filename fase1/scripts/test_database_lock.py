#!/usr/bin/env python3
"""
Test Database Lock Behavior

Test what happens when we try to delete the database while server is running.
"""
import os
import requests
from pathlib import Path
import time

def test_database_lock():
    """Test database locking behavior"""
    
    print("🧪 Database Lock Test")
    print("=" * 30)
    
    db_path = Path("/mnt/c/temp/00imalink_data/imalink.db")
    
    # Check server status
    try:
        health = requests.get("http://localhost:8000/health", timeout=2)
        if health.ok:
            print("✅ Server is running")
            server_running = True
        else:
            print("❌ Server responded with error")
            server_running = False
    except:
        print("❌ Server is not running")
        server_running = False
    
    if not server_running:
        print("💡 Start server to test lock behavior")
        return
    
    # Check if database exists
    if not db_path.exists():
        print("❌ Database file not found")
        return
    
    print(f"📁 Database: {db_path}")
    print(f"📊 Size: {db_path.stat().st_size} bytes")
    
    # Test read access
    print("\n🔍 Testing database access...")
    
    # Test if we can query via API
    try:
        stats = requests.get("http://localhost:8000/api/v1/debug/database-stats")
        if stats.ok:
            data = stats.json()
            print("✅ Database accessible via API")
            for table, count in data.get('table_counts', {}).items():
                print(f"   📋 {table}: {count} rows")
        else:
            print("❌ Cannot access database via API")
    except Exception as e:
        print(f"❌ API error: {e}")
    
    # Test direct file operations
    print("\n🧪 Testing file operations...")
    
    # Test rename (less destructive than delete)
    backup_path = db_path.with_suffix('.db.test_backup')
    
    try:
        # Try to copy the file
        import shutil
        shutil.copy2(db_path, backup_path)
        print("✅ Can copy database file")
        
        # Clean up
        if backup_path.exists():
            os.unlink(backup_path)
            print("✅ Can delete copy")
            
    except PermissionError:
        print("❌ Cannot copy - file is locked")
    except Exception as e:
        print(f"❌ Copy error: {e}")
    
    # Test if we can read file info
    try:
        stat = db_path.stat()
        print(f"✅ Can read file stats: {stat.st_size} bytes")
    except Exception as e:
        print(f"❌ Cannot read file stats: {e}")
    
    print("\n📋 Summary:")
    print("   • SQLite allows multiple readers")
    print("   • File deletion may fail if server has write lock")
    print("   • API reset is safer for running servers")
    print("   • Nuclear reset works best when server is stopped")

if __name__ == "__main__":
    test_database_lock()