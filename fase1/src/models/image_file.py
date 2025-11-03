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
    
    ARCHITECTURE: ImageFile is an internal implementation detail
    - Represents a physical file on disk (JPEG, RAW, etc.)
    - Belongs to exactly ONE Photo (via photo_hothash)
    - NO direct API access - all operations go through Photo
    - NO user_id - access control handled via Photo.user_id
    - Cascade deletion: When Photo is deleted, ImageFiles are deleted
    
    ImageFile stores only file-specific metadata:
    - filename: Name and extension
    - file_size: Size in bytes
    - imported_time: When THIS specific file was imported
    - storage locations: Where to find the file
    
    Visual and metadata is stored in Photo:
    - Photo has hotpreview (150x150 thumbnail)
    - Photo has exif_dict (EXIF metadata from master file)
    - Photo has perceptual_hash (for similarity search)
    
    Key design principles:
    - One ImageFile per physical file
    - Immutable after creation (no UPDATE operations)
    - Delete only via Photo cascade
    """
    __tablename__ = "image_files"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File-specific information
    filename = Column(String(255), nullable=False)  # Just name + extension, e.g. "IMG_1234.jpg"
    file_size = Column(Integer)  # Size in bytes
    
    # Link to Photo (via hothash)
    photo_hothash = Column(String(64), ForeignKey('photos.hothash'), nullable=True, index=True)
    
    # Import tracking (file-level) - when THIS SPECIFIC FILE was imported
    imported_time = Column(DateTime, nullable=True)  # When this specific file was imported
    imported_info = Column(JSON, nullable=True)      # Import context and original location
    
    # Storage location tracking - where files can be found now
    local_storage_info = Column(JSON, nullable=True)   # Current local storage details
    cloud_storage_info = Column(JSON, nullable=True)   # Current cloud storage details
    
    # Relationships
    photo = relationship("Photo", back_populates="image_files", foreign_keys=[photo_hothash])
    
    def __repr__(self):
        return f"<ImageFile(id={self.id}, filename={self.filename})>"
