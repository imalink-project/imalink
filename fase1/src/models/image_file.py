"""
ImageFile model for storing individual file metadata
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .photo import Photo


class ImageFile(Base, TimestampMixin):
    """
    File-level image model - represents a single physical image file
    
    ARCHITECTURE: ImageFile stores only file-specific metadata
    Photos are created via POST /image-files/new-photo with visual data (hotpreview, exif_dict):
    - First ImageFile (master) provides hotpreview/exif → Creates Photo with this data
    - Photo.hothash is generated from hotpreview via SHA256
    - Subsequent ImageFiles (companions) are added via POST /image-files/add-to-photo
    - Companion files do NOT provide hotpreview/exif (already in Photo)
    
    Key design principles:
    - One record per physical file
    - File-specific data only (filename, size, storage location)
    - NO visual data (hotpreview stored in Photo)
    - NO EXIF data (exif_dict stored in Photo)
    - NO perceptual_hash (stored in Photo for similarity search)
    - Immutable after creation (no UPDATE operations)
    - Delete only via Photo cascade (no individual DELETE)
    """
    __tablename__ = "image_files"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User ownership - for multi-user system
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # File-specific information
    filename = Column(String(255), nullable=False)  # Just name + extension, e.g. "IMG_1234.jpg"
    file_size = Column(Integer)  # Size in bytes
    
    # Link to Photo (via hothash)
    photo_hothash = Column(String(64), ForeignKey('photos.hothash'), nullable=True, index=True)
    
    # Import tracking (file-level) - EXPANDED
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    imported_time = Column(DateTime, nullable=True)  # When this specific file was imported
    imported_info = Column(JSON, nullable=True)      # Import context and original location
    
    # Storage location tracking - where files can be found now
    local_storage_info = Column(JSON, nullable=True)   # Current local storage details
    cloud_storage_info = Column(JSON, nullable=True)   # Current cloud storage details
    
    # Relationships
    user = relationship("User", back_populates="image_files")
    photo = relationship("Photo", back_populates="image_files", foreign_keys=[photo_hothash])
    import_session = relationship("ImportSession", back_populates="image_files")
    
    def __repr__(self):
        return f"<ImageFile(id={self.id}, filename={self.filename})>"
