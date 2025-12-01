"""
User model for authentication and data ownership
"""
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .photo import Photo
    from .input_channel import InputChannel
    from .author import Author
    from .tag import Tag


class User(Base, TimestampMixin):
    """
    User model for authentication and data ownership
    
    Each user has their own isolated data:
    - Photos they've uploaded
    - Input channels they've created
    - Authors (photographers) they've defined
    
    Self-Author Pattern:
    - At registration, a default Author is created representing the user
    - default_author_id points to this self-author
    - Used automatically when author_id not specified in photo imports
    
    Supports future group sharing functionality.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Default author (self-author created at registration)
    default_author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    
    # Relationships to user-owned data
    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    input_channels = relationship("InputChannel", back_populates="user", cascade="all, delete-orphan")
    photo_stacks = relationship("PhotoStack", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    saved_photo_searches = relationship("SavedPhotoSearch", back_populates="user", cascade="all, delete-orphan")
    photo_collections = relationship("PhotoCollection", back_populates="user", cascade="all, delete-orphan")
    phototext_documents = relationship("PhotoTextDocument", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', active={self.is_active})>"
    
    @property
    def photos_count(self) -> int:
        """Count of photos owned by this user"""
        return len(self.photos) if self.photos else 0
    
    @property
    def input_channels_count(self) -> int:
        """Count of input channels for this user"""
        return len(self.input_channels) if self.input_channels else 0