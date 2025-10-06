#!/usr/bin/env python3
"""
Demo Utility Functions

Shared utilities for ImaLink import session demos.
Keeps demo files clean and focused on their specific test scenarios.
"""

import requests
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
    """Print response details and return parsed data"""
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


def check_server_health(base_url="http://localhost:8000"):
    """Check if the FastAPI server is running"""
    try:
        health_response = requests.get(f"{base_url}/health", timeout=3)
        if not health_response.ok:
            print("❌ Server health check failed!")
            return False
        print("✅ Server is running")
        return True
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the FastAPI server is running on localhost:8000")
        return False


def get_project_test_path(*path_parts):
    """
    Get path relative to the fase1 project root.
    
    Args:
        *path_parts: Path components to join (e.g., "test_user_files", "images")
    
    Returns:
        Path: Absolute path to the requested location
    """
    # Go up from import_session/ -> python_demos/ -> fase1/
    script_dir = Path(__file__).parent.parent.parent
    return script_dir.joinpath(*path_parts)


def wait_for_import_completion(base_url, import_id, max_wait_seconds=30):
    """
    Monitor import progress until completion
    
    Args:
        base_url: API base URL
        import_id: Import session ID to monitor
        max_wait_seconds: Maximum time to wait before timeout
    
    Returns:
        dict|None: Final status data or None if timeout/error
    """
    print(f"\n⏳ Monitoring import {import_id}...")
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < max_wait_seconds:
        try:
            check_count += 1
            status_response = requests.get(f"{base_url}/api/v1/import_sessions/status/{import_id}")
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


def start_import_session(base_url, import_request):
    """
    Start an import session
    
    Args:
        base_url: API base URL
        import_request: Import request dictionary
    
    Returns:
        tuple: (success: bool, import_id: int|None, response_data: dict|None)
    """
    print(f"Starting import with request:")
    print(json.dumps(import_request, indent=2))
    
    start_response = requests.post(f"{base_url}/api/v1/import_sessions/start", json=import_request)
    import_data = print_response(start_response)
    
    if not import_data or isinstance(import_data, str):
        print("❌ Failed to start import session")
        return False, None, None
    
    import_id = import_data.get("import_id") if isinstance(import_data, dict) else None
    if not import_id:
        print("❌ No import_id in response")
        return False, None, import_data
    
    print(f"🚀 Started import session with ID: {import_id}")
    return True, import_id, import_data


def list_import_sessions(base_url):
    """List all import sessions"""
    list_response = requests.get(f"{base_url}/api/v1/import_sessions")
    return print_response(list_response)


def demo_header(demo_name):
    """Print demo header with timestamp"""
    print(f"📥 ImaLink {demo_name}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def demo_summary(summary_points):
    """Print demo completion summary"""
    print("✅ Demo finished successfully!")
    print("\n📋 Summary:")
    for point in summary_points:
        print(f"  - {point}")


def analyze_import_results(final_status, result_title="Import Results"):
    """Analyze and display import results"""
    if not final_status:
        return
        
    print_section(f"Final {result_title}")
    print(json.dumps(final_status, indent=2))
    
    if final_status.get("status") == "completed":
        print(f"✅ {result_title} completed successfully!")
        stats = final_status.get("stats", {})
        if stats:
            print(f"📊 Import Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        # Show detailed response for analysis
        print_section(f"Complete {result_title} Analysis")
        print("Full response data for detailed analysis:")
        print(json.dumps(final_status, indent=2, sort_keys=True))