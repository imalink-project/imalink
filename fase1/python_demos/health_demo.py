#!/usr/bin/env python3
"""
ImaLink Health Check Demo

Simple demo to verify that the FastAPI server is running and responding.
"""

import requests
import sys
from datetime import datetime


def main():
    print("🏥 ImaLink Health Check Demo")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Time: {timestamp}")
    print(f"Testing: {base_url}")
    print()
    
    try:
        # Test health endpoint
        print("Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        
        if response.ok:
            print("✅ Server is running!")
            print(f"   Status Code: {response.status_code}")
            
            # Try to get JSON response
            try:
                health_data = response.json()
                print(f"   Response: {health_data}")
            except:
                print(f"   Response: {response.text}")
        else:
            print(f"❌ Server responded with error: {response.status_code}")
            print(f"   Response: {response.text}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Make sure FastAPI server is running:")
        print("   cd fase1/src && uv run python main.py")
        return 1
        
    except requests.exceptions.Timeout:
        print("❌ Server timeout!")
        print("   Server is too slow to respond")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    print()
    print("🎉 Health check demo completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())