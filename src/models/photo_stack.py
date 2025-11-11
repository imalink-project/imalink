"""
PhotoStack Model - Group photos for UI organization (one-to-many)
"""
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .photo import Photo


class PhotoStack(Base, TimestampMixin):
    """
    PhotoStack - Manually managed grouping of photos for simplified browsing
    
    User organizes similar photos into stacks to reduce clutter in gallery views.
    Each photo can belong to at most ONE stack.
    
    Use cases:
    - Burst photography (group similar shots)
    - Panorama sequences  
    - Time-lapse series
    - HDR brackets
    - Before/after comparisons
    """
    __tablename__ = "photo_stacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stack_type = Column(String(50), nullable=True)  # "burst", "panorama", "timelapse", etc.
    title = Column(String(200), nullable=True)  # Optional user-friendly name
    
    # Relationships
    user = relationship("User", back_populates="photo_stacks")
    photos = relationship("Photo", back_populates="stack", foreign_keys="[Photo.stack_id]")
    
    def __repr__(self):
        return f"<PhotoStack(id={self.id}, type='{self.stack_type}', photos={len(self.photos) if self.photos else 0})>"