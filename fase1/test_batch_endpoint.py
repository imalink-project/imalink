#!/usr/bin/env python3
"""
Quick test script for the new batch photo endpoint
"""
import requests
import json
import time
import sys

def test_batch_endpoint():
    """Test the new POST /api/v1/photos/batch endpoint"""
    
    # Wait for server to be ready
    print("🚀 Testing batch photo endpoint...")
    time.sleep(2)
    
    # Test with empty batch (should validate but not create anything)
    test_data = {
        "photo_groups": [],
        "author_id": None
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/photos/batch",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 422:
            # Validation error expected for empty list
            print("✅ Endpoint exists and validates input (empty list rejected as expected)")
            error_detail = response.json()
            print(f"Validation error: {error_detail}")
            return True
        elif response.status_code == 201:
            # Success response
            result = response.json()
            print("✅ Endpoint works! Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_batch_endpoint()
    sys.exit(0 if success else 1)