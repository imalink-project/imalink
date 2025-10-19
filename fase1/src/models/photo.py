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
    from .image_file import ImageFile
    from .import_session import ImportSession


class Photo(Base, TimestampMixin):
    """
    Primary photo model - aggregated view for galleries and browsing
    
    CREATION FLOW:
    Photos are NEVER created manually. They are auto-generated when creating ImageFiles:
    1. Client uploads image file → POST /image-files with hotpreview
    2. System generates hothash from hotpreview (SHA256)
    3. If Photo with hothash exists → ImageFile links to existing Photo
    4. If Photo doesn't exist → New Photo is auto-created, ImageFile links to it
    5. First ImageFile becomes "master" for the Photo
    
    This ensures:
    - No orphaned Photos without files
    - JPEG/RAW pairs naturally share same Photo (same visual content = same hash)
    - Photo metadata can be edited independently of ImageFile files
    
    Key design principles:
    - hothash as primary key (content-based, shared between JPEG/RAW)
    - Contains all user-facing metadata (title, tags, rating)
    - Contains visual presentation data (dimensions, GPS)
    - Optimized for gallery queries and photo browsing
    - hotpreview accessed via photo.image_files[0].hotpreview (master ImageFile)
    """
    __tablename__ = "photos"
    
    # Primary key = content-based hash (same for JPEG/RAW pairs)
    # Hash is generated from ImageFile.hotpreview (first ImageFile = master)
    hothash = Column(String(64), primary_key=True, index=True)
    
    # Visual presentation data (critical for galleries)
    # NOTE: hotpreview removed - stored in ImageFile model instead
    # Access via photo.image_files[0].hotpreview (first ImageFile = master)
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
    
    # Authorship (import tracking moved to ImageFile level)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Coldpreview - medium-size preview for detail views (800-1200px)
    # SIMPLIFIED: Only store path, metadata is read dynamically from file
    coldpreview_path = Column(String(255), nullable=True)  # Filesystem path to coldpreview file
    
    # Relationships
    image_files = relationship("ImageFile", back_populates="photo", cascade="all, delete-orphan", 
                        foreign_keys="[ImageFile.photo_hothash]")
    author = relationship("Author", back_populates="photos")
    # Note: No back_populates to ImportSession - access photos via ImportSession.image_files[].photo
    
    def __repr__(self):
        return f"<Photo(hash={self.hothash[:8]}..., title='{self.title or 'Untitled'}', files={len(self.image_files) if self.image_files else 0})>"
    
    @property
    def has_gps(self) -> bool:
        """Check if photo has GPS coordinates"""
        return self.gps_latitude is not None and self.gps_longitude is not None
    
    @property
    def hotpreview(self) -> Optional[bytes]:
        """Get hotpreview from first (master) ImageFile"""
        if self.image_files and len(self.image_files) > 0:
            return self.image_files[0].hotpreview
        return None
    
    @property
    def exif_dict(self) -> Optional[dict]:
        """Get EXIF metadata from first (master) ImageFile"""
        if self.image_files and len(self.image_files) > 0:
            return self.image_files[0].exif_dict
        return None
    
    @property  
    def jpeg_file(self) -> Optional["ImageFile"]:
        """Get the JPEG file for this photo (if any)"""
        if not self.image_files:
            return None
        for file in self.image_files:
            if file.filename.lower().endswith(('.jpg', '.jpeg')):
                return file
        return None
    
    @property
    def raw_file(self) -> Optional["ImageFile"]: 
        """Get the RAW file for this photo (if any)"""
        if not self.image_files:
            return None
        for file in self.image_files:
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
        if self.image_files:
            return getattr(self.image_files[0], 'filename', 'Unknown')
        return "Unknown"
    
    @property
    def import_sessions(self) -> List[int]:
        """Get all unique import sessions for this photo's files"""
        sessions = [f.import_session_id for f in self.image_files if f.import_session_id]
        return list(set(sessions))
    
    @property
    def first_imported(self) -> Optional[datetime]:
        """Get earliest import time across all files"""
        times = [f.imported_time for f in self.image_files if f.imported_time]
        return min(times) if times else None
    
    @property
    def last_imported(self) -> Optional[datetime]:
        """Get latest import time across all files"""
        times = [f.imported_time for f in self.image_files if f.imported_time]
        return max(times) if times else None