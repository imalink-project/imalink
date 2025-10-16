"""
API endpoints for Author management - Modernized with Service Layer
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from services.author_service import AuthorService
from schemas.responses.author_responses import (
    AuthorResponse, AuthorListResponse
)
from schemas.requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest
from schemas.common import PaginatedResponse, SingleResponse
from core.dependencies import get_author_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AuthorResponse])
async def list_authors(
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    author_service: AuthorService = Depends(get_author_service)
):
    """
    Get paginated list of authors
    """
    return author_service.get_authors(offset=offset, limit=limit)


@router.post("/", response_model=SingleResponse[AuthorResponse])
async def create_author(
    author_data: AuthorCreateRequest,
    author_service: AuthorService = Depends(get_author_service)
):
    """
    Create a new author
    """
    author = author_service.create_author(author_data)
    return SingleResponse(
        data=author,
        meta={"message": f"Author '{author.name}' created successfully"}
    )



@router.get("/{author_id}", response_model=SingleResponse[AuthorResponse])
async def get_author(
    author_id: int, 
    author_service: AuthorService = Depends(get_author_service)
):
    """
    Get specific author details
    """
    author = author_service.get_author_by_id(author_id)
    return SingleResponse(
        data=author,
        meta={"message": f"Author '{author.name}' retrieved successfully"}
    )


@router.put("/{author_id}", response_model=SingleResponse[AuthorResponse])
async def update_author(
    author_id: int,
    update_data: AuthorUpdateRequest,
    author_service: AuthorService = Depends(get_author_service)
):
    """
    Update author details
    """
    author = author_service.update_author(author_id, update_data)
    return SingleResponse(
        data=author,
        meta={"message": f"Author '{author.name}' updated successfully"}
    )


@router.delete("/{author_id}")
async def delete_author(
    author_id: int, 
    author_service: AuthorService = Depends(get_author_service)
):
    """
    Delete author (only if no images are associated)
    """
    success = author_service.delete_author(author_id)
    return {"message": "Author deleted successfully"}

