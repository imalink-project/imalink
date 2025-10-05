#!/usr/bin/env python3
"""
ImaLink Import Session Demo

Demonstrates the complete import workflow:
1. Start full directory import
2. Monitor import progress
3. View import results

Uses configured test directories:
- Source: /mnt/c/temp/PHOTOS_SRC_TEST_MICRO
- Storage: /mnt/c/temp/storage
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path


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
                return data
            except:
                print(response.text)
                return response.text
    else:
        print(f"❌ Error ({response.status_code})")
        print(response.text)
        return None
    print()


def wait_for_import_completion(base_url, import_id, max_wait_seconds=30):
    """Monitor import progress until completion"""
    print(f"\n⏳ Monitoring import {import_id}...")
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < max_wait_seconds:
        try:
            check_count += 1
            status_response = requests.get(f"{base_url}/import_sessions/status/{import_id}")
            if status_response.ok:
                status_data = status_response.json()
                status = status_data.get("status", "unknown")
                
                print(f"Check #{check_count}: {status}")
                
                if status in ["completed", "failed", "cancelled"]:
                    print(f"\n🏁 Import finished with status: {status}")
                    print_response(status_response)
                    return status_data
                    
                # Show progress if available
                if "stats" in status_data:
                    stats = status_data["stats"]
                    total = stats.get("total_files", 0)
                    processed = stats.get("files_processed", 0)
                    if total > 0:
                        progress = (processed / total) * 100
                        print(f"   Progress: {processed}/{total} files ({progress:.1f}%)")
                
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            break
    
    print(f"\n⚠️  Timeout after {max_wait_seconds} seconds ({check_count} checks)")
    print("Import might still be running in background. Check manually with:")
    print(f"   GET /api/v1/import_sessions/status/{import_id}")
    return None


def main():
    print("📥 ImaLink Import Session Demo")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test connection first
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=3)
        if not health_response.ok:
            print("❌ Server health check failed!")
            return 1
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the FastAPI server is running on localhost:8000")
        return 1
    
    # Configuration from config.py
    test_import_dir = "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO"
    test_storage_root = "/mnt/c/temp/storage"
    
    print(f"\n📁 Using test directories:")
    print(f"  Source: {test_import_dir}")
    print(f"  Storage: {test_storage_root}")
    
    # Check if test directory exists 
    import_path = Path(test_import_dir)
    if not import_path.exists():
        print(f"❌ Test import directory does not exist: {test_import_dir}")
        return 1
    
    print(f"✅ Source directory exists - server will scan for images")
    
    # Create a test author first
    print_section("Creating Test Author")
    author_data = {
        "name": "Import Demo Author",
        "description": "Author created for import session demo"
    }
    
    author_response = requests.post(f"{base_url}/authors", json=author_data)
    author_info = print_response(author_response)
    
    if not author_info or isinstance(author_info, str) or author_response.status_code == 422:
        # Author might already exist, try to get existing authors
        print("⚠️  Author creation failed (might already exist). Fetching existing authors...")
        existing_authors_response = requests.get(f"{base_url}/authors")
        if existing_authors_response.ok:
            authors_data = existing_authors_response.json()
            if authors_data and "data" in authors_data and authors_data["data"]:
                default_author_id = authors_data["data"][0].get("id")
                print(f"✅ Using existing author with ID: {default_author_id}")
            else:
                default_author_id = None
                print("❌ No authors found. Continuing without default author...")
        else:
            default_author_id = None
            print("❌ Failed to fetch authors. Continuing without default author...")
    else:
        # Extract author ID from nested data structure
        if isinstance(author_info, dict) and "data" in author_info:
            default_author_id = author_info["data"].get("id")
        else:
            default_author_id = author_info.get("id") if isinstance(author_info, dict) else None
        print(f"✅ Created author with ID: {default_author_id}")
    
    # Demo 1: Start directory import
    print_section("Demo 1: Full Directory Import")
    
    import_request = {
        "source_path": test_import_dir,
        "source_description": "Demo import session - test micro directory",
        "default_author_id": default_author_id,
        "archive_base_path": test_storage_root,
        "storage_subfolder": f"demo_import_{int(time.time())}",
        "copy_files": True
    }
    
    print(f"Starting import with request:")
    print(json.dumps(import_request, indent=2))
    
    start_response = requests.post(f"{base_url}/import_sessions/start", json=import_request)
    import_data = print_response(start_response)
    
    if not import_data or isinstance(import_data, str):
        print("❌ Failed to start import session")
        return 1
    
    import_id = import_data.get("import_id") if isinstance(import_data, dict) else None
    if not import_id:
        print("❌ No import_id in response")
        return 1
    
    print(f"🚀 Started import session with ID: {import_id}")
    
    # Demo 2: Monitor progress
    print_section("Demo 2: Monitoring Import Progress")
    final_status = wait_for_import_completion(base_url, import_id)
    
    if final_status:
        print_section("Final Import Results")
        print(json.dumps(final_status, indent=2))
        
        # Import completed - storage handling is done by the service
        if final_status.get("status") == "completed":
            print("✅ Import completed successfully!")
            stats = final_status.get("stats", {})
            if stats:
                print(f"� Import Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
    
    # Demo 3: List all import sessions
    print_section("Demo 3: All Import Sessions")
    list_response = requests.get(f"{base_url}/import_sessions")
    print_response(list_response)
    
    print_section("Import Session Demo Complete")
    print("✅ Demo finished successfully!")
    print("\n📋 Summary:")
    print("  - Started full directory import")
    print("  - Monitored import progress")
    print("  - Reviewed import results")
    print("  - Listed all import sessions")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())