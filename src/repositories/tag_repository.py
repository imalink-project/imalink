"""
Tag Repository - Data access layer for tag operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models.tag import Tag, PhotoTag
from models.photo import Photo


class TagRepository:
    """Repository for tag CRUD operations (user-scoped)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, tag_id: int, user_id: int) -> Optional[Tag]:
        """Get tag by ID (user-scoped)"""
        return self.db.query(Tag).filter(
            and_(Tag.id == tag_id, Tag.user_id == user_id)
        ).first()
    
    def get_by_name(self, name: str, user_id: int) -> Optional[Tag]:
        """Get tag by name (case-insensitive, user-scoped)"""
        return self.db.query(Tag).filter(
            and_(Tag.name == name.lower(), Tag.user_id == user_id)
        ).first()
    
    def get_all_for_user(self, user_id: int, sort_by: str = 'name', order: str = 'asc') -> List[Tag]:
        """
        Get all tags for user with photo counts
        
        Args:
            user_id: User ID
            sort_by: Sort field ('name', 'count', 'created_at')
            order: Sort direction ('asc' or 'desc')
        """
        query = self.db.query(
            Tag,
            func.count(PhotoTag.photo_hothash).label('photo_count')
        ).outerjoin(PhotoTag, Tag.id == PhotoTag.tag_id)\
         .filter(Tag.user_id == user_id)\
         .group_by(Tag.id)
        
        # Apply sorting
        if sort_by == 'count':
            order_col = func.count(PhotoTag.photo_hothash)
        elif sort_by == 'created_at':
            order_col = Tag.created_at
        else:  # default to name
            order_col = Tag.name
        
        if order == 'desc':
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())
        
        results = query.all()
        
        # Attach photo_count to tag objects
        tags = []
        for tag, count in results:
            tag.photo_count = count
            tags.append(tag)
        
        return tags
    
    def autocomplete(self, query: str, user_id: int, limit: int = 10) -> List[Tag]:
        """
        Get tag suggestions for autocomplete (prefix matching)
        
        Args:
            query: Search prefix (case-insensitive)
            user_id: User ID
            limit: Max results
        """
        results = self.db.query(
            Tag,
            func.count(PhotoTag.photo_hothash).label('photo_count')
        ).outerjoin(PhotoTag, Tag.id == PhotoTag.tag_id)\
         .filter(
            and_(
                Tag.user_id == user_id,
                Tag.name.like(f"{query.lower()}%")
            )
         )\
         .group_by(Tag.id)\
         .order_by(func.count(PhotoTag.photo_hothash).desc())\
         .limit(limit)\
         .all()
        
        # Attach photo_count
        tags = []
        for tag, count in results:
            tag.photo_count = count
            tags.append(tag)
        
        return tags
    
    def create(self, name: str, user_id: int) -> Tag:
        """Create new tag (name must be lowercase normalized)"""
        tag = Tag(name=name.lower(), user_id=user_id)
        self.db.add(tag)
        self.db.flush()  # Get ID without committing
        return tag
    
    def get_or_create(self, name: str, user_id: int) -> Tag:
        """Get existing tag or create new one"""
        tag = self.get_by_name(name, user_id)
        if not tag:
            tag = self.create(name, user_id)
        return tag
    
    def update_name(self, tag_id: int, new_name: str, user_id: int) -> Optional[Tag]:
        """Rename tag (user-scoped)"""
        tag = self.get_by_id(tag_id, user_id)
        if tag:
            tag.name = new_name.lower()
            self.db.flush()
        return tag
    
    def delete(self, tag_id: int, user_id: int) -> bool:
        """
        Delete tag completely (user-scoped)
        Cascade deletes all photo_tags associations
        """
        tag = self.get_by_id(tag_id, user_id)
        if tag:
            self.db.delete(tag)
            return True
        return False
    
    def add_tag_to_photo(self, photo_hothash: str, tag_id: int) -> bool:
        """
        Add tag to photo (create association)
        Returns False if association already exists
        """
        existing = self.db.query(PhotoTag).filter(
            and_(
                PhotoTag.photo_hothash == photo_hothash,
                PhotoTag.tag_id == tag_id
            )
        ).first()
        
        if existing:
            return False  # Already tagged
        
        photo_tag = PhotoTag(photo_hothash=photo_hothash, tag_id=tag_id)
        self.db.add(photo_tag)
        self.db.flush()
        return True
    
    def remove_tag_from_photo(self, photo_hothash: str, tag_id: int) -> bool:
        """
        Remove tag from photo (delete association)
        Returns False if association doesn't exist
        """
        deleted = self.db.query(PhotoTag).filter(
            and_(
                PhotoTag.photo_hothash == photo_hothash,
                PhotoTag.tag_id == tag_id
            )
        ).delete()
        
        return deleted > 0
    
    def get_photo_tags(self, photo_hothash: str) -> List[Tag]:
        """Get all tags for a photo"""
        return self.db.query(Tag)\
            .join(PhotoTag, Tag.id == PhotoTag.tag_id)\
            .filter(PhotoTag.photo_hothash == photo_hothash)\
            .order_by(Tag.name)\
            .all()
    
    def count_photos_with_tag(self, tag_id: int) -> int:
        """Count how many photos have this tag"""
        return self.db.query(func.count(PhotoTag.photo_hothash))\
            .filter(PhotoTag.tag_id == tag_id)\
            .scalar() or 0
