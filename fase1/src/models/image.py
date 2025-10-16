"""
Image model for storing individual file metadata
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .photo import Photo


class Image(Base, TimestampMixin):
    """
    File-level image model - represents a single physical image file
    
    This model handles individual files (JPEG, RAW, etc.) and links to 
    the Photo model which contains the shared content metadata.
    
    Key design principles:
    - One record per physical file
    - File-specific data only (filename, size, rotation, EXIF)
    - Links to Photo via hothash for shared content metadata
    """
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File-specific information
    filename = Column(String(255), nullable=False)  # Just name + extension, e.g. "IMG_1234.jpg"
    file_size = Column(Integer)  # Size in bytes
    
    # File-specific processing data
    exif_data = Column(LargeBinary)  # Raw EXIF data stored as binary blob
    
    # Link to shared photo content (the "concept" of this photo)
    hothash = Column(String(64), ForeignKey('photos.hothash'), nullable=False, index=True)
    
    # Import tracking (file-level)
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    
    # Relationships
    photo = relationship("Photo", back_populates="files")
    import_session = relationship("ImportSession", back_populates="images")
    
    def __repr__(self):
        photo_preview = getattr(self, 'hothash', 'Unknown')
        if isinstance(photo_preview, str) and len(photo_preview) > 8:
            photo_preview = photo_preview[:8] + '...'
        return f"<Image(id={self.id}, filename={self.filename}, hothash={photo_preview})>"
    
    # ===== CONVENIENCE PROPERTIES =====
    
    @property
    def hotpreview(self) -> Optional[bytes]:
        """
        Get hotpreview from associated Photo.
        Convenient access to preview without needing to load Photo explicitly.
        
        Returns:
            Binary hotpreview data from Photo, or None if no Photo loaded
        """
        return self.photo.hotpreview if self.photo else None
    
    @property 
    def photo_metadata(self) -> dict:
        """
        Get key metadata from associated Photo for quick access.
        
        Returns:
            Dictionary with commonly needed Photo metadata
        """
        if not self.photo:
            return {}
        
        return {
            'title': self.photo.title,
            'width': self.photo.width,
            'height': self.photo.height,
            'taken_at': self.photo.taken_at,
            'has_gps': self.photo.has_gps,
            'rating': self.photo.rating,
        }