"""
Modernized API endpoints for importing images using Service Layer
"""
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form

from core.dependencies import get_import_session_service
from core.config import Config
from services.import_session_service import ImportSessionService
from schemas.requests.import_session_requests import ImportStartRequest, ImportTestRequest
from schemas.responses.import_session_responses import (
    ImportResponse, ImportStartResponse, ImportListResponse,
    ImportTestResponse, ImportProgressResponse, ImportCancelResponse
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


@router.post("/upload", response_model=ImportStartResponse)
async def upload_and_import(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    paths: List[str] = Form(...),
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Upload files with directory structure and start import process
    """
    logger.info(f"Upload endpoint called with {len(files)} files")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    if len(files) != len(paths):
        raise HTTPException(status_code=400, detail="Files and paths count mismatch")
    
    # Create temporary directory for uploaded files
    temp_dir = tempfile.mkdtemp(prefix="imalink_upload_")
    temp_path = Path(temp_dir)
    
    try:
        # Save all uploaded files preserving directory structure
        uploaded_files = []
        for file, relative_path in zip(files, paths):
            if not file.filename:
                continue
                
            # Create full path preserving directory structure
            # Clean up the relative path to avoid security issues
            clean_path = Path(relative_path).as_posix().lstrip('/')
            file_path = temp_path / clean_path
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file to temp directory with structure
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            uploaded_files.append(str(file_path))
            
        logger.info(f"Saved {len(uploaded_files)} files to {temp_dir} with directory structure")
        
        # Create import request for the temporary directory
        import_request = ImportStartRequest(
            source_path=str(temp_path),
            source_description=f"Uploaded files: {len(files)} files with directory structure",
            archive_base_path=None,
            storage_subfolder=None,
            copy_files=True  # We want to copy uploaded files to permanent storage
        )
        
        # Start import process
        response = await import_service.start_import(import_request)
        
        # Start background import task
        background_tasks.add_task(
            import_directory_background,
            response.import_id,
            str(temp_path),
            import_request.source_description
        )
        
        return response
        
    except Exception as e:
        # Clean up temp directory on error
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


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


@router.post("/{import_id}/copy-to-storage")
async def copy_to_storage(
    import_id: int,
    request: dict,  # {"storage_path": "/path/to/storage"}
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Copy files from temp directory to user-specified storage location
    """
    try:
        storage_path = request.get("storage_path")
        if not storage_path:
            raise HTTPException(status_code=400, detail="storage_path is required")
        
        result = await import_service.copy_to_storage(import_id, storage_path)
        return result
        
    except Exception as e:
        logger.error(f"Copy to storage failed for import {import_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Copy to storage failed: {str(e)}")


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


@router.get("/{import_id}/progress", response_model=ImportProgressResponse)
async def get_import_progress(
    import_id: int,
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Get real-time progress of an import session
    """
    try:
        return await import_service.get_import_progress(import_id)
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Import not found")
        raise HTTPException(status_code=500, detail=f"Error getting progress: {str(e)}")


@router.post("/{import_id}/cancel", response_model=ImportCancelResponse)
async def cancel_import(
    import_id: int,
    import_service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Cancel a running import session
    """
    try:
        return await import_service.cancel_import(import_id)
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Import not found")
        raise HTTPException(status_code=500, detail=f"Error cancelling import: {str(e)}")


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
