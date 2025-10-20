"""
API endpoints for Author management - Modernized with Service Layer
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from services.author_service import AuthorService
from schemas.responses.author_responses import (
    AuthorResponse, AuthorListResponse
)
from schemas.requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest
from schemas.common import PaginatedResponse, SingleResponse, create_success_response
from core.dependencies import get_author_service
from core.exceptions import NotFoundError, ValidationError, DuplicateImageError
from api.dependencies import get_current_user
from models.user import User

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AuthorResponse])
def list_authors(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    author_service: AuthorService = Depends(get_author_service),
    current_user: User = Depends(get_current_user)
):
    """List all authors for the current user with pagination"""
    return author_service.get_authors(user_id=current_user.id, offset=offset, limit=limit)


@router.post("/", response_model=AuthorResponse, status_code=201)
def create_author(
    author_data: AuthorCreateRequest,
    author_service: AuthorService = Depends(get_author_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new author"""
    try:
        return author_service.create_author(author_data, user_id=current_user.id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateImageError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create author: {str(e)}")


@router.get("/{author_id}", response_model=AuthorResponse)
def get_author(
    author_id: int, 
    author_service: AuthorService = Depends(get_author_service),
    current_user: User = Depends(get_current_user)
):
    """Get author by ID"""
    try:
        return author_service.get_author_by_id(author_id, user_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get author: {str(e)}")


@router.put("/{author_id}", response_model=AuthorResponse)
def update_author(
    author_id: int,
    update_data: AuthorUpdateRequest,
    author_service: AuthorService = Depends(get_author_service),
    current_user: User = Depends(get_current_user)
):
    """Update an existing author"""
    try:
        return author_service.update_author(author_id, update_data, user_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update author: {str(e)}")


@router.delete("/{author_id}")
def delete_author(
    author_id: int,
    author_service: AuthorService = Depends(get_author_service),
    current_user: User = Depends(get_current_user)
):
    """Delete an author"""
    try:
        author_service.delete_author(author_id, user_id=current_user.id)
        return create_success_response("Author deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))  # Author has images
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete author: {str(e)}")

