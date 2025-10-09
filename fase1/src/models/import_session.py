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
    
    # Archive system - Digital negative storage
    archive_base_path = Column(Text)                            # Full path to archive folder (e.g., D:\imalink_archives\imalink_2024-10-04_abc123)
    
    # File copy tracking (integrated from import_once)
    storage_name = Column(Text)                                 # Unique folder name (e.g., imalink_20241004_abc123def)
    copy_files = Column(Boolean, default=True)                 # Whether to copy files to storage
    files_copied = Column(Integer, default=0)                  # Number of files successfully copied
    files_copy_skipped = Column(Integer, default=0)            # Number of files skipped during copy (already exist)
    storage_errors_count = Column(Integer, default=0)          # Number of storage/copy errors
    
    # Storage system - Permanent file archiving
    storage_uuid = Column(String(36))                           # UUID for unique storage directory identification
    storage_name = Column(String(255))                          # Directory name (not full path) for universal search
    copy_status = Column(String(20), default="not_started")    # not_started, in_progress, completed, failed
    storage_size_mb = Column(Integer, default=0)               # Total size in MB after copying
    storage_started_at = Column(DateTime)                       # When storage copy process started
    storage_completed_at = Column(DateTime)                     # When storage copy process completed
    
    # Relationships
    default_author = relationship("Author", back_populates="imports")
    photos = relationship("Photo", back_populates="import_session")
    images = relationship("Image", back_populates="import_session")
    
    @property
    def is_archived(self) -> bool:
        """Check if this session has an archive path"""
        return bool(getattr(self, 'archive_base_path', None))
    
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
    
    @property
    def has_permanent_storage(self) -> bool:
        """Check if this session has permanent storage configured"""
        return bool(getattr(self, 'storage_uuid', None) and getattr(self, 'storage_name', None))
    
    @property
    def is_storage_in_progress(self) -> bool:
        """Check if storage copy is currently running"""
        return getattr(self, 'copy_status', '') == "in_progress"
    
    @property
    def is_storage_completed(self) -> bool:
        """Check if storage copy is completed"""
        return getattr(self, 'copy_status', '') == "completed"
    
    @property
    def storage_progress_percentage(self) -> float:
        """Calculate storage copy progress percentage"""
        total = getattr(self, 'total_files_found', 0) or 0
        copied = getattr(self, 'files_copied', 0) or 0
        if total == 0:
            return 0.0
        return (copied / total) * 100.0
    
    def generate_storage_name(self, session_description: str | None = None) -> str:
        """Generate storage name (directory name without path) with date prefix and UUID suffix"""
        import_date = (getattr(self, 'started_at', None) or datetime.utcnow()).strftime("%Y%m%d")
        uuid_suffix = getattr(self, 'storage_uuid', '')[:8] if getattr(self, 'storage_uuid', '') else "unknown"
        
        if session_description:
            # Clean session description for filename safety
            safe_description = re.sub(r'[^\w\-_]', '_', session_description)[:50]
            return f"{import_date}_import_{safe_description}_{uuid_suffix}"
        else:
            return f"{import_date}_import_session_{uuid_suffix}"
    
    def __repr__(self):
        archive_info = f"archived={self.is_archived}" if getattr(self, 'archive_base_path', None) else "no_archive"
        storage_info = f"storage={self.copy_status}" if getattr(self, 'storage_name', None) else "no_storage"
        return f"<ImportSession(id={self.id}, source={self.source_path}, status={self.status}, {archive_info}, {storage_info})>"