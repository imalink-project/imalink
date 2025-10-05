"""
Quick import test - just check if background task processes images
"""
import requests
import json
import time

def quick_import_test():
    """Quick test to see if background processing works"""
    
    API_BASE = "http://localhost:8000/api/v1"
    TEST_DIR = "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO"
    
    print("🚀 Quick Import Test")
    
    # Start import
    import_data = {
        "source_path": TEST_DIR,
        "source_description": "Quick test"
    }
    
    response = requests.post(f"{API_BASE}/imports/", json=import_data)
    
    if response.status_code != 200:
        print(f"❌ Failed to start import: {response.status_code}")
        return
    
    result = response.json()
    import_id = result.get('import_id')
    print(f"✅ Import started, session ID: {import_id}")
    
    # Check status 3 times with short intervals
    for i in range(3):
        time.sleep(3)  # Wait 3 seconds
        
        status_response = requests.get(f"{API_BASE}/imports/status/{import_id}")
        if status_response.status_code == 200:
            status = status_response.json()
            
            print(f"\nCheck #{i+1}:")
            print(f"  Status: {status.get('status')}")
            print(f"  Files found: {status.get('total_files_found', 0)}")
            print(f"  Images imported: {status.get('images_imported', 0)}")
            print(f"  Duplicates skipped: {status.get('duplicates_skipped', 0)}")
            print(f"  Errors: {status.get('errors_count', 0)}")
            
            if status.get('status') in ['completed', 'failed']:
                print(f"🎯 Import {status.get('status')}!")
                break
    
    print("\n✅ Quick test completed")

if __name__ == "__main__":
    quick_import_test()
