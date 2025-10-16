"""
Image API endpoints - READ-ONLY operations

IMPORTANT ARCHITECTURAL NOTE:
- Images can only be CREATED via Photo batch operations (POST /photos/batch)
- Images cannot be created, updated, or deleted individually
- All Image CRUD operations must go through the Photo API
- Images are always part of a PhotoGroup and cannot exist standalone

This API provides read-only access to Image data and related operations.
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import FileResponse

from core.dependencies import get_image_service
from services.image_service_new import ImageService
from schemas.image_schemas import (
    ImageResponse, ImageCreateRequest, ImageUpdateRequest
)
from schemas.common import PaginatedResponse, create_success_response
from core.exceptions import APIException

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ImageResponse])
async def list_images(
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of images to return"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    image_service: ImageService = Depends(get_image_service)
):
    """Get paginated list of images with metadata"""
    try:
        return await image_service.get_images(
            offset=offset,
            limit=limit,
            author_id=author_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images: {str(e)}")


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image_details(
    image_id: int,
    image_service: ImageService = Depends(get_image_service)
):
    """Get detailed information about a specific image"""
    try:
        return await image_service.get_image_by_id(image_id)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")


@router.get("/{image_id}/hotpreview")
async def get_hotpreview(
    image_id: int,
    image_service: ImageService = Depends(get_image_service)
):
    """Get hot preview image data"""
    try:
        hotpreview_data = await image_service.get_image_hotpreview(image_id)
        
        if not hotpreview_data:
            raise HTTPException(status_code=404, detail="Hot preview not found")
        
        return Response(
            content=hotpreview_data,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Type": "image/jpeg"
            }
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve hot preview: {str(e)}")


@router.get("/{image_id}/pool/{size}")
async def get_pool_image(
    image_id: int,
    size: str,
    image_service: ImageService = Depends(get_image_service)
):
    """
    Get optimized image version from pool
    
    Available sizes:
    - small: 400x400 max (for gallery grid view)
    - medium: 800x800 max (for standard viewing)  
    - large: 1200x1200 max (for detailed viewing)
    """
    try:
        # Validate size parameter
        valid_sizes = ["small", "medium", "large"]
        if size not in valid_sizes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
            )
        
        pool_image_path = await image_service.get_image_pool(image_id, size)
        
        if not pool_image_path:
            raise HTTPException(status_code=404, detail="Pool image not found")
        
        return FileResponse(
            path=pool_image_path,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Content-Type": "image/jpeg"
            }
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pool image: {str(e)}")


# NOTE: /search endpoint removed - use GET /images with query parameters instead
# The standard list endpoint supports filtering and sorting


@router.post("/", response_model=ImageResponse, status_code=201)
async def create_image(
    image_data: ImageCreateRequest,
    image_service: ImageService = Depends(get_image_service)
):
    """
    Create new Image with automatic Photo creation/association
    
    NEW ARCHITECTURE: Images drive Photo creation
    - hotpreview is REQUIRED in the request (thumbnail binary data)
    - photo_hothash is automatically generated from hotpreview via SHA256
    - If Photo with this hothash exists: Image is added to existing Photo
    - If Photo doesn't exist: New Photo is created automatically
    
    First Image with new hotpreview = Creates new Photo (master)
    Subsequent Images with same hotpreview = Added to existing Photo
    """
    try:
        return await image_service.create_image_with_photo(image_data)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create image: {str(e)}")

# NOTE: rotate endpoint removed - rotation is a Photo-level concern, not Image-level
# Use Photo API for rotation operations

# Images cannot be updated or deleted individually - they are managed via Photo operations
# Use PUT /photos/{hothash} and DELETE /photos/{hothash} instead


# Utility endpoints

# NOTE: /recent endpoint removed - use GET /images with sort_by=created_at&sort_order=desc instead

@router.get("/author/{author_id}", response_model=list[ImageResponse])
async def get_images_by_author(
    author_id: int,
    limit: int = Query(100, ge=1, le=500, description="Number of images to return"),
    image_service: ImageService = Depends(get_image_service)
):
    """Get images by specific author"""
    try:
        return await image_service.get_images_by_author(author_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images by author: {str(e)}")