"""
Modernized API endpoints for importing images using Service Layer
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from core.dependencies import get_import_session_service
from core.config import Config
from services.import_session_service import ImportSessionService
from schemas.requests.import_session_requests import ImportStartRequest, ImportTestRequest
from schemas.responses.import_session_responses import (
    ImportResponse, ImportStartResponse, ImportListResponse,
    ImportTestResponse
)

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
        base_storage = Path(Config.TEST_STORAGE_ROOT)  # Use config path
        
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
