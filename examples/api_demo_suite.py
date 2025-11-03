#!/usr/bin/env python3
"""
ImaLink API Demo Suite

Complete demo of all major AP    record_result(demo_endpoint("GET", f"{api_url}/authors/", description="List all authors"))
    
    # Create author
    timestamp = datetime.now().strftime("%H%M%S")
    
    create_success = demo_endpoint("POST", f"{api_url}/authors/", data=demo_author,.
"""

import requests
import sys
import json
from datetime import datetime


def print_header(title):
    print(f"\n{'🚀 ' + title + ' 🚀':=^60}")


def demo_endpoint(method, url, data=None, expected_status=200, description=""):
    """Demo a single endpoint and return result"""
    try:
        response = requests.request(method, url, json=data, timeout=10)
        
        status_icon = "✅" if response.status_code == expected_status else "❌"
        print(f"{status_icon} {method} {url}")
        
        if description:
            print(f"   {description}")
        
        print(f"   Status: {response.status_code} (expected: {expected_status})")
        
        if response.ok or response.status_code == expected_status:
            try:
                json_data = response.json()
                if isinstance(json_data, dict) and len(str(json_data)) < 200:
                    print(f"   Response: {json_data}")
                else:
                    print(f"   Response: [JSON data, {len(str(json_data))} chars]")
            except:
                if len(response.text) < 100:
                    print(f"   Response: {response.text}")
                else:
                    print(f"   Response: [Text data, {len(response.text)} chars]")
        else:
            print(f"   Error: {response.text}")
        
        print()
        return response.ok or response.status_code == expected_status
        
    except Exception as e:
        print(f"❌ {method} {url}")
        print(f"   Error: {e}")
        print()
        return False


def main():
    print("🧪 ImaLink API Demo Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    api_url = f"{base_url}/api/v1"
    
    passed = 0
    failed = 0
    
    def record_result(success):
        nonlocal passed, failed
        if success:
            passed += 1
        else:
            failed += 1
    
    # Health check first
    print_header("HEALTH CHECK")
    record_result(demo_endpoint("GET", f"{base_url}/health", description="Server health status"))
    
    # Authors API
    print_header("AUTHORS API")
    
    # List authors
    record_result(demo_endpoint("GET", f"{api_url}/authors/", description="List all authors"))
    
    # Create author
    timestamp = datetime.now().strftime("%H%M%S")
    demo_author = {
        "name": f"API Demo {timestamp}",
        "email": f"apidemo{timestamp}@example.com",
        "bio": "Created by API demo suite"
    }
    
    create_success = demo_endpoint("POST", f"{api_url}/authors/", data=demo_author, 
                                   expected_status=200, description="Create new author")
    record_result(create_success)
    
    # If creation successful, get the author ID and test other operations
    author_id = None
    if create_success:
        try:
            # Get the created author ID (would need to implement proper ID tracking)
            # For now, we'll just test with a placeholder
            author_id = 999  # This would normally come from the create response
        except:
            pass
    
    # Images API (if implemented)
    print_header("IMAGES API")
    record_result(demo_endpoint("GET", f"{api_url}/images/", description="List all images"))
    
    # Import Sessions API (if implemented)
    print_header("IMPORT SESSIONS API")
    record_result(demo_endpoint("GET", f"{api_url}/import-sessions/", expected_status=404, description="List import sessions (not implemented)"))
    
    # Debug API (development only)
    print_header("DEBUG API (DEV ONLY)")
    record_result(demo_endpoint("GET", f"{api_url}/debug/stats", expected_status=404, description="Database statistics (not implemented)"))
    
    # Summary
    print_header("DEMO SUMMARY")
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total demos: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if failed == 0:
        print("\n🎉 All demos passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} demo(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())