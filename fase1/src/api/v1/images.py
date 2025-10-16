"""
Image API endpoints - Image-first architecture

ARCHITECTURAL OVERVIEW:
Images are the PRIMARY entry point for creating content:
- POST /images creates an Image and automatically creates/associates a Photo
- First Image with a new hotpreview → Creates new Photo (becomes master)
- Subsequent Images with same hotpreview → Added to existing Photo
- Photo.hothash is generated from Image.hotpreview via SHA256

This architecture ensures:
- Image files drive the system (real data → metadata)
- Photos are created automatically, not manually
- JPEG/RAW pairs naturally share the same Photo (same visual content)
- No orphaned Photos without Image files

CRUD Operations:
- CREATE: POST /images (creates Image + auto-creates/links Photo)
- READ: GET /images, GET /images/{id}, GET /images/{id}/hotpreview
- UPDATE: Not supported - Images are immutable file records
- DELETE: Not supported - Delete via Photo API (DELETE /photos/{hothash})
"""
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
def list_images(
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of images to return"),
    image_service: ImageService = Depends(get_image_service)
):
    """Get paginated list of images with metadata"""
    try:
        return image_service.get_images(
            offset=offset,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images: {str(e)}")


@router.get("/{image_id}", response_model=ImageResponse)
def get_image_details(
    image_id: int,
    image_service: ImageService = Depends(get_image_service)
):
    """Get detailed information about a specific image"""
    try:
        return image_service.get_image_by_id(image_id)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")


@router.get("/{image_id}/hotpreview")
def get_hotpreview(
    image_id: int,
    image_service: ImageService = Depends(get_image_service)
):
    """Get hot preview image data"""
    try:
        hotpreview_data = image_service.get_image_thumbnail(image_id)
        
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


@router.post("/", response_model=ImageResponse, status_code=201)
def create_image(
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
        return image_service.create_image_with_photo(image_data)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create image: {str(e)}")

# ===== UPDATE and DELETE are NOT supported for Images =====
# 
# WHY NO UPDATE?
# Images represent immutable file records. The file data (filename, size, EXIF, 
# hotpreview) should not change after import. User-editable metadata lives in 
# the Photo model, not Image.
#
# WHY NO DELETE?
# Images should only be deleted when their parent Photo is deleted. This ensures
# referential integrity and prevents orphaned Photos. Use DELETE /photos/{hothash}
# which will cascade-delete all associated Image files.
#
# For bulk operations or updates to Photo metadata, use the Photo API:
# - PUT /photos/{hothash} - Update photo metadata (title, tags, rating, etc.)
# - DELETE /photos/{hothash} - Delete photo and all associated image files
