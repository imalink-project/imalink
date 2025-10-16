"""
Import session model for tracking import operations
"""
import re
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author


class ImportSession(Base, TimestampMixin):
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
    
    # Default author for this import
    default_author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Statistics
    total_files_found = Column(Integer, default=0)       # All image files (JPEG + RAW)
    images_imported = Column(Integer, default=0)         # Successfully imported images
    duplicates_skipped = Column(Integer, default=0)      # Actual duplicates (same hash)
    raw_files_skipped = Column(Integer, default=0)       # RAW files with JPEG companions  
    single_raw_skipped = Column(Integer, default=0)      # Single RAW files (no JPEG companion)
    errors_count = Column(Integer, default=0)            # Files that failed to process
    
    # Progress tracking
    files_processed = Column(Integer, default=0)         # Files processed so far
    current_file = Column(Text)                          # Currently processing file
    is_cancelled = Column(Boolean, default=False)        # Whether import was cancelled
    
    # Error log (JSON string)
    error_log = Column(Text)
    
    # Optional: Client-managed storage directory name
    # Client handles all file operations; backend only stores the directory name for reference
    storage_name = Column(String(255))                          # Directory name chosen by client (e.g., "20241004_vacation_photos")
    
    # Relationships
    default_author = relationship("Author", back_populates="imports")
    photos = relationship("Photo", back_populates="import_session")
    images = relationship("Image", back_populates="import_session")
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        total = getattr(self, 'total_files_found', 0) or 0
        processed = getattr(self, 'files_processed', 0) or 0
        if total == 0:
            return 0.0
        return (processed / total) * 100.0
    
    @property
    def is_in_progress(self) -> bool:
        """Check if import is currently running"""
        status = getattr(self, 'status', '')
        cancelled = getattr(self, 'is_cancelled', False)
        return status == "in_progress" and not cancelled
    
    def __repr__(self):
        storage_info = f", storage={self.storage_name}" if getattr(self, 'storage_name', None) else ""
        return f"<ImportSession(id={self.id}, source={self.source_path}, status={self.status}{storage_info})>"