"""
Modernized API endpoints for importing images using Service Layer
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from core.dependencies import get_import_session_service
from services.import_session_service import ImportSessionService
from schemas.requests.import_session_requests import ImportStartRequest, ImportTestRequest
from schemas.responses.import_session_responses import (
    ImportResponse, ImportStartResponse, ImportListResponse,
    ImportTestResponse
)
from schemas.common import SingleResponse
from core.exceptions import APIException
from services.importing.image_processor import ImageProcessor
import datetime as dt

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify routing works"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Test endpoint accessed")
    return {"message": "Test endpoint works!", "timestamp": "2025-10-02", "routing_confirmed": True}


def simple_background_test():
    """Simple test function to verify background tasks work"""
    logger.info("Background task executed successfully")


def run_import_background_service(import_id: int, source_directory: str):
    """Run import using service layer in background"""
    # Write to a debug file to confirm this function runs
    debug_file = "C:/temp/import_debug.txt"
    
    try:
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now()} - 🚀 BACKGROUND SERVICE: Starting import for session {import_id}\n")
            f.write(f"{dt.datetime.now()} - 📦 BACKGROUND SERVICE: Processing directory {source_directory}\n")
        
        # Import here to avoid circular imports
        from database.connection import get_db_sync
        from services.import_sessions_background_service import ImportSessionsBackgroundService
        
        # Get database connection and service
        db = get_db_sync()
        background_service = ImportSessionsBackgroundService(db)
        
        # Process the import using the service layer
        success = background_service.process_directory_import(import_id, source_directory)
        
        with open(debug_file, "a", encoding="utf-8") as f:
            status = "completed" if success else "failed"
            f.write(f"{dt.datetime.now()} - ✅ BACKGROUND SERVICE: Import {status} for session {import_id}\n")
        
    except Exception as e:
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now()} - ❌ BACKGROUND SERVICE ERROR: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()


def import_directory_background(import_id: int, source_path: str, source_description: str):
    """
    Background task to import all images from a directory using service layer
    """
    try:
        logger.info(f"Background import task started for session {import_id}")
        
        from database.connection import get_db_sync
        from services.import_sessions_background_service import ImportSessionsBackgroundService
        
        # Get database connection and service
        db = get_db_sync()
        background_service = ImportSessionsBackgroundService(db)
        
        # Process the import using the service layer
        success = background_service.process_directory_import(import_id, source_path)
        
        status = "completed" if success else "failed"
        print(f"🏁 Background import {status} for session {import_id}")
        
    except Exception as e:
        print(f"❌ Background import failed for session {import_id}: {e}")
        import traceback
        traceback.print_exc()


@router.post("/", response_model=ImportStartResponse)
async def import_directory(
    request: ImportStartRequest,
    background_tasks: BackgroundTasks,
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Main import endpoint - import directory
    """

    logger.info("Import directory endpoint called")
    debug_info = {"endpoint_hit": True, "source_directory": request.source_directory}
    try:
        response = await import_service.start_import(request)
        debug_info["service_called"] = True
        
        # Start background import task using threading - return debug info in response
        import threading
        
        debug_info = {
            "threading_approach": True,
            "import_id": response.import_id,
            "source_directory": request.source_directory
        }
        
        try:
            # Start simple test in thread
            test_thread = threading.Thread(target=simple_background_test)
            test_thread.daemon = True
            test_thread.start()
            debug_info["test_thread_started"] = True
            
            # Start actual import in thread
            import_thread = threading.Thread(
                target=run_import_background_service,
                args=(response.import_id, request.source_directory)
            )
            import_thread.daemon = True
            import_thread.start()
            debug_info["import_thread_started"] = True
            
        except Exception as e:
            debug_info["thread_error"] = str(e)
        
        # Add debug info to response object
        if hasattr(response, 'debug_info'):
            response.debug_info = debug_info
        else:
            # If we can't add to response, at least we know threading was attempted
            pass
            
        return response
        
    except Exception as e:
        if "does not exist" in str(e) or "must be a directory" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/start", response_model=ImportStartResponse)
async def start_import(
    request: ImportStartRequest,
    background_tasks: BackgroundTasks,
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Start an import process for a directory
    """
    logger.info("Start import endpoint called")
    try:
        response = await import_service.start_import(request)
        
        # Start background import task
        background_tasks.add_task(
            import_directory_background,
            response.import_id,
            request.source_path,
            request.source_description
        )
        
        return response
        
    except Exception as e:
        if "does not exist" in str(e) or "must be a directory" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/status/{import_id}", response_model=ImportResponse)
async def get_import_status(
    import_id: int, 
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Get status of an Import
    """
    try:
        return await import_service.get_import_status(import_id)
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Import not found")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/", response_model=ImportListResponse)
async def list_imports(
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    List all import imports
    """
    try:
        return await import_service.list_imports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing imports: {str(e)}")


@router.post("/test-single", response_model=ImportTestResponse)  
async def test_single_image(
    request: ImportTestRequest,
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Test importing a single image file (for development/testing)
    """
    try:
        return await import_service.test_single_file(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test import failed: {str(e)}")


@router.get("/storage-info")
async def get_storage_info(
    subfolder: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get information about storage path that will be used for file copying
    (Integrated from import_once functionality)
    """
    try:
        from pathlib import Path
        
        # Generate storage info similar to import_once
        base_storage = Path("C:/ImaLink/Storage")  # TODO: Make configurable
        
        if subfolder:
            storage_path = base_storage / subfolder
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_path = base_storage / f"import_{timestamp}"
        
        return {
            "storage_path": str(storage_path),
            "base_storage": str(base_storage),
            "exists": storage_path.exists(),
            "writable": storage_path.parent.exists(),
            "subfolder": subfolder
        }
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting storage information: {str(e)}"
        )
