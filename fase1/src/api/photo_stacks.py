"""
PhotoStack API Endpoints

Provides REST API for managing photo stacks - groups of photos for UI organization
without modifying the underlying Photo objects.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_current_user, get_photo_stack_service
from models.user import User
from services.photo_stack_service import PhotoStackService
from schemas.requests import (
    PhotoStackCreateRequest,
    PhotoStackUpdateRequest,
    PhotoStackAddPhotoRequest
)
from schemas.responses import (
    PhotoStackListResponse,
    PhotoStackDetail,
    PhotoStackSummary,
    PhotoStackOperationResponse,
    PhotoStackPhotoResponse
)
from schemas.common import PaginatedResponse
from core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/photo-stacks", tags=["photo-stacks"])


@router.get("/", response_model=PaginatedResponse[PhotoStackSummary])
def get_photo_stacks(
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_current_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Get paginated list of photo stacks for the current user.
    
    Returns PhotoStack summaries with photo counts but not full photo lists.
    Use the detail endpoint to get photo hashes for a specific stack.
    """
    try:
        result = photo_stack_service.get_stacks(
            user_id=current_user.id,  # type: ignore
            offset=offset,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch photo stacks: {str(e)}")


@router.get("/{stack_id}", response_model=PhotoStackDetail)
def get_photo_stack(
    stack_id: int,
    current_user: User = Depends(get_current_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Get detailed information about a specific photo stack including all photo hashes.
    """
    try:
        stack = photo_stack_service.get_stack_by_id(
            stack_id=stack_id,
            user_id=current_user.id,  # type: ignore
            include_photos=True
        )
        
        return PhotoStackDetail(**stack)
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch photo stack: {str(e)}")


@router.post("/", response_model=PhotoStackOperationResponse, status_code=201)
def create_photo_stack(
    request: PhotoStackCreateRequest,
    current_user: User = Depends(get_current_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Create a new photo stack with optional initial photos.
    
    The stack can be created empty and photos added later, or with initial photos.
    If photo_hothashes are provided, they will be validated and added to the stack.
    """
    try:
        # Build stack data dict
        stack_data = {
            "cover_photo_hothash": request.cover_photo_hothash,
            "stack_type": request.stack_type
        }
        
        result = photo_stack_service.create_stack(
            stack_data=stack_data,
            user_id=current_user.id  # type: ignore
        )
        
        return PhotoStackOperationResponse(
            success=True,
            message="Photo stack created successfully",
            stack=PhotoStackDetail(**result)
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create photo stack: {str(e)}")


@router.put("/{stack_id}", response_model=PhotoStackOperationResponse)
def update_photo_stack(
    stack_id: int,
    request: PhotoStackUpdateRequest,
    current_user: User = Depends(get_current_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Update photo stack metadata (cover photo, stack type).
    
    This endpoint only updates metadata - use the photo management endpoints
    to add/remove photos from the stack.
    """
    try:
        # Build update data dict, only including non-None values
        update_data = {}
        if request.cover_photo_hothash is not None:
            update_data["cover_photo_hothash"] = request.cover_photo_hothash
        if request.stack_type is not None:
            update_data["stack_type"] = request.stack_type
        
        result = photo_stack_service.update_stack(
            stack_id=stack_id,
            update_data=update_data,
            user_id=current_user.id  # type: ignore
        )
        
        return PhotoStackOperationResponse(
            success=True,
            message="Photo stack updated successfully",
            stack=PhotoStackDetail(**result)
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update photo stack: {str(e)}")


@router.delete("/{stack_id}", response_model=PhotoStackOperationResponse)
def delete_photo_stack(
    stack_id: int,
    current_user: User = Depends(get_current_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Delete a photo stack.
    
    This removes the stack and all photo memberships but does not delete
    the actual Photo objects - they remain in the system unchanged.
    """
    try:
        photo_stack_service.delete_stack(
            stack_id=stack_id,
            user_id=current_user.id  # type: ignore
        )
        
        return PhotoStackOperationResponse(
            success=True,
            message="Photo stack deleted successfully",
            stack=None
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete photo stack: {str(e)}")


@router.post("/{stack_id}/photo", response_model=PhotoStackPhotoResponse)
def add_photo_to_stack(
    stack_id: int,
    request: PhotoStackAddPhotoRequest,
    current_user: User = Depends(get_current_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Add a single photo to a photo stack.
    
    If the photo is already in another stack, it will be removed from that stack first.
    Each photo can only belong to one stack at a time.
    """
    try:
        result = photo_stack_service.add_photo_to_stack(
            stack_id=stack_id,
            photo_hothash=request.photo_hothash,
            user_id=current_user.id  # type: ignore
        )
        
        return PhotoStackPhotoResponse(
            success=True,
            message="Photo added to stack successfully",
            stack=PhotoStackDetail(**result['stack'])
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add photo to stack: {str(e)}")


@router.delete("/{stack_id}/photo/{photo_hothash}", response_model=PhotoStackPhotoResponse)
def remove_photo_from_stack(
    stack_id: int,
    photo_hothash: str,
    current_user: User = Depends(get_current_user),
    photo_stack_service: PhotoStackService = Depends(get_photo_stack_service)
):
    """
    Remove a single photo from a photo stack.
    
    Stack remains even if empty - use DELETE /{stack_id} to delete empty stacks manually.
    """
    try:
        result = photo_stack_service.remove_photo_from_stack(
            stack_id=stack_id,
            photo_hothash=photo_hothash,
            user_id=current_user.id  # type: ignore
        )
        
        return PhotoStackPhotoResponse(
            success=True,
            message="Photo removed from stack successfully",
            stack=PhotoStackDetail(**result['stack'])
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove photo from stack: {str(e)}")


# Note: Moved to /photos/{hash}/stack endpoint in photos.py API 
# Since this is about getting a photo's stack, not about stack operations