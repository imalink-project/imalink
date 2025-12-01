"""
Input channel model - User's organizational channels for photo uploads
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


class InputChannel(Base, TimestampMixin):
    """
    InputChannel - User's organizational channel for photo uploads
    
    ROLE: Passive grouping and documentation (NO file processing)
    
    PURPOSE:
    - Group photos by user-defined channels (source, purpose, event, etc.)
    - Store user's notes about the channel purpose
    - Document where user stores the original files
    - Set default photographer for the channel
    
    RELATIONSHIP TO PHOTOS:
    - REQUIRED: Every Photo MUST belong to one InputChannel
    - Grouping: All photos uploaded to same channel stay together
    - Persistence: Channels remain even if photos are deleted (history)
    
    WHAT IT IS:
    - User's organizational tool ("Canon 5D", "iPhone Photos", "Client Work 2024")
    - Reference metadata (source, storage location notes)
    - Upload timestamp (when channel received photos)
    
    WHAT IT IS NOT:
    - File processor (client handles all file operations)
    - File scanner (client detects and processes images)
    - Storage manager (just stores notes about where files are)
    
    CLIENT WORKFLOW:
    1. User selects channel for upload (or uses default)
    2. Client sends PhotoCreateSchema + input_channel_id to backend
    3. Backend creates Photo linked to InputChannel
    """
    __tablename__ = "input_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Data ownership - each input channel belongs to a user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # When the channel was created
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User's metadata
    title = Column(String(255))                         # "Canon 5D", "iPhone Photos"
    description = Column(Text)                          # User's notes/comments
    
    # System protection flag - prevents deletion by user
    # Set to True for auto-created default channel (like "Quick Channel")
    # User can edit title/description, but cannot delete the channel
    is_protected = Column(Boolean, default=False, nullable=False)
    
    # Default photographer for this channel
    default_author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="input_channels")
    default_author = relationship("Author", back_populates="input_channels")
    photos = relationship("Photo", back_populates="input_channel", lazy="selectin")
    
    @property
    def images_count(self) -> int:
        """Count of photos in this input channel"""
        return len(self.photos) if self.photos else 0
    
    @property
    def index_filename(self) -> str:
        """Generate standard index filename for this channel"""
        return f"channel_{self.id}.json"
    
    def generate_index_data(self) -> dict:
        """Generate complete JSON index data for this input channel"""
        from datetime import datetime
        
        # Basic channel metadata
        channel_data = {
            "input_channel": {
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
        
        # Add photo data for each photo in this channel
        if self.photos:
            for photo in self.photos:
                channel_data["files"][photo.hothash] = {
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
        
        return channel_data
    
    def __repr__(self):
        title_info = f"'{self.title}'" if getattr(self, 'title', None) else "Untitled"
        return f"<InputChannel(id={self.id}, title={title_info}, photos={self.images_count})>"