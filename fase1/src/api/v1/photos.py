"""
API endpoints for photo operations using Service Layer
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
import io

from core.dependencies import get_photo_service
from services.photo_service import PhotoService
from schemas.photo_schemas import (
    PhotoResponse, PhotoCreateRequest, PhotoUpdateRequest, 
    PhotoSearchRequest, PhotoRotateRequest
)
from schemas.requests.photo_batch_requests import PhotoGroupBatchRequest
from schemas.responses.photo_batch_responses import BatchPhotoResponse
from schemas.common import PaginatedResponse, create_success_response
from core.exceptions import APIException

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[PhotoResponse])
async def list_photos(
    offset: int = Query(0, ge=0, description="Number of photos to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of photos to return"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get paginated list of photos with metadata"""
    try:
        return await photo_service.get_photos(
            offset=offset,
            limit=limit,
            author_id=author_id
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/search", response_model=PaginatedResponse[PhotoResponse])
async def search_photos(
    search_request: PhotoSearchRequest,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Search photos with advanced filtering"""
    try:
        return await photo_service.search_photos(search_request)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{hothash}", response_model=PhotoResponse)
async def get_photo(
    hothash: str,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get single photo by hash"""
    try:
        return await photo_service.get_photo_by_hash(hothash)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/", response_model=PhotoResponse, status_code=201)
async def create_photo(
    photo_data: PhotoCreateRequest,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Create new photo"""
    try:
        return await photo_service.create_photo(photo_data)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=BatchPhotoResponse, status_code=201)
async def create_photo_batch(
    batch_request: PhotoGroupBatchRequest,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Create multiple photos with their associated images in batch"""
    try:
        return await photo_service.create_photo_batch(batch_request)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch creation failed: {str(e)}")


@router.put("/{hothash}", response_model=PhotoResponse)
async def update_photo(
    hothash: str,
    photo_data: PhotoUpdateRequest,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Update existing photo"""
    try:
        return await photo_service.update_photo(hothash, photo_data)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{hothash}")
async def delete_photo(
    hothash: str,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Delete photo"""
    try:
        success = await photo_service.delete_photo(hothash)
        return create_success_response(message="Photo deleted successfully")
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{hothash}/rotate", response_model=PhotoResponse)
async def rotate_photo(
    hothash: str,
    rotate_request: PhotoRotateRequest,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Rotate photo by 90 degrees"""
    try:
        return await photo_service.rotate_photo(hothash, rotate_request)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{hothash}/hotpreview")
async def get_hotpreview(
    hothash: str,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get hotpreview image for photo"""
    try:
        hotpreview_data = await photo_service.get_hotpreview(hothash)
        
        # Return as streaming response
        if hotpreview_data:
            return StreamingResponse(
                io.BytesIO(hotpreview_data),
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename=hotpreview_{hothash[:8]}.jpg",
                    "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Hotpreview not found")
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/statistics/overview")
async def get_statistics(
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get photo collection statistics"""
    try:
        stats = await photo_service.get_photo_statistics()
        return create_success_response(message="Statistics retrieved successfully", data=stats)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Additional utility endpoints

@router.get("/{hothash}/files", response_model=list[dict])
async def get_photo_files(
    hothash: str,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get list of files associated with photo"""
    try:
        photo = await photo_service.get_photo_by_hash(hothash)
        return create_success_response(
            message="Photo files retrieved successfully",
            data=photo.files
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{hothash}/metadata")
async def get_photo_metadata(
    hothash: str,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get photo metadata (title, description, tags, rating)"""
    try:
        photo = await photo_service.get_photo_by_hash(hothash)
        metadata = {
            "title": photo.title,
            "description": photo.description,
            "tags": photo.tags,
            "rating": photo.rating,
            "user_rotation": photo.user_rotation
        }
        return create_success_response(
            message="Photo metadata retrieved successfully",
            data=metadata
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{hothash}/metadata")
async def update_photo_metadata(
    hothash: str,
    metadata: dict,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Update photo metadata (title, description, tags, rating)"""
    try:
        # Convert to PhotoUpdateRequest
        update_data = PhotoUpdateRequest(
            title=metadata.get("title"),
            description=metadata.get("description"),
            tags=metadata.get("tags"),
            rating=metadata.get("rating"),
            user_rotation=metadata.get("user_rotation"),
            author_id=metadata.get("author_id")
        )
        
        updated_photo = await photo_service.update_photo(hothash, update_data)
        return create_success_response(
            message="Photo metadata updated successfully",
            data={
                "title": updated_photo.title,
                "description": updated_photo.description,
                "tags": updated_photo.tags,
                "rating": updated_photo.rating,
                "user_rotation": updated_photo.user_rotation
            }
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")