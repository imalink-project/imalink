"""
PhotoTextDocument Service - Business logic for PhotoText document operations
"""
from typing import Optional, List, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from src.repositories.phototext_document_repository import PhotoTextDocumentRepository
from src.repositories.photo_repository import PhotoRepository
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
        self.photo_repo = PhotoRepository(db)
    
    def _extract_photo_hashes(self, content: dict) -> Set[str]:
        """
        Extract all photo hothashes referenced in PhotoText content
        
        Args:
            content: PhotoText JSON document structure
            
        Returns:
            Set of photo hothashes
        """
        hashes = set()
        
        # Check blocks for image references
        blocks = content.get('blocks', [])
        for block in blocks:
            block_type = block.get('type')
            
            # Single image block
            if block_type == 'image' and 'hash' in block:
                hashes.add(block['hash'])
            
            # Collage block (multiple images)
            elif block_type == 'collage' and 'images' in block:
                for image in block['images']:
                    if 'hash' in image:
                        hashes.add(image['hash'])
        
        return hashes
    
    def _update_photo_visibility(self, photo_hashes: Set[str], visibility: str, user_id: int) -> None:
        """
        Update visibility for all referenced photos
        
        Args:
            photo_hashes: Set of photo hothashes to update
            visibility: New visibility level
            user_id: Owner user ID (to verify ownership)
        """
        from src.schemas.photo_schemas import PhotoUpdateRequest
        
        for hothash in photo_hashes:
            try:
                # Get photo to verify ownership
                photo = self.photo_repo.get_by_hash(hothash, user_id)
                if photo is not None:
                    current_visibility = getattr(photo, 'visibility', 'private')
                    if current_visibility != visibility:
                        # Only update if photo belongs to user and has different visibility
                        # We update to document's visibility to ensure consistency
                        update_data = PhotoUpdateRequest(visibility=visibility, rating=None, author_id=None)
                        self.photo_repo.update(hothash, update_data, user_id)
            except Exception:
                # Skip photos that don't exist or user doesn't own
                # This prevents breaking document creation/update if a photo is missing
                pass
    
    def create_document(
        self,
        document_data: PhotoTextDocumentCreate,
        user_id: int
    ) -> PhotoTextDocumentResponse:
        """
        Create new PhotoText document
        
        When a document is created, all referenced photos are automatically
        updated to match the document's visibility level to ensure consistency.
        
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
        
        # Determine visibility (default to private)
        visibility = document_data.visibility or 'private'
        
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
            published_at=published_at,
            visibility=visibility
        )
        
        # Update visibility of all referenced photos to match document
        photo_hashes = self._extract_photo_hashes(document_data.content)
        if photo_hashes:
            self._update_photo_visibility(photo_hashes, visibility, user_id)
        
        # Commit changes
        self.db.commit()
        
        return PhotoTextDocumentResponse.model_validate(document)
    
    def get_document(
        self,
        document_id: int,
        user_id: Optional[int]
    ) -> PhotoTextDocumentResponse:
        """
        Get single document by ID
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public documents
        - If user_id is provided: Own documents + public documents
        
        Args:
            document_id: Document ID
            user_id: Owner user ID (None for anonymous access)
            
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
        user_id: Optional[int],
        document_type: Optional[str] = None,
        is_published: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PhotoTextDocumentListResponse:
        """
        List documents with filtering and pagination
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public documents
        - If user_id is provided: Own documents + public documents
        
        Args:
            user_id: Owner user ID (None for anonymous access)
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
        
        When a document's visibility is updated, all referenced photos are
        automatically updated to match the document's new visibility level.
        
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
        
        # Handle visibility change
        new_visibility = None
        if document_data.visibility is not None:
            update_data['visibility'] = document_data.visibility
            new_visibility = document_data.visibility
        
        # Update document
        updated_document = self.repo.update(document, update_data)
        
        # If visibility changed, update all referenced photos
        if new_visibility is not None:
            # Use updated content if provided, otherwise use existing content
            content = document_data.content if document_data.content is not None else getattr(document, 'content', {})
            if isinstance(content, dict):
                photo_hashes = self._extract_photo_hashes(content)
                if photo_hashes:
                    self._update_photo_visibility(photo_hashes, new_visibility, user_id)
        
        # Commit changes
        self.db.commit()
        
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
