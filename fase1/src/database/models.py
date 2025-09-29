"""
Database models for ImaLink Fase 1
Simple and focused on core functionality
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Image(Base):
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
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
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
    
    # Import tracking
    import_source = Column(String(255))  # Description of where this came from
    
    def __repr__(self):
        return f"<Image(id={self.id}, hash={self.image_hash[:8]}..., filename={self.original_filename})>"


class ImportSession(Base):
    """
    Tracks import sessions for auditing and organization
    """
    __tablename__ = "import_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Session info
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), default="in_progress")  # in_progress, completed, failed
    
    # Import details
    source_path = Column(Text, nullable=False)
    source_description = Column(Text)
    
    # Statistics
    total_files_found = Column(Integer, default=0)
    images_imported = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Error log (JSON string)
    error_log = Column(Text)
    
    def __repr__(self):
        return f"<ImportSession(id={self.id}, source={self.source_path}, status={self.status})>"