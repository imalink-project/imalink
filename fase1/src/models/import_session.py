"""
Import session model - User's reference metadata for imported photos
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

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
    
    # Default photographer for this batch
    default_author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Relationships
    default_author = relationship("Author", back_populates="imports")
    image_files = relationship("ImageFile", back_populates="import_session", cascade="all, delete-orphan")
    
    @property
    def images_count(self) -> int:
        """Count of image files in this import session"""
        return len(self.image_files) if self.image_files else 0
    
    @property
    def index_filename(self) -> str:
        """Generate standard index filename for this session"""
        return f"session_{self.id}.json"
    
    def generate_index_data(self) -> dict:
        """Generate complete JSON index data for this import session"""
        from datetime import datetime
        
        # Basic session metadata
        session_data = {
            "import_session": {
                "id": self.id,
                "title": self.title,
                "description": self.description,
                "imported_at": self.imported_at.isoformat() if self.imported_at is not None else None,
                "default_author_id": self.default_author_id
            },
            "files": {},
            "statistics": {
                "total_files": self.images_count,
                "index_generated": datetime.utcnow().isoformat(),
                "imalink_version": "2.0"
            }
        }
        
        # Add file data for each image in this session
        if self.image_files:
            for image_file in self.image_files:
                if hasattr(image_file, 'photo') and image_file.photo:
                    hothash = image_file.photo.hothash
                    session_data["files"][hothash] = {
                        "filename": image_file.filename,
                        "file_size": image_file.file_size,
                        "taken_at": image_file.taken_at.isoformat() if image_file.taken_at else None,
                        "created_at": image_file.created_at.isoformat() if image_file.created_at else None,
                        "original_filename": image_file.original_filename,
                        "file_format": image_file.file_format,
                        "width": image_file.width,
                        "height": image_file.height,
                        "has_hotpreview": image_file.has_hotpreview
                    }
        
        return session_data
    
    def __repr__(self):
        title_info = f"'{self.title}'" if getattr(self, 'title', None) else "Untitled"
        return f"<ImportSession(id={self.id}, title={title_info}, images={self.images_count})>"