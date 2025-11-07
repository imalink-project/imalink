"""
PhotoTextDocument model - Structured photo storytelling documents
"""
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class PhotoTextDocument(Base, TimestampMixin):
    """
    PhotoText document storage - Blog-style photo storytelling
    
    PhotoText is a frontend TypeScript/JavaScript library for creating structured,
    photo-rich documents (blogs, albums, slideshows). Backend only stores JSON.
    
    Document Types:
    - 'general': Full-featured (headings, paragraphs, lists, images)
    - 'album': Image-focused (only images/collages, no text blocks)
    - 'slideshow': Presentation-style (single images per block)
    
    Key Design Principles:
    - Frontend-first: All processing in browser, backend is storage only
    - Content-addressed images: References photos by hothash (SHA256)
    - Complete JSON storage: Entire document structure in content field
    - Timeline viewing: Sorted by created_at for blog-style display
    - User isolation: Each user has their own documents
    
    The content field stores the complete PhotoText document structure:
    {
        "version": "1.0",
        "documentType": "general",
        "title": "Summer Vacation 2024",
        "abstract": "Our memorable trip",
        "coverImage": {"hash": "sha256_...", "alt": "Cover photo"},
        "created": "2024-07-15T10:30:00Z",
        "modified": "2024-07-20T14:22:00Z",
        "metadata": {},
        "blocks": [
            {"type": "heading", "level": 1, "content": [...]},
            {"type": "paragraph", "content": [...]},
            {"type": "image", "images": [...], "caption": "...", "layout": "auto"}
        ]
    }
    
    Image references use hothash from Photo model - same content-based addressing.
    """
    __tablename__ = "phototext_documents"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Data ownership - each document belongs to a user
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Required metadata (extracted for querying/filtering)
    title = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=False, index=True)
    
    # Complete document as JSON (entire PhotoText structure)
    content = Column(JSON, nullable=False)
    
    # Optional metadata (extracted for search/display)
    abstract = Column(Text, nullable=True)
    cover_image_hash = Column(String(64), nullable=True)  # Photo hothash (64-char SHA256)
    cover_image_alt = Column(String(500), nullable=True)
    
    # Publishing workflow
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Sharing and visibility control (Fase 1)
    visibility = Column(String(20), nullable=False, default='private', index=True)
    # Values: 'private' (only owner), 'public' (everyone including anonymous)
    
    # Version tracking
    version = Column(String(10), default='1.0', nullable=False)
    
    # Timestamps managed by TimestampMixin (created_at, updated_at)
    # created_at used for timeline sorting
    
    # Constraints
    __table_args__ = (
        # Validate document_type enum
        CheckConstraint(
            "document_type IN ('general', 'album', 'slideshow')",
            name='valid_document_type'
        ),
        # Ensure cover_image_hash and cover_image_alt are both set or both null
        CheckConstraint(
            "(cover_image_hash IS NULL AND cover_image_alt IS NULL) OR "
            "(cover_image_hash IS NOT NULL AND cover_image_alt IS NOT NULL)",
            name='valid_cover_image'
        ),
        # Validate visibility enum
        CheckConstraint(
            "visibility IN ('private', 'public')",
            name='valid_document_visibility'
        ),
    )
    
    # Relationships
    user = relationship("User", back_populates="phototext_documents")
    
    def __repr__(self):
        return f"<PhotoTextDocument(id={self.id}, type='{self.document_type}', title='{self.title[:30]}...', user_id={self.user_id})>"
    
    @property
    def is_general(self) -> bool:
        """Check if document is general type (full-featured)"""
        return self.document_type == 'general'
    
    @property
    def is_album(self) -> bool:
        """Check if document is album type (images only)"""
        return self.document_type == 'album'
    
    @property
    def is_slideshow(self) -> bool:
        """Check if document is slideshow type (single images)"""
        return self.document_type == 'slideshow'
    
    @property
    def has_cover_image(self) -> bool:
        """Check if document has a cover image"""
        return self.cover_image_hash is not None
