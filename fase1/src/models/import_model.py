"""
Import session model for tracking import operations
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author


class Import(Base, TimestampMixin):
    """
    Tracks imports for auditing and organization
    """
    __tablename__ = "imports"
    
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
    
    # Error log (JSON string)
    error_log = Column(Text)
    
    # Relationships
    default_author = relationship("Author", back_populates="imports")
    
    def __repr__(self):
        return f"<Import(id={self.id}, source={self.source_path}, status={self.status})>"