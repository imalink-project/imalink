"""
PhotoTextDocument Repository - Data Access Layer for PhotoTextDocument operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_

from src.models import PhotoTextDocument


class PhotoTextDocumentRepository:
    """Repository for PhotoTextDocument data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, document_id: int, user_id: Optional[int] = None) -> Optional[PhotoTextDocument]:
        """
        Get document by ID
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public documents
        - If user_id is provided: Own documents + public/authenticated documents
        """
        query = self.db.query(PhotoTextDocument).filter(PhotoTextDocument.id == document_id)
        
        # Apply visibility filtering
        if user_id is None:
            # Anonymous user: only public documents
            query = query.filter(PhotoTextDocument.visibility == 'public')
        else:
            # Authenticated user: own documents OR public OR authenticated
            # Note: 'space' treated as private in Phase 1
            query = query.filter(
                or_(
                    PhotoTextDocument.user_id == user_id,
                    PhotoTextDocument.visibility == 'public',
                    PhotoTextDocument.visibility == 'authenticated'
                )
            )
        
        return query.first()
    
    def list_documents(
        self,
        user_id: Optional[int] = None,
        document_type: Optional[str] = None,
        is_published: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[PhotoTextDocument]:
        """
        List documents with filtering and sorting
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public documents
        - If user_id is provided: Own documents + public/authenticated documents
        
        Args:
            user_id: Owner user ID (None for anonymous access)
            document_type: Filter by document type
            is_published: Filter by publication status
            limit: Page size
            offset: Page offset
            sort_by: Sort field
            sort_order: Sort direction
            
        Returns:
            List of documents
        """
        query = self.db.query(PhotoTextDocument)
        
        # Apply visibility filtering (Phase 1)
        if user_id is None:
            # Anonymous user: only public documents
            query = query.filter(PhotoTextDocument.visibility == 'public')
        else:
            # Authenticated user: own documents OR public OR authenticated
            # Note: 'space' treated as private in Phase 1
            query = query.filter(
                or_(
                    PhotoTextDocument.user_id == user_id,
                    PhotoTextDocument.visibility == 'public',
                    PhotoTextDocument.visibility == 'authenticated'
                )
            )
        
        # Apply filters
        if document_type:
            query = query.filter(PhotoTextDocument.document_type == document_type)
        
        if is_published is not None:
            query = query.filter(PhotoTextDocument.is_published == is_published)
        
        # Apply sorting
        sort_column = getattr(PhotoTextDocument, sort_by, PhotoTextDocument.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()
    
    def count_documents(
        self,
        user_id: Optional[int] = None,
        document_type: Optional[str] = None,
        is_published: Optional[bool] = None
    ) -> int:
        """
        Count documents with filters
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public documents
        - If user_id is provided: Own documents + public/authenticated documents
        """
        query = self.db.query(PhotoTextDocument)
        
        # Apply visibility filtering (Phase 1)
        if user_id is None:
            # Anonymous user: only public documents
            query = query.filter(PhotoTextDocument.visibility == 'public')
        else:
            # Authenticated user: own documents OR public OR authenticated
            # Note: 'space' treated as private in Phase 1
            query = query.filter(
                or_(
                    PhotoTextDocument.user_id == user_id,
                    PhotoTextDocument.visibility == 'public',
                    PhotoTextDocument.visibility == 'authenticated'
                )
            )
        
        # Apply filters
        if document_type:
            query = query.filter(PhotoTextDocument.document_type == document_type)
        
        if is_published is not None:
            query = query.filter(PhotoTextDocument.is_published == is_published)
        
        return query.count()
    
    def create(
        self,
        user_id: int,
        title: str,
        document_type: str,
        content: dict,
        abstract: Optional[str] = None,
        cover_image_hash: Optional[str] = None,
        cover_image_alt: Optional[str] = None,
        is_published: bool = False,
        published_at: Optional[Any] = None,
        visibility: str = 'private'
    ) -> PhotoTextDocument:
        """Create new document (user-scoped)"""
        document = PhotoTextDocument(
            user_id=user_id,
            title=title,
            document_type=document_type,
            content=content,
            abstract=abstract,
            cover_image_hash=cover_image_hash,
            cover_image_alt=cover_image_alt,
            is_published=is_published,
            published_at=published_at,
            visibility=visibility
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def update(
        self,
        document: PhotoTextDocument,
        update_data: Dict[str, Any]
    ) -> PhotoTextDocument:
        """Update existing document"""
        for key, value in update_data.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def delete(self, document: PhotoTextDocument) -> None:
        """Delete document"""
        self.db.delete(document)
        self.db.commit()
