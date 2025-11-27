"""
Import session model - User's reference metadata for imported photos
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author
    from .user import User


class ImportSession(Base, TimestampMixin):
    """
    ImportSession - User's organizational metadata for photo imports
    
    ROLE: Passive grouping and documentation (NO file processing)
    
    PURPOSE:
    - Group photos by when they were imported (batch tracking)
    - Store user's notes about the import source
    - Document where user stores the original files
    - Set default photographer for the batch
    
    RELATIONSHIP TO PHOTOS:
    - REQUIRED: Every Photo MUST belong to one ImportSession
    - Grouping: All photos imported together share same session
    - Persistence: Sessions remain even if photos are deleted (history)
    
    WHAT IT IS:
    - User's organizational tool ("Italy vacation 2024")
    - Reference metadata (source, storage location notes)
    - Batch timestamp (when import happened)
    
    WHAT IT IS NOT:
    - File processor (client handles all file operations)
    - File scanner (client detects and processes images)
    - Storage manager (just stores notes about where files are)
    
    CLIENT WORKFLOW:
    1. User selects folder/files to import
    2. Client creates ImportSession with user's notes
    3. Client processes each file → creates PhotoCreateSchema
    4. Client sends PhotoCreateSchema + import_session_id to backend
    5. Backend creates Photo linked to ImportSession
    """
    __tablename__ = "import_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Data ownership - each import session belongs to a user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # When the import happened
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User's metadata
    title = Column(String(255))                         # "Italy Summer 2024"
    description = Column(Text)                          # User's notes/comments
    
    # System protection flag - prevents deletion by user
    # Set to True for auto-created default sessions (like "Quick Add")
    # User can edit title/description, but cannot delete the session
    is_protected = Column(Boolean, default=False, nullable=False)
    
    # Default photographer for this batch
    default_author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="import_sessions")
    default_author = relationship("Author", back_populates="imports")
    photos = relationship("Photo", back_populates="import_session", lazy="selectin")
    
    @property
    def images_count(self) -> int:
        """Count of photos in this import session"""
        return len(self.photos) if self.photos else 0
    
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
        
        # Add photo data for each photo in this session
        if self.photos:
            for photo in self.photos:
                session_data["files"][photo.hothash] = {
                    "hothash": photo.hothash,
                    "primary_filename": photo.primary_filename,
                    "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                    "created_at": photo.created_at.isoformat() if photo.created_at else None,
                    "width": photo.width,
                    "height": photo.height,
                    "rating": photo.rating,
                    "has_gps": photo.has_gps,
                    "file_count": len(photo.image_files) if photo.image_files else 0
                }
        
        return session_data
    
    def __repr__(self):
        title_info = f"'{self.title}'" if getattr(self, 'title', None) else "Untitled"
        return f"<ImportSession(id={self.id}, title={title_info}, photos={self.images_count})>"