"""
Advanced import API tester - checks if background processing actually works
"""
import requests
import json
import time

# Test configuration
API_BASE = "http://localhost:8000/api/v1"
TEST_DIR = "C:\\temp\\PHOTOS_SRC_TEST_MICRO"

def test_full_import_cycle():
    """Test complete import cycle with proper monitoring"""
    
    print("=== Testing Full Import Cycle ===")
    
    # 1. Start import
    print(f"1. Starting import from: {TEST_DIR}")
    
    import_data = {
        "source_directory": TEST_DIR,
        "source_description": "Full cycle test"
    }
    
    try:
        response = requests.post(f"{API_BASE}/imports/", json=import_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Import start failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error: {response.text}")
            return False
        
        result = response.json()
        import_id = result.get('import_id')
        print(f"✅ Import started successfully! Session ID: {import_id}")
        
        # 2. Monitor progress
        print("\n2. Monitoring import progress...")
        
        max_checks = 30  # Maximum 30 checks (3 minutes at 6-second intervals)
        check_count = 0
        
        while check_count < max_checks:
            time.sleep(6)  # Wait 6 seconds between checks
            check_count += 1
            
            try:
                status_response = requests.get(f"{API_BASE}/imports/status/{import_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    print(f"Check #{check_count}:")
                    print(f"  Status: {status_data.get('status')}")
                    print(f"  Files found: {status_data.get('total_files_found', 0)}")
                    print(f"  Imported: {status_data.get('images_imported', 0)}")
                    print(f"  Duplicates: {status_data.get('duplicates_skipped', 0)}")
                    print(f"  Errors: {status_data.get('errors_count', 0)}")
                    print(f"  Progress: {status_data.get('progress_percentage', 0)}%")
                    
                    # Check if completed
                    status = status_data.get('status')
                    if status in ['completed', 'failed']:
                        print(f"\n🎯 Import {status}!")
                        return status == 'completed'
                        
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error checking status: {e}")
        
        print(f"\n⏰ Timeout after {max_checks} checks")
        return False
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_imports_list():
    """Test imports listing"""
    print("\n=== Testing imports List ===")
    
    try:
        response = requests.get(f"{API_BASE}/imports/imports")
        
        if response.status_code == 200:
            imports_data = response.json()
            print(f"✅ imports retrieved successfully")
            print(f"Response structure: {json.dumps(imports_data, indent=2)}")
            return True
        else:
            print(f"❌ imports list failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ imports test failed: {e}")
        return False

if __name__ == "__main__":
    print("Advanced Import API Test")
    print("=" * 50)
    
    # Test imports first
    imports_success = test_imports_list()
    
    # Test full import cycle
    import_success = test_full_import_cycle()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(f"imports API: {'✅ PASS' if imports_success else '❌ FAIL'}")
    print(f"Import Cycle: {'✅ PASS' if import_success else '❌ FAIL'}")
    
    if import_success:
        print("\n🎉 All tests passed! Import functionality is working.")
    else:
        print("\n🔍 Import functionality needs investigation.")
