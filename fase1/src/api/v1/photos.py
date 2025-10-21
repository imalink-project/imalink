"""
API endpoints for photo operations using Service Layer

ARCHITECTURAL NOTE (UPDATED):
Photos are created via POST /photos/new-photo which creates both Photo + ImageFile.
Additional files can be added to existing Photos via POST /photos/{hothash}/files.
This ensures:
- Photo-centric API (100% of operations through /photos)
- No orphaned Photos without Image files
- Photo.hothash is derived from Image.hotpreview (content-based)
- JPEG/RAW pairs automatically share the same Photo

This API provides:
- CREATE: Upload new photos (POST /new-photo) and add files (POST /{hothash}/files)
- READ: List, search, and retrieve photo metadata
- UPDATE: Edit photo metadata (title, description, tags, rating, author)
- DELETE: Remove photo and all associated image files (cascade)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query, File, UploadFile
from fastapi.responses import StreamingResponse
import io
import logging

from core.dependencies import get_photo_service, get_photo_stack_service
from services.photo_service import PhotoService
from services.photo_stack_service import PhotoStackService
from schemas.photo_schemas import (
    PhotoResponse, PhotoCreateRequest, PhotoUpdateRequest, 
    PhotoSearchRequest
)
from schemas.image_file_upload_schemas import (
    ImageFileNewPhotoRequest, ImageFileAddToPhotoRequest, ImageFileUploadResponse
)
from schemas.common import PaginatedResponse, create_success_response
from schemas.responses.photo_stack_responses import PhotoStackSummary
from core.exceptions import NotFoundError, ValidationError, DuplicateImageError
from api.dependencies import get_current_active_user
from models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=PaginatedResponse[PhotoResponse])
def list_photos(
    offset: int = Query(0, ge=0, description="Number of photos to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of photos to return"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get paginated list of photos with metadata (user-scoped)"""
    try:
        return photo_service.get_photos(
            offset=offset,
            limit=limit,
            author_id=author_id,
            user_id=getattr(current_user, 'id')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve photos: {str(e)}")


@router.post("/search", response_model=PaginatedResponse[PhotoResponse])
def search_photos(
    search_request: PhotoSearchRequest,
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Search photos with advanced filtering (user-scoped)"""
    try:
        return photo_service.search_photos(search_request, getattr(current_user, 'id'))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search photos: {str(e)}")


@router.post("/new-photo", response_model=ImageFileUploadResponse, status_code=201)
def create_photo_with_file(
    image_data: ImageFileNewPhotoRequest,
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Create new Photo with initial ImageFile
    
    USE CASE: Uploading a completely new, unique photo
    - Hotpreview and exif_dict stored in Photo (visual data)
    - ImageFile stores only file metadata
    - A new Photo will always be created
    
    WORKFLOW:
    1. Validate hotpreview data
    2. Generate photo_hothash from hotpreview (SHA256)
    3. Check if Photo already exists (if yes → error 409)
    4. Create new Photo with visual data
    5. Create ImageFile with file metadata
    6. Return success response
    
    Returns:
        ImageFileUploadResponse with photo_created=True
    """
    try:
        logger.debug(f"Creating new photo for user {getattr(current_user, 'id')}")
        logger.debug(f"Request data: filename={image_data.filename}, has_hotpreview={bool(image_data.hotpreview)}, "
                    f"file_size={image_data.file_size}, has_exif={bool(image_data.exif_dict)}")
        
        return photo_service.create_photo_with_file(image_data, getattr(current_user, 'id'))
    except DuplicateImageError as e:
        # Photo with same hotpreview already exists
        logger.warning(f"Duplicate photo upload attempt by user {getattr(current_user, 'id')}: {str(e)}")
        raise HTTPException(
            status_code=409, 
            detail=f"Photo with this image already exists. Use POST /photos/{{hothash}}/files to add companion files. {str(e)}"
        )
    except ValidationError as e:
        logger.error(f"Validation error creating photo: {str(e)}")
        logger.error(f"Request data details - filename: {image_data.filename}, "
                    f"hotpreview_size: {len(image_data.hotpreview) if image_data.hotpreview else 0}, "
                    f"file_size: {image_data.file_size}, "
                    f"has_exif: {bool(image_data.exif_dict)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating photo with file: {str(e)}", exc_info=True)
        logger.error(f"Request data - filename: {image_data.filename if hasattr(image_data, 'filename') else 'N/A'}, "
                    f"hotpreview_present: {bool(getattr(image_data, 'hotpreview', None))}, "
                    f"user_id: {getattr(current_user, 'id')}")
        raise HTTPException(status_code=500, detail=f"Failed to create photo with file: {str(e)}")


@router.post("/{hothash}/files", response_model=ImageFileUploadResponse, status_code=201)
def add_file_to_photo(
    hothash: str,
    image_data: ImageFileAddToPhotoRequest,
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Add new ImageFile to an existing Photo
    
    USE CASE: Adding companion files to existing photos
    - RAW file for existing JPEG photo
    - Different format/resolution of same photo
    - Additional file versions
    
    REQUIREMENTS:
    - Photo with {hothash} must exist and belong to user
    - NO hotpreview or exif_dict (Photo already has these)
    
    WORKFLOW:
    1. Validate that Photo with hothash exists
    2. Create ImageFile with only file metadata
    3. Return success response
    
    Returns:
        ImageFileUploadResponse with photo_created=False
    """
    try:
        logger.debug(f"Adding file to existing photo {hothash} for user {getattr(current_user, 'id')}")
        logger.debug(f"Request data: filename={image_data.filename}, file_size={image_data.file_size}")
        
        return photo_service.add_file_to_photo(hothash, image_data, getattr(current_user, 'id'))
    except NotFoundError as e:
        # Photo with provided hothash doesn't exist
        logger.warning(f"Attempt to add file to non-existent photo {hothash} by user {getattr(current_user, 'id')}")
        raise HTTPException(
            status_code=404,
            detail=f"Photo with hothash '{hothash}' not found. Use POST /photos/new-photo to create new photo."
        )
    except ValidationError as e:
        logger.error(f"Validation error adding file to photo {hothash}: {str(e)}")
        logger.error(f"Request data - filename: {image_data.filename}, file_size: {image_data.file_size}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error adding file to photo {hothash}: {str(e)}", exc_info=True)
        logger.error(f"Request data - filename: {image_data.filename if hasattr(image_data, 'filename') else 'N/A'}, "
                    f"hothash: {hothash}, user_id: {getattr(current_user, 'id')}")
        raise HTTPException(status_code=500, detail=f"Failed to add file to photo: {str(e)}")


@router.get("/{hothash}", response_model=PhotoResponse)
def get_photo(
    hothash: str,
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get single photo by hash (user-scoped)"""
    try:
        return photo_service.get_photo_by_hash(hothash, getattr(current_user, 'id'))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve photo: {str(e)}")


@router.put("/{hothash}", response_model=PhotoResponse)
def update_photo(
    hothash: str,
    photo_data: PhotoUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Update existing photo (user-scoped)"""
    try:
        return photo_service.update_photo(hothash, photo_data, getattr(current_user, 'id'))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update photo: {str(e)}")


@router.delete("/{hothash}")
def delete_photo(
    hothash: str,
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Delete photo and all associated image files (user-scoped)"""
    try:
        photo_service.delete_photo(hothash, getattr(current_user, 'id'))
        return create_success_response(message="Photo deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")


@router.get("/{hothash}/hotpreview")
def get_hotpreview(
    hothash: str,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get hotpreview image for photo"""
    try:
        hotpreview_data = photo_service.get_hotpreview(hothash)
        
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
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve hotpreview: {str(e)}")


@router.put("/{hothash}/coldpreview")
async def upload_coldpreview(
    hothash: str,
    file: UploadFile = File(..., description="Coldpreview image file"),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Upload or update coldpreview for photo"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await file.read()
        
        # Validate that content is not empty
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Validate that it's a valid image by trying to open it
        from PIL import Image as PILImage
        import io
        try:
            test_img = PILImage.open(io.BytesIO(file_content))
            test_img.verify()  # Check if it's a valid image
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        result = photo_service.upload_coldpreview(hothash, file_content)
        return create_success_response(
            message="Coldpreview uploaded successfully",
            data=result
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload coldpreview: {str(e)}")


@router.get("/{hothash}/coldpreview")
def get_coldpreview(
    hothash: str,
    width: Optional[int] = Query(None, ge=100, le=2000, description="Target width for dynamic resizing"),
    height: Optional[int] = Query(None, ge=100, le=2000, description="Target height for dynamic resizing"),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get coldpreview image for photo with optional resizing"""
    try:
        coldpreview_data = photo_service.get_coldpreview(hothash, width=width, height=height)
        
        if coldpreview_data:
            return StreamingResponse(
                io.BytesIO(coldpreview_data),
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename=coldpreview_{hothash[:8]}.jpg",
                    "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Coldpreview not found")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve coldpreview: {str(e)}")


@router.delete("/{hothash}/coldpreview")
def delete_coldpreview(
    hothash: str,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Delete coldpreview for photo"""
    try:
        photo_service.delete_coldpreview(hothash)
        return create_success_response(message="Coldpreview deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete coldpreview: {str(e)}")


# Additional utility endpoints

@router.get("/{hothash}/stack", response_model=Optional[PhotoStackSummary])
def get_photo_stack(
    hothash: str,
    current_user: User = Depends(get_current_active_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Get the stack containing this photo.
    
    Returns the stack if photo belongs to one, null otherwise.
    With one-to-many relationship, each photo can belong to at most one stack.
    """
    try:
        stack = photo_stack_service.get_photo_stack(
            photo_hothash=hothash,
            user_id=getattr(current_user, 'id')
        )
        
        return stack
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stack for photo: {str(e)}")