"""
Tags API endpoints
"""
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from database.connection import get_db
from services.tag_service import TagService
from schemas.tag_schemas import (
    TagListResponse, TagAutocompleteResponse, TagUpdate,
    DeleteTagResponse, RenameTagResponse
)
from models.user import User
from api.dependencies import get_current_user
from core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/tags", tags=["tags"])
logger = logging.getLogger(__name__)


@router.get("", response_model=TagListResponse)
async def list_tags(
    sort_by: str = Query('name', regex='^(name|count|created_at)$'),
    order: str = Query('asc', regex='^(asc|desc)$'),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all tags for current user with photo counts
    
    **Sort options:**
    - `name`: Alphabetical order
    - `count`: By number of photos (most used first)
    - `created_at`: By creation date
    
    **Order:**
    - `asc`: Ascending
    - `desc`: Descending
    """
    try:
        tag_service = TagService(db)
        return tag_service.get_all_tags(getattr(current_user, 'id'), sort_by, order)
    except Exception as e:
        logger.error(f"Failed to list tags: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tags: {str(e)}")


@router.get("/autocomplete", response_model=TagAutocompleteResponse)
async def autocomplete_tags(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tag suggestions for autocomplete (prefix matching)
    
    Results are ordered by photo count (most used first).
    """
    try:
        tag_service = TagService(db)
        return tag_service.autocomplete(q, getattr(current_user, 'id'), limit)
    except Exception as e:
        logger.error(f"Failed to autocomplete tags: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to autocomplete tags: {str(e)}")


@router.put("/{tag_id}", response_model=RenameTagResponse)
async def rename_tag(
    tag_id: int,
    update_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rename a tag (applies to all photos using it)
    
    Returns 404 if tag not found or doesn't belong to user.
    Returns 409 if new name already exists for user.
    """
    try:
        tag_service = TagService(db)
        return tag_service.rename_tag(tag_id, update_data.new_name, getattr(current_user, 'id'))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to rename tag: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rename tag: {str(e)}")


@router.delete("/{tag_id}", response_model=DeleteTagResponse)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a tag completely (removes from all photos)
    
    **Warning:** This action cannot be undone.
    The tag will be removed from all photos that have it.
    
    Returns 404 if tag not found or doesn't belong to user.
    """
    try:
        tag_service = TagService(db)
        return tag_service.delete_tag(tag_id, getattr(current_user, 'id'))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete tag: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete tag: {str(e)}")
