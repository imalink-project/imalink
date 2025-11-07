"""
PhotoTextDocument API Endpoints

Provides REST API for managing PhotoText documents - structured photo storytelling
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.dependencies import get_current_user, get_current_user_optional
from src.models.user import User
from src.services.phototext_document_service import PhotoTextDocumentService
from src.database.connection import get_db
from sqlalchemy.orm import Session
from src.schemas.phototext_document import (
    PhotoTextDocumentCreate,
    PhotoTextDocumentUpdate,
    PhotoTextDocumentResponse,
    PhotoTextDocumentListResponse
)
from src.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/phototext", tags=["phototext"])


def get_phototext_service(db: Session = Depends(get_db)) -> PhotoTextDocumentService:
    """Dependency to get PhotoTextDocumentService"""
    return PhotoTextDocumentService(db)


@router.post("/", response_model=PhotoTextDocumentResponse, status_code=201)
def create_document(
    request: PhotoTextDocumentCreate,
    current_user: User = Depends(get_current_user),
    service: PhotoTextDocumentService = Depends(get_phototext_service)
):
    """
    Create a new PhotoText document.
    
    Document types:
    - general: Full-featured (headings, paragraphs, lists, images)
    - album: Image-focused (only images/collages)
    - slideshow: Presentation-style (single images per block)
    
    The content field must be a complete PhotoText JSON document structure.
    Images are referenced by hothash (SHA256 from Photo model).
    """
    try:
        document = service.create_document(
            document_data=request,
            user_id=current_user.id  # type: ignore
        )
        return document
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/", response_model=PhotoTextDocumentListResponse)
def list_documents(
    document_type: Optional[str] = Query(None, description="Filter by document type (general/album/slideshow)"),
    is_published: Optional[bool] = Query(None, description="Filter by publication status"),
    limit: int = Query(20, ge=1, le=100, description="Number of documents per page"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    sort_by: str = Query("created_at", description="Sort field (created_at, updated_at, title)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: PhotoTextDocumentService = Depends(get_phototext_service)
):
    """
    List PhotoText documents with optional filtering and sorting.
    
    Access rules (Phase 1):
    - Anonymous users: Only public documents
    - Authenticated users: Own documents + public documents
    
    Supports filtering by document_type and publication status.
    Returns paginated results with total count.
    """
    try:
        result = service.list_documents(
            user_id=current_user.id if current_user else None,  # type: ignore
            document_type=document_type,
            is_published=is_published,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}", response_model=PhotoTextDocumentResponse)
def get_document(
    document_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: PhotoTextDocumentService = Depends(get_phototext_service)
):
    """
    Get a single PhotoText document by ID.
    
    Access rules (Phase 1):
    - Anonymous users: Only public documents
    - Authenticated users: Own documents + public documents
    
    Returns the complete document including content JSON.
    """
    try:
        document = service.get_document(
            document_id=document_id,
            user_id=current_user.id if current_user else None  # type: ignore
        )
        return document
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")


@router.put("/{document_id}", response_model=PhotoTextDocumentResponse)
def update_document(
    document_id: int,
    request: PhotoTextDocumentUpdate,
    current_user: User = Depends(get_current_user),
    service: PhotoTextDocumentService = Depends(get_phototext_service)
):
    """
    Update an existing PhotoText document.
    
    All fields are optional - only provided fields will be updated.
    User can only update their own documents.
    """
    try:
        document = service.update_document(
            document_id=document_id,
            user_id=current_user.id,  # type: ignore
            document_data=request
        )
        return document
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    service: PhotoTextDocumentService = Depends(get_phototext_service)
):
    """
    Delete a PhotoText document.
    
    User can only delete their own documents.
    This is permanent and cannot be undone.
    """
    try:
        service.delete_document(
            document_id=document_id,
            user_id=current_user.id  # type: ignore
        )
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
