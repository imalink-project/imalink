"""
ImageFile API endpoints - Simplified architecture

SIMPLIFIED ARCHITECTURE:
ImageFiles are immutable file records with only two creation endpoints:
- POST /image-files/new-photo: Creates Photo + ImageFile (with visual data)
- POST /image-files/add-to-photo: Adds ImageFile to existing Photo (file metadata only)

ImageFiles CANNOT be:
- Listed independently (use GET /photos instead)
- Retrieved individually (access via Photo.image_files)
- Updated (immutable file records)
- Deleted individually (delete via Photo cascade: DELETE /photos/{hothash})

For all photo viewing, browsing, and management operations, use the Photos API.
"""
from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_image_file_service
from api.dependencies import get_current_user
from services.image_file_service import ImageFileService
from models.user import User
from schemas.image_file_upload_schemas import (
    ImageFileNewPhotoRequest, ImageFileAddToPhotoRequest, ImageFileUploadResponse
)
from core.exceptions import NotFoundError, ValidationError, DuplicateImageError

router = APIRouter()


@router.post("/new-photo", response_model=ImageFileUploadResponse, status_code=201)
def create_image_with_new_photo(
    image_data: ImageFileNewPhotoRequest,
    image_file_service: ImageFileService = Depends(get_image_file_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create new ImageFile that will create a new Photo
    
    USE CASE: Uploading a completely new, unique photo
    - Hotpreview, exif_dict, perceptual_hash stored in Photo (visual data)
    - ImageFile stores only file metadata
    - A new Photo will always be created
    
    WORKFLOW:
    1. Validate hotpreview data
    2. Generate photo_hothash from hotpreview (SHA256)
    3. Check if Photo already exists (if yes → error 409)
    4. Create new Photo with visual data
    5. Create ImageFile with file metadata
    6. Return success response
    """
    try:
        return image_file_service.create_image_file_new_photo(image_data, current_user.id)
    except DuplicateImageError as e:
        # Photo with same hotpreview already exists
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
    image_file_service: ImageFileService = Depends(get_image_file_service),
    current_user: User = Depends(get_current_user)
):
    """
    Add new ImageFile to an existing Photo
    
    USE CASE: Adding companion files to existing photos
    - RAW file for existing JPEG photo
    - Different format/resolution of same photo
    - Additional file versions
    
    REQUIREMENTS:
    - photo_hothash must reference an existing Photo
    - NO hotpreview, exif_dict, or perceptual_hash (Photo already has these)
    
    WORKFLOW:
    1. Validate that Photo with photo_hothash exists
    2. Create ImageFile with only file metadata
    3. Return success response
    """
    try:
        return image_file_service.add_image_file_to_photo(image_data, current_user.id)
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


# ===== REMOVED ENDPOINTS =====
# 
# The following endpoints have been removed:
#
# - GET /image-files/ - Use GET /photos/ instead for browsing
# - GET /image-files/{id} - Access via Photo.image_files relationship
# - GET /image-files/{id}/hotpreview - Use GET /photos/{hothash}/hotpreview instead
# - POST /image-files/ (legacy) - Use /new-photo or /add-to-photo
# - PUT /image-files/{id} - ImageFiles are immutable
# - DELETE /image-files/{id} - Delete via Photo: DELETE /photos/{hothash}
# - GET /image-files/similar/{id} - Will be implemented on Photos API
# - PUT/GET /image-files/{id}/storage-info - May be re-added if needed
#
# This simplification reflects the architectural principle that:
# - Photos are the user-facing entity for browsing and management
# - ImageFiles are internal file records managed through Photo lifecycle
