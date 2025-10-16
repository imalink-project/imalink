"""
Import session model - User's reference metadata for imported photos
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author


class ImportSession(Base, TimestampMixin):
    """
    User's reference metadata for a batch of imported photos.
    
    This is NOT a file processor - it's a simple container for:
    - User's notes about the import ("Italy vacation 2024")
    - When the import happened
    - Who took the photos (default author)
    - Where the client stored the files
    
    All file operations are handled by the client application.
    """
    __tablename__ = "import_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # When the import happened
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User's metadata
    title = Column(String(255))                         # "Italy Summer 2024"
    description = Column(Text)                          # User's notes/comments
    storage_location = Column(Text)                     # Where client stored files (e.g., "D:/photos/2024/italy")
    
    # Default photographer for this batch
    default_author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Relationships
    default_author = relationship("Author", back_populates="imports")
    image_files = relationship("ImageFile", back_populates="import_session", cascade="all, delete-orphan")
    
    @property
    def images_count(self) -> int:
        """Count of image files in this import session"""
        return len(self.image_files) if self.image_files else 0
    
    def __repr__(self):
        title_info = f"'{self.title}'" if getattr(self, 'title', None) else "Untitled"
        return f"<ImportSession(id={self.id}, title={title_info}, images={self.images_count})>"