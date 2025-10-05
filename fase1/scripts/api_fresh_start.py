#!/usr/bin/env python3
"""
API Fresh Start - Use Debug API to Reset Database

Uses the existing debug API endpoint to reset the database.
Requires the server to be running.
"""
import requests
import sys

def api_fresh_start():
    """Use debug API to reset database"""
    
    print("🌐 API Fresh Start")
    print("=" * 30)
    print("Uses debug API to reset database")
    print("⚠️  Server must be running!")
    
    base_url = "http://localhost:8000"
    
    # Check server
    try:
        health = requests.get(f"{base_url}/health", timeout=3)
        if not health.ok:
            print("❌ Server not responding properly")
            return False
        print("✅ Server is running")
    except:
        print("❌ Server not running!")
        print("   Start server: cd fase1/src && uv run python main.py")
        return False
    
    # Confirm action
    print(f"\n🎯 Will reset database via: {base_url}/api/v1/debug/reset-database")
    confirm = input("Type 'RESET' to confirm: ").strip()
    if confirm != "RESET":
        print("❌ Cancelled")
        return False
    
    try:
        # Call reset API
        print("🔄 Calling reset API...")
        response = requests.post(
            f"{base_url}/api/v1/debug/reset-database",
            params={"confirm": "DELETE_EVERYTHING"}
        )
        
        if response.ok:
            print("✅ Database reset successful!")
            result = response.json()
            print(f"   Message: {result.get('message', 'Reset completed')}")
            
            # Test the fresh database
            print("\n🧪 Testing fresh database...")
            stats = requests.get(f"{base_url}/api/v1/debug/database-stats")
            if stats.ok:
                data = stats.json()
                print("✅ Fresh database verified:")
                for table, count in data.get('table_counts', {}).items():
                    print(f"   📊 {table}: {count} rows")
            
            print("\n🎉 API fresh start complete!")
            print("   Database is fresh and ready!")
            return True
            
        else:
            print(f"❌ Reset failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = api_fresh_start()
    sys.exit(0 if success else 1)