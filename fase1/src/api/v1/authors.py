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

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AuthorResponse])
def list_authors(
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    author_service: AuthorService = Depends(get_author_service)
):
    """Get paginated list of authors"""
    try:
        return author_service.get_authors(offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve authors: {str(e)}")


@router.post("/", response_model=AuthorResponse, status_code=201)
def create_author(
    author_data: AuthorCreateRequest,
    author_service: AuthorService = Depends(get_author_service)
):
    """Create a new author"""
    try:
        return author_service.create_author(author_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateImageError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create author: {str(e)}")


@router.get("/{author_id}", response_model=AuthorResponse)
def get_author(
    author_id: int, 
    author_service: AuthorService = Depends(get_author_service)
):
    """Get specific author details"""
    try:
        return author_service.get_author_by_id(author_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve author: {str(e)}")


@router.put("/{author_id}", response_model=AuthorResponse)
def update_author(
    author_id: int,
    update_data: AuthorUpdateRequest,
    author_service: AuthorService = Depends(get_author_service)
):
    """Update author details"""
    try:
        return author_service.update_author(author_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateImageError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update author: {str(e)}")


@router.delete("/{author_id}")
def delete_author(
    author_id: int, 
    author_service: AuthorService = Depends(get_author_service)
):
    """Delete author (only if no photos are associated)"""
    try:
        author_service.delete_author(author_id)
        return create_success_response(message="Author deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete author: {str(e)}")

