#!/usr/bin/env python3
"""
ImaLink JPG-DNG Pair Import Demo

Demonstrates JPG-DNG pair import workflow:
1. Start import from jpg_dng_forskjellige directory
2. Monitor import progress
3. Analyze complete import response
4. No author assignment (empty field test)

Uses test directory:
- Source: {project_root}/test_user_files/images/jpg_dng_forskjellige
- Storage: /mnt/c/temp/storage
"""

import sys
import time
from demo_util import (
    demo_header, print_section, check_server_health, get_project_test_path,
    start_import_session, wait_for_import_completion, analyze_import_results,
    list_import_sessions, demo_summary
)


def main():
    demo_header("JPG-DNG Import Demo")
    
    base_url = "http://localhost:8000"
    
    # Test connection first
    if not check_server_health(base_url):
        return 1
    
    # Configuration for JPG-DNG pair testing
    test_import_dir = get_project_test_path("test_user_files", "images", "jpg_dng_forskjellige")
    test_storage_root = "/mnt/c/temp/storage"
    
    print(f"\n📁 Using JPG-DNG test directory:")
    print(f"  Source: {test_import_dir}")
    print(f"  Storage: {test_storage_root}")
    
    # Check if project-relative path exists
    if not test_import_dir.exists():
        print(f"❌ Test import directory does not exist: {test_import_dir}")
        return 1
    
    print(f"✅ Source directory exists - server will scan for JPG-DNG pairs")
    
    # No author creation - use empty field for testing
    print("ℹ️  Using empty author field (no default author)")
    
    # Demo 1: Start JPG-DNG import
    print_section("Demo 1: JPG-DNG Pair Import")
    
    import_request = {
        "source_path": str(test_import_dir),
        "source_description": "JPG-DNG pair import test",
        "default_author_id": None,
        "archive_base_path": test_storage_root,
        "storage_subfolder": f"jpg_dng_import_{int(time.time())}",
        "copy_files": True
    }
    
    # Start import using utility function
    success, import_id, _ = start_import_session(base_url, import_request)
    if not success:
        return 1
    
    # Demo 2: Monitor progress
    print_section("Demo 2: Monitoring Import Progress")
    final_status = wait_for_import_completion(base_url, import_id)
    
    # # Demo 3: Analyze results
    # if final_status:
    #     analyze_import_results(final_status, "JPG-DNG Import Results")
    
    # # Demo 4: List all import sessions
    # print_section("Demo 4: All Import Sessions")
    # list_import_sessions(base_url)
    
    # print_section("JPG-DNG Import Demo Complete")
    # demo_summary([
    #     "Started JPG-DNG pair import (no author)",
    #     "Monitored import progress",
    #     "Analyzed complete import response",
    #     "Listed all import sessions"
    # ])
    
    return 0


if __name__ == "__main__":
    sys.exit(main())