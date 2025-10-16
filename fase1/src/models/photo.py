"""
Photo model - Primary display model for photo galleries and browsing
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author
    from .image import Image
    from .import_session import ImportSession


class Photo(Base, TimestampMixin):
    """
    Primary photo model - aggregated view for galleries and browsing
    
    CREATION FLOW:
    Photos are NEVER created manually. They are auto-generated when creating Images:
    1. Client uploads image file → POST /images with hotpreview
    2. System generates hothash from hotpreview (SHA256)
    3. If Photo with hothash exists → Image links to existing Photo
    4. If Photo doesn't exist → New Photo is auto-created, Image links to it
    5. First Image becomes "master" for the Photo
    
    This ensures:
    - No orphaned Photos without files
    - JPEG/RAW pairs naturally share same Photo (same visual content = same hash)
    - Photo metadata can be edited independently of Image files
    
    Key design principles:
    - hothash as primary key (content-based, shared between JPEG/RAW)
    - Contains all user-facing metadata (title, tags, rating)
    - Contains visual presentation data (dimensions, GPS)
    - Optimized for gallery queries and photo browsing
    - hotpreview accessed via photo.files[0].hotpreview (master Image)
    """
    __tablename__ = "photos"
    
    # Primary key = content-based hash (same for JPEG/RAW pairs)
    # Hash is generated from Image.hotpreview (first Image = master)
    hothash = Column(String(64), primary_key=True, index=True)
    
    # Visual presentation data (critical for galleries)
    # NOTE: hotpreview removed - stored in Image model instead
    # Access via photo.files[0].hotpreview (first Image = master)
    width = Column(Integer)           # Original image dimensions
    height = Column(Integer)
    
    # Content metadata (extracted from EXIF)
    taken_at = Column(DateTime)       # When photo was actually taken
    gps_latitude = Column(Float)      # GPS coordinates (if available)
    gps_longitude = Column(Float)
    
    # User metadata (editable by users)
    title = Column(String(255))       # User-assigned title
    description = Column(Text)        # User description/notes
    tags = Column(JSON)               # List of tags ["nature", "landscape"]
    rating = Column(Integer, default=0)  # 1-5 star rating
    
    # Authorship and import tracking
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    
    # Relationships
    files = relationship("Image", back_populates="photo", cascade="all, delete-orphan", 
                        foreign_keys="[Image.photo_hothash]")
    author = relationship("Author", back_populates="photos")
    # Note: No back_populates to ImportSession - access photos via ImportSession.images[].photo
    
    def __repr__(self):
        return f"<Photo(hash={self.hothash[:8]}..., title='{self.title or 'Untitled'}', files={len(self.files) if self.files else 0})>"
    
    @property
    def has_gps(self) -> bool:
        """Check if photo has GPS coordinates"""
        return self.gps_latitude is not None and self.gps_longitude is not None
    
    @property
    def hotpreview(self) -> Optional[bytes]:
        """Get hotpreview from first (master) Image"""
        if self.files and len(self.files) > 0:
            return self.files[0].hotpreview
        return None
    
    @property  
    def jpeg_file(self) -> Optional["Image"]:
        """Get the JPEG file for this photo (if any)"""
        if not self.files:
            return None
        for file in self.files:
            if file.filename.lower().endswith(('.jpg', '.jpeg')):
                return file
        return None
    
    @property
    def raw_file(self) -> Optional["Image"]: 
        """Get the RAW file for this photo (if any)"""
        if not self.files:
            return None
        for file in self.files:
            if file.filename.lower().endswith(('.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.raw')):
                return file
        return None
    
    @property
    def has_raw_companion(self) -> bool:
        """Check if photo has both JPEG and RAW files"""
        return self.jpeg_file is not None and self.raw_file is not None
    
    @property
    def primary_filename(self) -> str:
        """Get the primary filename (prefer JPEG over RAW for display)"""
        jpeg = self.jpeg_file
        if jpeg:
            return getattr(jpeg, 'filename', 'Unknown')
        if self.files:
            return getattr(self.files[0], 'filename', 'Unknown')
        return "Unknown"