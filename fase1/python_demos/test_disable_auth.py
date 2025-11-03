#!/usr/bin/env python3
"""
Demonstration of DISABLE_AUTH feature for testing
This script shows how to access protected endpoints without authentication
"""
import os
import sys
import requests
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_with_auth_disabled():
    """Test API access with authentication disabled"""
    
    print("=" * 60)
    print("Testing API with DISABLE_AUTH=True")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test 1: Health check (public endpoint)
    print("\n1. Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Get photos (normally requires authentication)
    print("\n2. Testing photos endpoint (normally requires auth)...")
    try:
        response = requests.get(f"{base_url}/photos")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success! Got {len(data.get('photos', []))} photos")
            print(f"   Total: {data.get('total', 0)}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get current user profile
    print("\n3. Testing current user endpoint...")
    try:
        response = requests.get(f"{base_url}/auth/me")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"   Logged in as: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Full name: {user.get('full_name')}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Get users (admin-like endpoint)
    print("\n4. Testing users list endpoint...")
    try:
        response = requests.get(f"{base_url}/users")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"   Found {len(users)} users")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


def test_with_auth_enabled():
    """Test API access with authentication enabled (should fail without token)"""
    
    print("\n" + "=" * 60)
    print("Testing API with DISABLE_AUTH=False (normal mode)")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test: Get photos without token (should fail)
    print("\n1. Testing photos endpoint without authentication...")
    try:
        response = requests.get(f"{base_url}/photos")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print(f"   Expected: Authentication required")
            print(f"   Response: {response.json()}")
        else:
            print(f"   Unexpected status: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)


def main():
    # Check if DISABLE_AUTH is set
    disable_auth = os.getenv("DISABLE_AUTH", "False").lower() in ("true", "1", "yes")
    
    print("\nCurrent configuration:")
    print(f"  DISABLE_AUTH: {disable_auth}")
    print(f"  API should be running at: http://localhost:8000")
    
    if not disable_auth:
        print("\n⚠️  DISABLE_AUTH is not enabled!")
        print("   Set DISABLE_AUTH=True in .env or environment to test without authentication")
        print("\nTesting with authentication enabled (expecting 401 errors)...")
        test_with_auth_enabled()
    else:
        print("\n✓ DISABLE_AUTH is enabled")
        print("   Testing API access without authentication tokens...")
        test_with_auth_disabled()
    
    print("\nNote: Make sure the FastAPI server is running!")
    print("      export DISABLE_AUTH=True")
    print("      uv run src/main.py")


if __name__ == "__main__":
    main()
