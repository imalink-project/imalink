"""
Photo model - Primary display model for photo galleries and browsing
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author
    from .image_file import ImageFile
    from .import_session import ImportSession
    from .user import User
    from .tag import Tag


class Photo(Base, TimestampMixin):
    """
    Primary photo model - aggregated view for galleries and browsing
    
    CREATION FLOW:
    Photos are created when uploading the first (master) ImageFile:
    1. Client uploads image file → POST /image-files/new-photo with hotpreview, exif_dict
    2. System generates hothash from hotpreview (SHA256)
    3. Photo is created with hotpreview, exif_dict from request
    4. ImageFile is created and linked to Photo (without hotpreview/exif - stored only in Photo)
    5. Additional ImageFiles (RAW, etc.) can be added via POST /image-files/add-to-photo
    
    This ensures:
    - Photo has single source of visual representation (from master file)
    - No duplication of hotpreview/exif data across multiple ImageFiles
    - JPEG/RAW pairs naturally share same Photo (same visual content = same hash)
    - Photo metadata can be edited independently of ImageFile files
    
    Key design principles:
    - Hybrid primary key: Integer id (technical PK) + unique hothash (content-based identifier)
    - hothash used for API operations (content-based, shared between JPEG/RAW)
    - id used internally for foreign key relationships (performance optimization)
    - Contains all user-facing metadata (rating, author, GPS)
    - Contains visual data (hotpreview, coldpreview, dimensions)
    - Contains EXIF metadata from master file (immutable after creation)
    - Optimized for gallery queries and photo browsing
    """
    __tablename__ = "photos"
    
    # Technical primary key for efficient joins and foreign key relationships
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Content-based identifier (unique, used in API)
    # Hash is generated from hotpreview (SHA256) - same for JPEG/RAW pairs
    hothash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Data ownership - each photo belongs to a user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Visual presentation data from master ImageFile (immutable after creation)
    hotpreview = Column(LargeBinary, nullable=False)  # 150x150px thumbnail from master file
    exif_dict = Column(JSON, nullable=True)           # EXIF metadata from master file
    
    # Image dimensions (extracted from EXIF or provided by client)
    width = Column(Integer)           # Original image dimensions
    height = Column(Integer)
    
    # Content metadata (extracted from EXIF)
    taken_at = Column(DateTime)       # When photo was actually taken
    gps_latitude = Column(Float)      # GPS coordinates (if available)
    gps_longitude = Column(Float)
    
    # User metadata (editable by users)
    rating = Column(Integer, default=0)  # 1-5 star rating
    
    # Import tracking - which import session this photo came from
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    
    # Authorship
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # PhotoStack relationship - each photo can belong to ONE stack (optional)
    stack_id = Column(Integer, ForeignKey('photo_stacks.id'), nullable=True, index=True)
    
    # Coldpreview - medium-size preview for detail views (800-1200px)
    # SIMPLIFIED: Only store path, metadata is read dynamically from file
    coldpreview_path = Column(String(255), nullable=True)  # Filesystem path to coldpreview file
    
    # Photo Corrections - Non-destructive metadata overrides
    # These allow users to correct inaccurate EXIF data without modifying original files
    timeloc_correction = Column(JSON, nullable=True)  # Time/location corrections with metadata
    view_correction = Column(JSON, nullable=True)      # Display adjustments (rotation, crop, exposure)
    
    # Sharing and visibility control (Fase 1)
    visibility = Column(String(20), nullable=False, default='private', index=True)
    # Values: 'private' (only owner), 'public' (everyone including anonymous)
    
    # Relationships
    user = relationship("User", back_populates="photos")
    image_files = relationship("ImageFile", back_populates="photo", cascade="all, delete-orphan", 
                        foreign_keys="[ImageFile.photo_id]")
    author = relationship("Author", back_populates="photos")
    import_session = relationship("ImportSession", back_populates="photos")
    stack = relationship("PhotoStack", back_populates="photos", foreign_keys=[stack_id])
    tags = relationship("Tag", secondary="photo_tags", back_populates="photos")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('private', 'public')",
            name='valid_photo_visibility'
        ),
    )
    
    def __repr__(self):
        return f"<Photo(hash={self.hothash[:8]}..., rating={self.rating}, files={len(self.image_files) if self.image_files else 0})>"
    
    @property
    def has_gps(self) -> bool:
        """Check if photo has GPS coordinates"""
        return self.gps_latitude is not None and self.gps_longitude is not None
    
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
    def first_imported(self) -> Optional[datetime]:
        """Get earliest import time across all files"""
        times = [f.imported_time for f in self.image_files if f.imported_time]
        return min(times) if times else None
    
    @property
    def last_imported(self) -> Optional[datetime]:
        """Get latest import time across all files"""
        times = [f.imported_time for f in self.image_files if f.imported_time]
        return max(times) if times else None