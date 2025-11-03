"""
Photo Collection model - Static lists of photos organized by user
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class PhotoCollection(Base, TimestampMixin):
    """
    User-defined static collection of photos.
    
    Unlike SavedPhotoSearch (dynamic, criteria-based), PhotoCollection is a
    static list of specific photos identified by their hothashes.
    
    Features:
    - Flat organization (no hierarchy)
    - User-owned (no sharing yet)
    - Ordered array (order matters)
    - Auto cover photo (first in list)
    """
    __tablename__ = "photo_collections"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Collection metadata
    name = Column(String(255), nullable=False)          # "Best of Italy 2024"
    description = Column(Text)                          # Optional notes
    
    # Photo list - JSON array of hothashes in display order
    # Example: ["abc123...", "def456...", "ghi789..."]
    # Order is significant - first photo is cover photo
    hothashes = Column(JSON, nullable=False, default=list)
    
    # Timestamps via TimestampMixin (created_at, updated_at)
    
    # Relationships
    user = relationship("User", back_populates="photo_collections")
    
    @property
    def photo_count(self) -> int:
        """Number of photos in collection"""
        return len(self.hothashes) if self.hothashes else 0
    
    @property
    def cover_photo_hothash(self) -> Optional[str]:
        """First photo serves as cover photo"""
        return self.hothashes[0] if self.hothashes else None
    
    def add_photos(self, hothashes: List[str]) -> int:
        """
        Add photos to collection (append to end).
        Returns number of photos added (skips duplicates).
        """
        if not self.hothashes:
            self.hothashes = []
        
        existing = set(self.hothashes)
        added = 0
        
        for hothash in hothashes:
            if hothash not in existing:
                self.hothashes.append(hothash)
                existing.add(hothash)
                added += 1
        
        return added
    
    def remove_photos(self, hothashes: List[str]) -> int:
        """
        Remove photos from collection.
        Returns number of photos removed.
        """
        if not self.hothashes:
            return 0
        
        to_remove = set(hothashes)
        original_count = len(self.hothashes)
        self.hothashes = [h for h in self.hothashes if h not in to_remove]
        
        return original_count - len(self.hothashes)
    
    def reorder_photos(self, hothashes: List[str]) -> bool:
        """
        Reorder photos in collection.
        New list must contain exactly the same hothashes (just reordered).
        Returns True if successful, False if hothashes don't match.
        """
        if not self.hothashes:
            return False
        
        if set(hothashes) != set(self.hothashes):
            return False
        
        self.hothashes = hothashes
        return True
    
    def cleanup_invalid_hothashes(self, valid_hothashes: set) -> int:
        """
        Remove hothashes that no longer exist in database.
        Returns number of invalid hothashes removed.
        """
        if not self.hothashes:
            return 0
        
        original_count = len(self.hothashes)
        self.hothashes = [h for h in self.hothashes if h in valid_hothashes]
        
        return original_count - len(self.hothashes)
    
    def __repr__(self):
        return f"<PhotoCollection(id={self.id}, name='{self.name}', photos={self.photo_count})>"
