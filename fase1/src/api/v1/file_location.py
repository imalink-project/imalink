"""
API endpoints for file location and storage root configuration
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...database.connection import get_db_sync
from services.file_location_service import get_file_location_service
from models.photo import Photo
from models.image import Image
from models.import_session import ImportSession

router = APIRouter()


class StorageRootRequest(BaseModel):
    storage_root: str


class FileLocationResponse(BaseModel):
    found: bool
    full_path: Optional[str] = None
    directory_name: Optional[str] = None
    import_session_id: Optional[int] = None
    storage_root: Optional[str] = None
    error_message: Optional[str] = None


class StorageStatusResponse(BaseModel):
    accessible: bool
    total_files: int
    found_files: int
    missing_files: int
    storage_root: Optional[str] = None
    directory_name: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/configure-storage-root")
async def configure_storage_root(
    request: StorageRootRequest
) -> Dict[str, Any]:
    """
    Configure storage root path (e.g., 'X:', 'X:\\my photo storage')
    """
    try:
        file_service = get_file_location_service(db)
        success = file_service.set_storage_root(request.storage_root)
        
        if success:
            return {
                "success": True,
                "message": f"Storage root configured: {request.storage_root}",
                "storage_root": file_service.get_storage_root()
            }
        else:
            return {
                "success": False,
                "message": f"Invalid storage root path: {request.storage_root}"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring storage root: {str(e)}"
        )


@router.get("/storage-root")
async def get_storage_root(
    db = Depends(get_database)
) -> Dict[str, str]:
    """Get current storage root path"""
    try:
        file_service = get_file_location_service(db)
        return {
            "storage_root": file_service.get_storage_root()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting storage root: {str(e)}"
        )


@router.get("/image/{image_id}/location")
async def get_image_location(
    image_id: int,
    storage_root: Optional[str] = None,
    db = Depends(get_database)
) -> FileLocationResponse:
    """
    Find location of a specific image file via ImportSession
    """
    try:
        # Get image
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Find file location
        file_service = get_file_location_service(db, storage_root)
        location = file_service.find_image_file(image)
        
        return FileLocationResponse(
            found=location.found,
            full_path=location.full_path,
            directory_name=location.directory_name,
            import_session_id=location.import_session_id,
            storage_root=location.storage_root,
            error_message=location.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error finding image location: {str(e)}"
        )


@router.get("/photo/{hothash}/storage-status")
async def get_photo_storage_status(
    hothash: str,
    storage_root: Optional[str] = None,
    db = Depends(get_database)
) -> StorageStatusResponse:
    """
    Get storage status for all files associated with a photo
    """
    try:
        # Get photo
        photo = db.query(Photo).filter(Photo.hothash == hothash).first()
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Get storage status
        file_service = get_file_location_service(db, storage_root)
        status = file_service.get_photo_storage_status(photo)
        
        return StorageStatusResponse(
            accessible=status.accessible,
            total_files=status.total_files,
            found_files=status.found_files,
            missing_files=status.missing_files,
            storage_root=status.storage_root,
            directory_name=status.directory_name,
            error_message=status.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting photo storage status: {str(e)}"
        )


@router.get("/import-session/{import_session_id}/storage-status")
async def get_import_session_storage_status(
    import_session_id: int,
    storage_root: Optional[str] = None,
    db = Depends(get_database)
) -> StorageStatusResponse:
    """
    Get storage status for an entire import session
    """
    try:
        # Get import session
        import_session = db.query(ImportSession).filter(ImportSession.id == import_session_id).first()
        if not import_session:
            raise HTTPException(status_code=404, detail="ImportSession not found")
        
        # Get storage status
        file_service = get_file_location_service(db, storage_root)
        status = file_service.get_import_session_storage_status(import_session)
        
        return StorageStatusResponse(
            accessible=status.accessible,
            total_files=status.total_files,
            found_files=status.found_files,
            missing_files=status.missing_files,
            storage_root=status.storage_root,
            directory_name=status.directory_name,
            error_message=status.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting import session storage status: {str(e)}"
        )


@router.get("/storage-directories")
async def list_storage_directories(
    storage_root: Optional[str] = None,
    db = Depends(get_database)
) -> Dict[str, Any]:
    """
    List all available storage directories in storage root
    """
    try:
        file_service = get_file_location_service(db, storage_root)
        directories = file_service.list_available_storage_directories()
        
        return {
            "storage_root": file_service.get_storage_root(),
            "directories": directories,
            "total_directories": len(directories)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing storage directories: {str(e)}"
        )