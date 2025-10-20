"""
API endpoints for photo operations using Service Layer

ARCHITECTURAL NOTE:
Photos are NOT created directly via this API. They are auto-generated when
creating Images via POST /images. This ensures:
- No orphaned Photos without Image files
- Photo.hothash is derived from Image.hotpreview (content-based)
- JPEG/RAW pairs automatically share the same Photo

This API provides:
- READ: List, search, and retrieve photo metadata
- UPDATE: Edit photo metadata (title, description, tags, rating, author)
- DELETE: Remove photo and all associated image files (cascade)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query, File, UploadFile
from fastapi.responses import StreamingResponse
import io

from core.dependencies import get_photo_service, get_photo_stack_service
from services.photo_service import PhotoService
from services.photo_stack_service import PhotoStackService
from schemas.photo_schemas import (
    PhotoResponse, PhotoCreateRequest, PhotoUpdateRequest, 
    PhotoSearchRequest
)
from schemas.common import PaginatedResponse, create_success_response
from schemas.responses.photo_stack_responses import PhotoStackSummary
from core.exceptions import NotFoundError, ValidationError
from api.dependencies import get_current_active_user
from models.user import User

router = APIRouter()


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