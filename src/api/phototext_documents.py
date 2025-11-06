"""
PhotoTextDocument API Endpoints

Provides REST API for managing PhotoText documents - structured photo storytelling
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.dependencies import get_current_user
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
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    sort_by: str = Query("created_at", description="Sort field (created_at/updated_at/title)"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_user),
    service: PhotoTextDocumentService = Depends(get_phototext_service)
):
    """
    List PhotoText documents for the current user.
    
    Supports filtering by:
    - document_type: 'general', 'album', or 'slideshow'
    - is_published: true/false
    
    Results can be sorted by:
    - created_at (default): Timeline/blog order
    - updated_at: Recently modified
    - title: Alphabetical
    """
    try:
        # Validate sort parameters
        if sort_by not in ['created_at', 'updated_at', 'title']:
            raise ValidationError(f"Invalid sort_by: {sort_by}")
        if sort_order not in ['asc', 'desc']:
            raise ValidationError(f"Invalid sort_order: {sort_order}")
        
        # Validate document_type if provided
        if document_type and document_type not in ['general', 'album', 'slideshow']:
            raise ValidationError(f"Invalid document_type: {document_type}")
        
        documents = service.list_documents(
            user_id=current_user.id,  # type: ignore
            document_type=document_type,
            is_published=is_published,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return documents
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}", response_model=PhotoTextDocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    service: PhotoTextDocumentService = Depends(get_phototext_service)
):
    """
    Get a single PhotoText document by ID.
    
    Returns the complete document including content JSON.
    User can only access their own documents.
    """
    try:
        document = service.get_document(
            document_id=document_id,
            user_id=current_user.id  # type: ignore
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
