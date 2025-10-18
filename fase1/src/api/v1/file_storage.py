"""
FileStorage API - Endpoints for managing FileStorage metadata

This API provides endpoints for:
1. Registering new FileStorage instances (frontend creates directories, backend stores metadata)
2. Retrieving FileStorage metadata
3. Updating FileStorage status and accessibility
4. Managing storage relationships

These endpoints support the hybrid storage architecture where the frontend
handles all file operations and the backend stores only metadata.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.dependencies import get_db
from models.file_storage import FileStorage
from core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class FileStorageCreateRequest(BaseModel):
    """Request model for creating a new FileStorage"""
    storage_uuid: str = Field(..., description="UUID for the storage directory")
    base_path: str = Field(..., description="Base path where storage is located")
    display_name: str = Field(..., description="User-friendly name for the storage")
    description: Optional[str] = Field(None, description="Optional description")


class FileStorageMetadataResponse(BaseModel):
    """Response model for FileStorage metadata"""
    id: int
    storage_uuid: str
    directory_name: str
    base_path: str
    full_path: str
    display_name: Optional[str]
    description: Optional[str]
    is_active: bool
    is_accessible: bool
    total_files: int
    total_size_bytes: int
    storage_size_mb: float
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class FileStorageUpdateRequest(BaseModel):
    """Request model for updating FileStorage metadata"""
    display_name: Optional[str] = None
    description: Optional[str] = None


@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_file_storage(
    request: FileStorageCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new FileStorage record (metadata only)
    
    The frontend has already created the physical directory structure.
    This endpoint just registers the metadata in the database.
    """
    try:
        # Check if storage with this UUID already exists
        existing = db.query(FileStorage).filter(
            FileStorage.storage_uuid == request.storage_uuid
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"FileStorage with UUID {request.storage_uuid} already exists"
            )
        
        # Create new FileStorage record
        storage = FileStorage(
            base_path=request.base_path,
            display_name=request.display_name,
            description=request.description
        )
        
        # Override the auto-generated UUID with the one from frontend
        storage.storage_uuid = request.storage_uuid
        # full_path is now a computed property
        
        db.add(storage)
        db.commit()
        db.refresh(storage)
        
        logger.info(f"Created FileStorage: {storage.storage_uuid} at {storage.full_path}")
        
        return {
            "success": True,
            "message": "FileStorage created successfully",
            "data": {
                "id": storage.id,
                "storage_uuid": storage.storage_uuid,
                "directory_name": storage.directory_name,
                "full_path": storage.full_path,
                "display_name": storage.display_name
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create FileStorage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create FileStorage: {str(e)}"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_file_storages(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all FileStorage instances
    """
    try:
        storages = db.query(FileStorage).all()
        
        storage_list = []
        for storage in storages:
            storage_data = {
                "id": storage.id,
                "storage_uuid": storage.storage_uuid,
                "directory_name": storage.directory_name,
                "base_path": storage.base_path,
                "full_path": storage.full_path,
                "display_name": storage.display_name,
                "description": storage.description,
                "is_active": storage.is_active,
                "is_accessible": storage.is_accessible,
                "total_files": storage.total_files or 0,
                "total_size_bytes": storage.total_size_bytes or 0,
                "storage_size_mb": storage.storage_size_mb,
                "created_at": storage.created_at.isoformat() if storage.created_at else None,
                "updated_at": storage.updated_at.isoformat() if storage.updated_at else None
            }
            storage_list.append(storage_data)
        
        return {
            "success": True,
            "data": {
                "storages": storage_list,
                "total_count": len(storage_list)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get FileStorage metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve FileStorage metadata: {str(e)}"
        )


@router.get("/{storage_uuid}", response_model=Dict[str, Any])
async def get_file_storage(
    storage_uuid: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific FileStorage by UUID
    """
    try:
        storage = db.query(FileStorage).filter(
            FileStorage.storage_uuid == storage_uuid
        ).first()
        
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FileStorage with UUID {storage_uuid} not found"
            )
        
        storage_data = {
            "id": storage.id,
            "storage_uuid": storage.storage_uuid,
            "directory_name": storage.directory_name,
            "base_path": storage.base_path,
            "full_path": storage.full_path,
            "display_name": storage.display_name,
            "description": storage.description,
            "is_active": storage.is_active,
            "is_accessible": storage.is_accessible,
            "total_files": storage.total_files or 0,
            "total_size_bytes": storage.total_size_bytes or 0,
            "storage_size_mb": storage.storage_size_mb,
            "created_at": storage.created_at.isoformat() if storage.created_at else None,
            "updated_at": storage.updated_at.isoformat() if storage.updated_at else None,
            "import_sessions_count": len(storage.import_sessions) if storage.import_sessions else 0
        }
        
        return {
            "success": True,
            "data": storage_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get FileStorage details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve FileStorage details: {str(e)}"
        )


@router.put("/{storage_uuid}", response_model=Dict[str, Any])
async def update_file_storage(
    storage_uuid: str,
    request: FileStorageUpdateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update FileStorage metadata
    """
    try:
        storage = db.query(FileStorage).filter(
            FileStorage.storage_uuid == storage_uuid
        ).first()
        
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FileStorage with UUID {storage_uuid} not found"
            )
        
        # Update provided fields
        if request.display_name is not None:
            storage.display_name = request.display_name
        if request.description is not None:
            storage.description = request.description
        
        db.commit()
        db.refresh(storage)
        
        logger.info(f"Updated FileStorage metadata: {storage_uuid}")
        
        return {
            "success": True,
            "message": "FileStorage metadata updated successfully",
            "data": {
                "storage_uuid": storage.storage_uuid,
                "display_name": storage.display_name,
                "is_accessible": storage.is_accessible,
                "total_files": storage.total_files,
                "storage_size_mb": storage.storage_size_mb
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update FileStorage metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update FileStorage metadata: {str(e)}"
        )


@router.delete("/{storage_uuid}", response_model=Dict[str, Any])
async def delete_file_storage(
    storage_uuid: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete FileStorage record from database (metadata only)
    
    This does NOT delete the physical files - that's the frontend's responsibility.
    """
    try:
        storage = db.query(FileStorage).filter(
            FileStorage.storage_uuid == storage_uuid
        ).first()
        
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FileStorage with UUID {storage_uuid} not found"
            )
        
        # Check if storage has import sessions
        if storage.import_sessions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete FileStorage with {len(storage.import_sessions)} import sessions. Delete sessions first."
            )
        
        storage_name = storage.display_name or storage.directory_name
        
        db.delete(storage)
        db.commit()
        
        logger.info(f"Deleted FileStorage record: {storage_uuid} ({storage_name})")
        
        return {
            "success": True,
            "message": f"FileStorage record '{storage_name}' deleted successfully",
            "data": {
                "storage_uuid": storage_uuid,
                "deleted_name": storage_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete FileStorage record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete FileStorage record: {str(e)}"
        )