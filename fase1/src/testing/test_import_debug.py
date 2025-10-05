"""
Debug import with file logging
"""
import requests
import json
import time
from datetime import datetime

def test_import_with_logging():
    """Test import and log everything to file"""
    
    API_BASE = "http://localhost:8000/api/v1"
    TEST_DIR = "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO"
    
    # Create log file
    log_file = f"import_debug_{datetime.now().strftime('%H%M%S')}.txt"
    
    def log(message):
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
        print(message)
    
    log(f"=== Import Debug Test - Log file: {log_file} ===")
    
    # Start import
    import_data = {
        "source_path": TEST_DIR,
        "source_description": "Debug test with logging"
    }
    
    log(f"Starting import from: {TEST_DIR}")
    
    try:
        response = requests.post(f"{API_BASE}/imports/", json=import_data)
        
        if response.status_code != 200:
            log(f"❌ Failed to start import: {response.status_code}")
            log(f"Response: {response.text}")
            return
        
        result = response.json()
        session_id = result.get('session_id')
        log(f"✅ Import started, session ID: {session_id}")
        
        # Monitor for longer time
        for i in range(10):  # Check 10 times
            time.sleep(2)  # Wait 2 seconds
            
            try:
                status_response = requests.get(f"{API_BASE}/imports/status/{session_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    log(f"Check #{i+1}: Status={status.get('status')}, "
                        f"Files={status.get('total_files_found', 0)}, "
                        f"Imported={status.get('images_imported', 0)}, "
                        f"Errors={status.get('errors_count', 0)}")
                    
                    if status.get('status') in ['completed', 'failed']:
                        log(f"🎯 Import {status.get('status')}!")
                        break
                else:
                    log(f"❌ Status check failed: {status_response.status_code}")
                    
            except Exception as e:
                log(f"❌ Error checking status: {e}")
        
        # Final check - list all images
        try:
            images_response = requests.get(f"{API_BASE}/images/")
            if images_response.status_code == 200:
                images_data = images_response.json()
                image_count = len(images_data.get('data', []))
                log(f"📊 Total images in database: {image_count}")
            else:
                log(f"❌ Could not get images list: {images_response.status_code}")
        except Exception as e:
            log(f"❌ Error getting images: {e}")
        
    except Exception as e:
        log(f"❌ Test failed: {e}")
    
    log(f"=== Test completed - Check {log_file} for full log ===")

if __name__ == "__main__":
    test_import_with_logging()