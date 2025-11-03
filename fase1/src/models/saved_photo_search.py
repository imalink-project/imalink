"""
SavedPhotoSearch model - Saved and reusable photo search queries
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class SavedPhotoSearch(Base, TimestampMixin):
    """
    Saved photo search queries for reuse
    
    Stores PhotoSearchRequest criteria as JSON for flexible querying.
    Users can save frequently used searches and execute them later.
    
    Design:
    - search_criteria: JSON field storing PhotoSearchRequest dict
    - name: User-friendly name ("Summer 2024 RAW files")
    - description: Optional longer description
    - is_favorite: Quick access to favorite searches
    - result_count: Cached count (updated when executed)
    - last_executed: Track usage
    """
    __tablename__ = "saved_photo_searches"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Search metadata
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Search criteria as JSON (stores PhotoSearchRequest)
    # Example: {"author_id": 1, "rating_min": 4, "has_raw": true, ...}
    search_criteria = Column(JSON, nullable=False)
    
    # Usage tracking
    is_favorite = Column(Boolean, default=False, nullable=False)
    result_count = Column(Integer, nullable=True)  # Cached count from last execution
    last_executed = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="saved_photo_searches")
    
    def __repr__(self):
        return f"<SavedPhotoSearch(id={self.id}, name='{self.name}', user_id={self.user_id})>"
