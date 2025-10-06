"""
Modernized API endpoints for image operations using Service Layer
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import FileResponse

from core.dependencies import get_image_service
from services.image_service_new import ImageService
from schemas.image_schemas import (
    ImageResponse, ImageCreateRequest, ImageUpdateRequest, 
    ImageSearchRequest, ImageRotateRequest
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


@router.get("/search", response_model=PaginatedResponse[ImageResponse])
async def search_images(
    q: Optional[str] = Query(None, description="Search query (filename, title, description)"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    rating_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating"),
    rating_max: Optional[int] = Query(None, ge=1, le=5, description="Maximum rating"),
    taken_after: Optional[str] = Query(None, description="Taken after date (YYYY-MM-DD)"),
    taken_before: Optional[str] = Query(None, description="Taken before date (YYYY-MM-DD)"),
    has_gps: Optional[bool] = Query(None, description="Filter by GPS availability"),
    file_format: Optional[str] = Query(None, description="Filter by file format"),
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of images to return"),
    sort_by: str = Query("taken_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    image_service: ImageService = Depends(get_image_service)
):
    """Search images with advanced criteria"""
    try:
        # Parse tags from comma-separated string
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Parse dates
        taken_after_dt = None
        taken_before_dt = None
        if taken_after:
            from datetime import datetime
            taken_after_dt = datetime.fromisoformat(taken_after)
        if taken_before:
            from datetime import datetime  
            taken_before_dt = datetime.fromisoformat(taken_before)
        
        # Create search request
        search_request = ImageSearchRequest(
            q=q,
            author_id=author_id,
            tags=tags_list,
            rating_min=rating_min,
            rating_max=rating_max,
            taken_after=taken_after_dt,
            taken_before=taken_before_dt,
            has_gps=has_gps,
            file_format=file_format,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return await image_service.search_images(search_request)
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/{image_id}/rotate")
async def rotate_image(
    image_id: int,
    rotate_request: ImageRotateRequest = ImageRotateRequest(clockwise=True),
    image_service: ImageService = Depends(get_image_service)
):
    """Rotate image 90 degrees (updates user_rotation field only)"""
    try:
        rotated_image = await image_service.rotate_image(image_id, rotate_request)
        
        return create_success_response(
            message=f"Image rotated to {rotated_image.user_rotation * 90} degrees",
            image_id=image_id,
            user_rotation=rotated_image.user_rotation
        )
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rotate image: {str(e)}")


@router.put("/{image_id}", response_model=ImageResponse)
async def update_image(
    image_id: int,
    update_data: ImageUpdateRequest,
    image_service: ImageService = Depends(get_image_service)
):
    """Update image metadata"""
    try:
        return await image_service.update_image(image_id, update_data)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update image: {str(e)}")


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    image_service: ImageService = Depends(get_image_service)
):
    """Delete image and associated files"""
    try:
        success = await image_service.delete_image(image_id)
        
        if success:
            return create_success_response(
                message="Image deleted successfully",
                image_id=image_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete image")
            
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")


@router.post("/", response_model=ImageResponse, status_code=201)
async def create_image(
    image_data: ImageCreateRequest,
    image_service: ImageService = Depends(get_image_service)
):
    """Create new image record"""
    try:
        return await image_service.create_image(image_data)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create image: {str(e)}")


# Statistics and utility endpoints

@router.get("/statistics/overview")
async def get_image_statistics(
    image_service: ImageService = Depends(get_image_service)
):
    """Get comprehensive image statistics"""
    try:
        stats = await image_service.get_image_statistics()
        return {"data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@router.get("/recent", response_model=list[ImageResponse])
async def get_recent_images(
    limit: int = Query(50, ge=1, le=200, description="Number of recent images to return"),
    image_service: ImageService = Depends(get_image_service)
):
    """Get recently imported images"""
    try:
        return await image_service.get_recent_images(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent images: {str(e)}")


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