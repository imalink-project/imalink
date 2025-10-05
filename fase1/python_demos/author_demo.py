#!/usr/bin/env python3
"""
ImaLink Author API Demo

Simple demo for all author CRUD operations.
"""

import requests
import sys
import json
from datetime import datetime


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def print_response(response, show_json=True):
    """Print response details"""
    if response.ok:
        print(f"✅ Success ({response.status_code})")
        if show_json:
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
            except:
                print(response.text)
    else:
        print(f"❌ Error ({response.status_code})")
        print(response.text)
    print()


def main():
    print("👤 ImaLink Author API Demo")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test connection first
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=3)
        if not health_response.ok:
            print("❌ Server health check failed!")
            return 1
        print("✅ Server is running")
    except:
        print("❌ Cannot connect to server!")
        print("Start server: cd fase1/src && uv run python main.py")
        return 1
    
    author_id = None
    
    try:
        # 1. List existing authors
        print_section("1. LIST AUTHORS")
        response = requests.get(f"{base_url}/authors/")
        print_response(response)
        
        if response.ok:
            response_data = response.json()
            authors = response_data.get('data', [])
            print(f"Found {len(authors)} existing authors")
        
        # 2. Create new author
        print_section("2. CREATE AUTHOR")
        timestamp = datetime.now().strftime("%H%M%S")
        new_author = {
            "name": f"Demo User {timestamp}",
            "email": f"demo{timestamp}@example.com",
            "bio": "Created by Python demo"
        }
        
        print("Creating author with data:")
        print(json.dumps(new_author, indent=2))
        print()
        
        response = requests.post(f"{base_url}/authors/", json=new_author)
        print_response(response)
        
        if response.ok:
            response_data = response.json()
            author_data = response_data.get('data', {})
            author_id = author_data.get('id')
            print(f"📝 Created author with ID: {author_id}")
        else:
            print("❌ Failed to create author, stopping demo")
            return 1
        
        # 3. Get author by ID
        print_section(f"3. GET AUTHOR BY ID ({author_id})")
        response = requests.get(f"{base_url}/authors/{author_id}")
        print_response(response)
        
        # 4. Update author
        print_section(f"4. UPDATE AUTHOR ({author_id})")
        update_data = {
            "bio": "Updated by Python demo! 🚀"
        }
        
        print("Updating with data:")
        print(json.dumps(update_data, indent=2))
        print()
        
        response = requests.put(f"{base_url}/authors/{author_id}", json=update_data)
        print_response(response)
        
        # 5. Verify update
        print_section(f"5. VERIFY UPDATE ({author_id})")
        response = requests.get(f"{base_url}/authors/{author_id}")
        print_response(response)
        
        # 6. Delete author
        print_section(f"6. DELETE AUTHOR ({author_id})")
        print(f"Deleting demo author {author_id}...")
        
        response = requests.delete(f"{base_url}/authors/{author_id}")
        print_response(response, show_json=False)
        
        # 7. Verify deletion
        print_section("7. VERIFY DELETION")
        response = requests.get(f"{base_url}/authors/{author_id}")
        if response.status_code == 404:
            print("✅ Author successfully deleted (404 Not Found)")
        else:
            print(f"❓ Unexpected response: {response.status_code}")
            print(response.text)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    print_section("🎉 DEMO COMPLETED")
    print("All author CRUD operations demonstrated successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())