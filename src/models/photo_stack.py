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
    PhotoStack - Groups photos for UI organization without modifying them
    
    RELATIONSHIP CHANGE: Now uses one-to-many - each photo can belong to at most ONE stack
    
    Use cases:
    - Panorama sequences  
    - Burst photography
    - Time-lapse series
    - Before/after comparisons
    - Mini-animations
    - HDR brackets
    - Focus stacking
    """
    __tablename__ = "photo_stacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Optional metadata
    cover_photo_hothash = Column(String, nullable=True)  # Which photo to show as cover
    stack_type = Column(String, nullable=True)  # "panorama", "burst", "animation", etc.
    
    # Relationships
    user = relationship("User", back_populates="photo_stacks")
    photos = relationship("Photo", back_populates="stack")  # One-to-many: stack has many photos
    
    def __repr__(self):
        return f"<PhotoStack(id={self.id}, user_id={self.user_id}, type='{self.stack_type}', photos={len(self.photos) if self.photos else 0})>"