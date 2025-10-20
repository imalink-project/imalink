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
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import FileResponse

from core.dependencies import get_image_file_service
from services.image_file_service import ImageFileService
from schemas.image_file_schemas import (
    ImageFileResponse, ImageFileCreateRequest, ImageFileUpdateRequest, StorageInfoUpdateRequest
)
from schemas.image_file_upload_schemas import (
    ImageFileNewPhotoRequest, ImageFileAddToPhotoRequest, ImageFileUploadResponse
)
from schemas.common import PaginatedResponse, create_success_response
from core.exceptions import NotFoundError, ValidationError, DuplicateImageError

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ImageFileResponse])
def list_images(
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of images to return"),
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """Get paginated list of images with metadata"""
    try:
        return image_file_service.get_image_files(
            offset=offset,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images: {str(e)}")


@router.get("/{image_id}", response_model=ImageFileResponse)
def get_image_details(
    image_id: int,
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """Get detailed information about a specific image"""
    try:
        return image_file_service.get_image_file_by_id(image_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")


@router.get("/{image_id}/hotpreview")
def get_hotpreview(
    image_id: int,
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """Get hot preview image data"""
    try:
        hotpreview_data = image_file_service.get_image_hotpreview(image_id)
        
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
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve hot preview: {str(e)}")


@router.post("/", response_model=ImageFileResponse, status_code=201)
def create_image(
    image_data: ImageFileCreateRequest,
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """
    Create new Image with automatic Photo creation/association
    
    NEW ARCHITECTURE: Images drive Photo creation
    - hotpreview is REQUIRED in the request (hotpreview binary data)
    - photo_hothash is automatically generated from hotpreview via SHA256
    - If Photo with this hothash exists: Image is added to existing Photo
    - If Photo doesn't exist: New Photo is created automatically
    
    First Image with new hotpreview = Creates new Photo (master)
    Subsequent Images with same hotpreview = Added to existing Photo
    """
    try:
        return image_file_service.create_image_file_with_photo(image_data)
    except DuplicateImageError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create image: {str(e)}")

# ===== SIMILARITY SEARCH =====

@router.get("/similar/{image_id}", response_model=List[ImageFileResponse])
async def find_similar_images(
    image_id: int,
    threshold: int = Query(5, ge=0, le=16, description="Hamming distance threshold (0=identical, 16=very different)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of similar images to return"),
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """
    Find images similar to the given image using perceptual hash
    
    - **image_id**: ID of the reference image
    - **threshold**: Hamming distance threshold (0-16, lower = more similar)
    - **limit**: Maximum number of results to return
    
    Returns images sorted by similarity (most similar first)
    """
    try:
        similar_images = image_file_service.find_similar_images(image_id, threshold, limit)
        return similar_images
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar images: {str(e)}")


@router.put("/{image_file_id}/storage-info")
def update_storage_info(
    image_file_id: int,
    storage_info: 'StorageInfoUpdateRequest',
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """Update storage information for an image file"""
    try:
        return image_file_service.update_storage_info(image_file_id, storage_info)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating storage info: {str(e)}")


@router.get("/{image_file_id}/storage-info")
def get_storage_info(
    image_file_id: int,
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """Get storage information for an image file"""
    try:
        return image_file_service.get_storage_info(image_file_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving storage info: {str(e)}")


# ===== NEW CLEAR UPLOAD ENDPOINTS =====

@router.post("/new-photo", response_model=ImageFileUploadResponse, status_code=201)
def create_image_with_new_photo(
    image_data: ImageFileNewPhotoRequest,
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """
    Create new ImageFile that will create a new Photo
    
    USE CASE: Uploading a completely new, unique photo
    - Hotpreview is REQUIRED and will generate the Photo's hothash
    - A new Photo will always be created
    - This ImageFile becomes the master file for the new Photo
    
    WORKFLOW:
    1. Validate hotpreview data
    2. Generate photo_hothash from hotpreview (SHA256)
    3. Create new Photo with generated hothash
    4. Create ImageFile linked to new Photo
    5. Return success with Photo and ImageFile details
    """
    try:
        return image_file_service.create_image_file_new_photo(image_data)
    except DuplicateImageError as e:
        # This means a Photo with same hotpreview already exists
        raise HTTPException(
            status_code=409, 
            detail=f"Photo with this image already exists. Use /add-to-photo endpoint instead. {str(e)}"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create image with new photo: {str(e)}")


@router.post("/add-to-photo", response_model=ImageFileUploadResponse, status_code=201)
def add_image_to_existing_photo(
    image_data: ImageFileAddToPhotoRequest,
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """
    Add new ImageFile to an existing Photo
    
    USE CASE: Adding companion files to existing photos
    - RAW file for existing JPEG photo
    - Different format/resolution of same photo
    - Additional file versions
    
    REQUIREMENTS:
    - photo_hothash must reference an existing Photo
    - NO hotpreview needed (Photo already has visual representation)
    - NO perceptual_hash needed (not used for companion files)
    
    WORKFLOW:
    1. Validate that Photo with photo_hothash exists
    2. Create ImageFile linked to existing Photo
    3. Return success with Photo and ImageFile details
    """
    try:
        return image_file_service.add_image_file_to_photo(image_data)
    except NotFoundError as e:
        # Photo with provided hothash doesn't exist
        raise HTTPException(
            status_code=404,
            detail=f"Photo with hothash '{image_data.photo_hothash}' not found. Use /new-photo endpoint to create new photo."
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add image to existing photo: {str(e)}")


# ===== LEGACY UPLOAD ENDPOINT (TO BE DEPRECATED) =====

@router.post("/", response_model=ImageFileResponse, status_code=201)
def create_image_legacy(
    image_data: ImageFileCreateRequest,
    image_file_service: ImageFileService = Depends(get_image_file_service)
):
    """
    LEGACY: Create new Image with automatic Photo creation/association
    
    ⚠️ DEPRECATED: This endpoint has unclear logic for new vs existing photos.
    Use the new endpoints instead:
    - POST /image-files/new-photo - For creating new photos
    - POST /image-files/add-to-photo - For adding files to existing photos
    
    This endpoint will determine behavior based on whether a Photo with the
    same hotpreview already exists, which can be confusing for API clients.
    """
    try:
        return image_file_service.create_image_file_with_photo(image_data)
    except DuplicateImageError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
