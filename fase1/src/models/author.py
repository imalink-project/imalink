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
    Author/photographer model - who took the photo
    
    Each user maintains their own list of photographers/authors.
    This allows users to have personal author lists without conflicts.
    """
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Data ownership - each author belongs to a user
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