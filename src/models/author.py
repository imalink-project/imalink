"""
Author/photographer model
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .photo import Photo
    from .input_channel import InputChannel


class Author(Base, TimestampMixin):
    """
    Author/photographer model - shared metadata tag for identifying who took a photo
    
    Authors are SHARED across all users - they are NOT user-scoped resources.
    All users can view and use all authors when tagging photos.
    
    Photo ownership and visibility is controlled via Photo.user_id, not Author.
    
    Self-Author Pattern:
    - When a user registers, an Author is automatically created with is_self=True
    - This "self-author" represents the user themselves as a photographer
    - The user's default_author_id points to this self-author
    - Users can create additional authors for other photographers (is_self=False)
    """
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    bio = Column(Text, nullable=True)
    
    # Self-Author flag - marks authors that represent users themselves
    is_self = Column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    photos = relationship("Photo", back_populates="author")
    input_channels = relationship("InputChannel", back_populates="default_author")
    
    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}', is_self={self.is_self})>"