"""
Test script for import API - run this while server is running from another shell
"""
import requests
import json
import time

# Test data
TEST_DATA = {
    "source_directory": "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO",
    "source_description": "Test import from script"
}

def test_import_api():
    """Test the import API endpoint"""
    try:
        print("Testing import API...")
        print(f"Payload: {json.dumps(TEST_DATA, indent=2)}")
        
        # Test the import endpoint
        response = requests.post(
            "http://localhost:8000/api/v1/import_sessions/",
            json=TEST_DATA,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS! Response: {json.dumps(result, indent=2)}")
            
            # If we got a session_id, test status endpoint
            if 'session_id' in result:
                session_id = result['session_id']
                print(f"\nTesting status endpoint for session {session_id}...")
                
                time.sleep(1)  # Wait a bit
                
                status_response = requests.get(
                    f"http://localhost:8000/api/v1/import_sessions/status/{session_id}"
                )
                
                print(f"Status endpoint response: {status_response.status_code}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Status data: {json.dumps(status_data, indent=2)}")
                
        else:
            print(f"ERROR! Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Make sure server is running on localhost:8000")
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_import_api()