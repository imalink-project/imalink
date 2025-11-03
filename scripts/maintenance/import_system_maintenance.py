#!/usr/bin/env python3
"""
Import System Maintenance Utilities

Quick utilities for common import system maintenance tasks.
Use these scripts for debugging, monitoring, and system health checks.
"""

import sys
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add src to Python path for imports
script_dir = Path(__file__).parent
src_dir = script_dir.parent.parent / "src"
sys.path.insert(0, str(src_dir))

def check_import_system_health():
    """
    Quick health check of the import system components
    """
    print("🏥 ImaLink Import System Health Check")
    print("=" * 50)
    
    health_checks = []
    
    # 1. Check if core services can be imported
    try:
        from services.import_sessions_background_service import ImportSessionsBackgroundService
        health_checks.append("✅ ImportSessionsBackgroundService: OK")
    except Exception as e:
        health_checks.append(f"❌ ImportSessionsBackgroundService: {e}")
    
    # 2. Check ImageProcessor
    try:
        from services.importing.image_processor import ImageProcessor
        processor = ImageProcessor()
        health_checks.append("✅ ImageProcessor: OK")
    except Exception as e:
        health_checks.append(f"❌ ImageProcessor: {e}")
    
    # 3. Check repositories
    try:
        from repositories.import_session_repository import ImportSessionRepository
        from repositories.image_repository import ImageRepository
        health_checks.append("✅ Repositories: OK")
    except Exception as e:
        health_checks.append(f"❌ Repositories: {e}")
    
    # 4. Check database connection
    try:
        from database.connection import get_db_sync
        db = get_db_sync()
        db.close()
        health_checks.append("✅ Database connection: OK")
    except Exception as e:
        health_checks.append(f"❌ Database connection: {e}")
    
    # Print results
    for check in health_checks:
        print(check)
    
    # Summary
    failed_checks = [c for c in health_checks if "❌" in c]
    if failed_checks:
        print(f"\n⚠️ {len(failed_checks)} component(s) have issues")
        return False
    else:
        print("\n🎉 All import system components are healthy!")
        return True


def list_recent_imports(days: int = 7):
    """
    List recent import sessions for monitoring
    """
    print(f"📊 Recent Import Sessions (last {days} days)")
    print("=" * 50)
    
    try:
        from database.connection import get_db_sync
        from repositories.import_session_repository import ImportSessionRepository
        
        db = get_db_sync()
        import_repo = ImportSessionRepository(db)
        
        # This would need to be implemented in the repository
        # For now, just show the structure
        print("🔄 Import session monitoring would show:")
        print("   - Import session IDs and timestamps")
        print("   - Success/failure rates")
        print("   - File counts processed")
        print("   - Error summaries")
        print("\n💡 To implement: Add date filtering to ImportSessionRepository")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error accessing import history: {e}")


def validate_import_paths():
    """
    Validate that import-related paths and directories exist
    """
    print("📁 Import Path Validation")
    print("=" * 30)
    
    try:
        from core.config import Config
        
        # Check common test paths
        test_paths = [
            "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO",
            "/mnt/c/temp/storage"
        ]
        
        for path_str in test_paths:
            path = Path(path_str)
            if path.exists():
                if path.is_dir():
                    file_count = len(list(path.rglob("*"))) if path.is_dir() else 0
                    print(f"✅ {path_str} (directory with {file_count} items)")
                else:
                    print(f"⚠️ {path_str} (exists but not a directory)")
            else:
                print(f"❌ {path_str} (does not exist)")
                
    except Exception as e:
        print(f"❌ Error validating paths: {e}")


def show_import_workflow():
    """
    Display the import workflow for reference
    """
    print("🔄 ImaLink Import Workflow")
    print("=" * 40)
    
    workflow_steps = [
        "1. API receives import request (start_import)",
        "2. Background task started (import_directory_background)", 
        "3. Service processes directory (process_directory_import):",
        "   3a. Find all image files (_find_image_files)",
        "   3b. For each file:",
        "       - Calculate hash (_calculate_file_hash)",
        "       - Check for duplicates (image_repo.exists_by_hash)",
        "       - Extract metadata (image_processor.extract_metadata)",
        "       - Save to database (Image creation)",
        "   3c. Copy files to storage (_copy_files_to_storage)",
        "   3d. Generate import feedback (_generate_import_feedback)",
        "   3e. Mark import as completed (complete_import)",
        "4. Return status to user"
    ]
    
    for step in workflow_steps:
        print(step)
    
    print("\n📍 Key Files:")
    print("   • Main logic: src/services/import_sessions_background_service.py")
    print("   • Metadata: src/services/importing/image_processor.py")
    print("   • API entry: src/api/v1/import_sessions.py")


def quick_diagnostics():
    """
    Run a comprehensive diagnostic of the import system
    """
    print("🔧 ImaLink Import System Diagnostics")
    print("=" * 50)
    
    # Component health
    print("\n1. Component Health:")
    health_ok = check_import_system_health()
    
    # Path validation  
    print("\n2. Path Validation:")
    validate_import_paths()
    
    # Show workflow for reference
    print("\n3. Workflow Reference:")
    show_import_workflow()
    
    # Recent activity (placeholder)
    print("\n4. Recent Activity:")
    list_recent_imports(7)
    
    # Summary
    print("\n" + "=" * 50)
    if health_ok:
        print("🎉 System appears healthy and ready for imports")
    else:
        print("⚠️ Some components need attention before running imports")
    
    print("\n💡 For detailed testing, run:")
    print("   cd python_demos/import_session/")  
    print("   uv run demo_jpg_dng.py")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "health":
            check_import_system_health()
        elif command == "imports":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            list_recent_imports(days)
        elif command == "paths":
            validate_import_paths()
        elif command == "workflow":
            show_import_workflow()
        else:
            print("❌ Unknown command. Use: health, imports, paths, workflow, or run without args for full diagnostics")
    else:
        # Run full diagnostics
        quick_diagnostics()