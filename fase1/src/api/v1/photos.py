"""
API endpoints for photo operations using Service Layer
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
import io

from core.dependencies import get_photo_service
from services.photo_service import PhotoService
from schemas.photo_schemas import (
    PhotoResponse, PhotoCreateRequest, PhotoUpdateRequest, 
    PhotoSearchRequest
)
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


# NOTE: Photo creation removed - Photos are now created automatically via POST /images
# When creating an Image without hothash, a new Photo is created automatically
# This simplifies the architecture: Image is the entry point, Photo is auto-generated


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


# Additional utility endpoints
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")