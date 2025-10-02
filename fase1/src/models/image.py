"""
Image model for storing photo metadata
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author


class Image(Base, TimestampMixin):
    """
    Core image model - represents a single image/photo
    """
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Unique identifier based on perceptual hash
    image_hash = Column(String(64), unique=True, index=True, nullable=False)
    
    # File information  
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)  # Size in bytes
    file_format = Column(String(10))  # jpg, png, raw, etc.
    
    # RAW+JPEG pairing support
    # RAW companion info computed dynamically from filesystem when needed
    # This eliminates data redundancy and sync issues
    
    # Timestamps
    taken_at = Column(DateTime)  # When photo was actually taken (from EXIF)
    
    # Image dimensions
    width = Column(Integer)
    height = Column(Integer)
    
    # Thumbnail stored as binary data
    thumbnail = Column(LargeBinary)
    
    # EXIF data stored as binary blob
    exif_data = Column(LargeBinary)
    
    # GPS coordinates (if available)
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    
    # User-added metadata (for future use)
    title = Column(String(255))
    description = Column(Text)
    tags = Column(Text)  # JSON string for now, can be separate table later
    rating = Column(Integer)  # 1-5 stars
    
    # User rotation (0=0°, 1=90°, 2=180°, 3=270°)
    user_rotation = Column(Integer, default=0, nullable=False)
    
    # Author/photographer
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Import tracking
    import_source = Column(String(255))  # Description of where this came from
    
    # Relationships
    author = relationship("Author", back_populates="images")
    
    def __repr__(self):
        return f"<Image(id={self.id}, hash={self.image_hash[:8]}..., filename={self.original_filename})>"