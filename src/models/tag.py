"""
Tag models - User-scoped photo tagging system
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .photo import Photo


class Tag(Base, TimestampMixin):
    """
    User-scoped tag for photo categorization
    
    Design principles:
    - User-scoped: Each user has their own tag vocabulary
    - Normalized: Tag strings stored once, reused across photos
    - Case-insensitive: All tag names converted to lowercase
    - Many-to-many: One tag can apply to many photos, one photo can have many tags
    """
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(50), nullable=False)  # Lowercase normalized
    
    # Unique constraint: prevent duplicate tag names per user
    __table_args__ = (
        Index('idx_user_tag_unique', 'user_id', 'name', unique=True),
    )
    
    # Relationships
    user = relationship("User", back_populates="tags")
    photos = relationship("Photo", secondary="photo_tags", back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class PhotoTag(Base):
    """
    Association table between Photos and Tags (many-to-many)
    
    Tracks when a tag was applied to a photo.
    Composite primary key ensures no duplicate tag-photo pairs.
    """
    __tablename__ = "photo_tags"
    
    photo_hothash = Column(String(64), ForeignKey('photos.hothash'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    tagged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for reverse lookup (find all photos with a tag)
    __table_args__ = (
        Index('idx_tag_photos', 'tag_id', 'photo_hothash'),
        Index('idx_photo_tags', 'photo_hothash', 'tag_id'),
    )
    
    def __repr__(self):
        return f"<PhotoTag(photo={self.photo_hothash[:8]}..., tag_id={self.tag_id})>"
