"""
Author/photographer model
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .photo import Photo
    from .import_session import ImportSession
    from .user import User


class Author(Base, TimestampMixin):
    """
    Author/photographer model - metadata tag for identifying who took a photo
    
    Authors are SHARED across all users - they are NOT user-scoped resources.
    The user_id field tracks who created the author (for audit purposes),
    but all users can see and use all authors when tagging photos.
    
    Photo ownership and visibility is controlled via Photo.user_id, not Author.
    """
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Audit trail - tracks who created this author
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    bio = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="authors")
    photos = relationship("Photo", back_populates="author")
    imports = relationship("ImportSession", back_populates="default_author")
    
    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}', user_id={self.user_id})>"