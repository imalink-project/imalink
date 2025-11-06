"""
PhotoTextDocument Service - Business logic for PhotoText document operations
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from src.repositories.phototext_document_repository import PhotoTextDocumentRepository
from src.schemas.phototext_document import (
    PhotoTextDocumentCreate,
    PhotoTextDocumentUpdate,
    PhotoTextDocumentResponse,
    PhotoTextDocumentSummary,
    PhotoTextDocumentListResponse
)
from src.core.exceptions import NotFoundError, ValidationError
from src.models import PhotoTextDocument


class PhotoTextDocumentService:
    """Service layer for PhotoTextDocument operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = PhotoTextDocumentRepository(db)
    
    def create_document(
        self,
        document_data: PhotoTextDocumentCreate,
        user_id: int
    ) -> PhotoTextDocumentResponse:
        """
        Create new PhotoText document
        
        Args:
            document_data: Document creation request
            user_id: Owner user ID
            
        Returns:
            Created document response
        """
        # Extract cover image fields if present
        cover_image_hash = None
        cover_image_alt = None
        if document_data.cover_image:
            cover_image_hash = document_data.cover_image.hash
            cover_image_alt = document_data.cover_image.alt
        
        # Set published_at if document is being published
        published_at = datetime.utcnow() if document_data.is_published else None
        
        # Create document
        document = self.repo.create(
            user_id=user_id,
            title=document_data.title,
            document_type=document_data.document_type.value,
            content=document_data.content,
            abstract=document_data.abstract,
            cover_image_hash=cover_image_hash,
            cover_image_alt=cover_image_alt,
            is_published=document_data.is_published,
            published_at=published_at
        )
        
        return PhotoTextDocumentResponse.model_validate(document)
    
    def get_document(
        self,
        document_id: int,
        user_id: int
    ) -> PhotoTextDocumentResponse:
        """
        Get single document by ID (user-scoped)
        
        Args:
            document_id: Document ID
            user_id: Owner user ID
            
        Returns:
            Document response
            
        Raises:
            NotFoundError: If document not found or access denied
        """
        document = self.repo.get_by_id(document_id, user_id)
        if not document:
            raise NotFoundError("PhotoTextDocument", str(document_id))
        
        return PhotoTextDocumentResponse.model_validate(document)
    
    def list_documents(
        self,
        user_id: int,
        document_type: Optional[str] = None,
        is_published: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PhotoTextDocumentListResponse:
        """
        List documents with filtering and pagination (user-scoped)
        
        Args:
            user_id: Owner user ID
            document_type: Filter by document type ('general', 'album', 'slideshow')
            is_published: Filter by publication status
            limit: Page size
            offset: Page offset
            sort_by: Sort field ('created_at', 'updated_at', 'title')
            sort_order: Sort direction ('asc', 'desc')
            
        Returns:
            Paginated document list
        """
        # Get documents from repository
        documents = self.repo.list_documents(
            user_id=user_id,
            document_type=document_type,
            is_published=is_published,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Count total documents
        total = self.repo.count_documents(
            user_id=user_id,
            document_type=document_type,
            is_published=is_published
        )
        
        # Convert to summary models
        summaries = [PhotoTextDocumentSummary.model_validate(doc) for doc in documents]
        
        return PhotoTextDocumentListResponse(
            documents=summaries,
            total=total,
            limit=limit,
            offset=offset
        )
    
    def update_document(
        self,
        document_id: int,
        user_id: int,
        document_data: PhotoTextDocumentUpdate
    ) -> PhotoTextDocumentResponse:
        """
        Update existing document (user-scoped)
        
        Args:
            document_id: Document ID
            user_id: Owner user ID
            document_data: Update request
            
        Returns:
            Updated document response
            
        Raises:
            NotFoundError: If document not found or access denied
        """
        # Get existing document
        document = self.repo.get_by_id(document_id, user_id)
        if not document:
            raise NotFoundError("PhotoTextDocument", str(document_id))
        
        # Prepare update data
        update_data = {}
        
        if document_data.title is not None:
            update_data['title'] = document_data.title
        
        if document_data.content is not None:
            update_data['content'] = document_data.content
        
        if document_data.abstract is not None:
            update_data['abstract'] = document_data.abstract
        
        if document_data.cover_image is not None:
            update_data['cover_image_hash'] = document_data.cover_image.hash
            update_data['cover_image_alt'] = document_data.cover_image.alt
        
        # Handle publication status change
        if document_data.is_published is not None:
            update_data['is_published'] = document_data.is_published
            
            # Set published_at when publishing for the first time
            if document_data.is_published and not bool(document.is_published):
                update_data['published_at'] = datetime.utcnow()
            # Clear published_at when unpublishing
            elif not document_data.is_published and bool(document.is_published):
                update_data['published_at'] = None
        
        # Update document
        updated_document = self.repo.update(document, update_data)
        
        return PhotoTextDocumentResponse.model_validate(updated_document)
    
    def delete_document(
        self,
        document_id: int,
        user_id: int
    ) -> None:
        """
        Delete document (user-scoped)
        
        Args:
            document_id: Document ID
            user_id: Owner user ID
            
        Raises:
            NotFoundError: If document not found or access denied
        """
        # Get existing document
        document = self.repo.get_by_id(document_id, user_id)
        if not document:
            raise NotFoundError("PhotoTextDocument", str(document_id))
        
        # Delete document
        self.repo.delete(document)
