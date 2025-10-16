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
    - File-specific data only (filename, size, EXIF, hotpreview)
    - hotpreview stored here (thumbnail for UI)
    - Photo.hothash generated from Image.hotpreview (first Image = master)
    """
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File-specific information
    filename = Column(String(255), nullable=False)  # Just name + extension, e.g. "IMG_1234.jpg"
    file_size = Column(Integer)  # Size in bytes
    
    # File-specific processing data
    exif_data = Column(LargeBinary)  # Raw EXIF data stored as binary blob
    hotpreview = Column(LargeBinary)  # Thumbnail/preview image for this file
    
    # Link to Photo (via hothash - not a FK since it's generated from hotpreview)
    photo_hothash = Column(String(64), ForeignKey('photos.hothash'), nullable=True, index=True)
    
    # Import tracking (file-level)
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    
    # Relationships
    photo = relationship("Photo", back_populates="files", foreign_keys=[photo_hothash])
    import_session = relationship("ImportSession", back_populates="images")
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename={self.filename})>"
    
    # ===== CONVENIENCE PROPERTIES =====
    
    # NOTE: hotpreview is now a Column field, not a property
    # Access directly via image.hotpreview
    
    # NOTE: photo relationship removed - Images are standalone files
    # Photo metadata accessed separately via Photo API using hothash
