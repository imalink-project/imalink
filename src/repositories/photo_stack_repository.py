"""
PhotoStack Repository - Data access layer for PhotoStack operations (one-to-many)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.photo_stack import PhotoStack
from src.models.photo import Photo


class PhotoStackRepository:
    """Repository for PhotoStack operations with user isolation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, user_id: int, offset: int = 0, limit: int = 100) -> List[PhotoStack]:
        """Get all photo stacks for a user with pagination"""
        return (
            self.db.query(PhotoStack)
            .filter(PhotoStack.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def count_all(self, user_id: int) -> int:
        """Count total photo stacks for a user"""
        return (
            self.db.query(PhotoStack)
            .filter(PhotoStack.user_id == user_id)
            .count()
        )
    
    def get_by_id(self, stack_id: int, user_id: int) -> Optional[PhotoStack]:
        """Get a specific photo stack by ID for a user"""
        return (
            self.db.query(PhotoStack)
            .filter(PhotoStack.id == stack_id)
            .filter(PhotoStack.user_id == user_id)
            .first()
        )
    
    def create(self, stack_data: dict, user_id: int) -> PhotoStack:
        """Create a new photo stack"""
        stack = PhotoStack(
            user_id=user_id,
            cover_photo_hothash=stack_data.get('cover_photo_hothash'),
            stack_type=stack_data.get('stack_type')
        )
        
        self.db.add(stack)
        self.db.commit()
        self.db.refresh(stack)
        
        return stack
    
    def update(self, stack_id: int, update_data: dict, user_id: int) -> Optional[PhotoStack]:
        """Update an existing photo stack"""
        stack = self.get_by_id(stack_id, user_id)
        if not stack:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(stack, field):
                setattr(stack, field, value)
        
        self.db.commit()
        self.db.refresh(stack)
        
        return stack
    
    def delete(self, stack_id: int, user_id: int) -> bool:
        """Delete a photo stack (memberships cascade deleted)"""
        stack = self.get_by_id(stack_id, user_id)
        if not stack:
            return False
        
        self.db.delete(stack)
        self.db.commit()
        
        return True
    
    # Photo membership operations
    
    def add_photos(self, stack_id: int, photo_hothashes: List[str], user_id: int) -> bool:
        """Add photos to a stack (one-to-many: photos must not be in other stacks)"""
        stack = self.get_by_id(stack_id, user_id)
        if not stack:
            return False
        
        try:
            for photo_hothash in photo_hothashes:
                # Get the photo - it must belong to the user
                photo = (
                    self.db.query(Photo)
                    .filter(Photo.hothash == photo_hothash)
                    .filter(Photo.user_id == user_id)
                    .first()
                )
                
                if photo is not None:
                    # Set stack_id (will move from existing stack if any)
                    photo.stack_id = stack_id
            
            self.db.commit()
            return True
            
        except IntegrityError:
            self.db.rollback()
            return False
    
    def remove_photos(self, stack_id: int, photo_hothashes: List[str], user_id: int) -> bool:
        """Remove photos from a stack (set their stack_id to None)"""
        stack = self.get_by_id(stack_id, user_id)
        if not stack:
            return False
        
        # Update photos to remove from stack
        updated = (
            self.db.query(Photo)
            .filter(Photo.stack_id == stack_id)
            .filter(Photo.hothash.in_(photo_hothashes))
            .filter(Photo.user_id == user_id)
            .update({Photo.stack_id: None}, synchronize_session=False)
        )
        
        self.db.commit()
        return updated > 0
    
    def get_photos_in_stack(self, stack_id: int, user_id: int) -> List[str]:
        """Get all photo hothashes in a stack"""
        stack = self.get_by_id(stack_id, user_id)
        if not stack:
            return []
        
        photos = (
            self.db.query(Photo.hothash)
            .filter(Photo.stack_id == stack_id)
            .filter(Photo.user_id == user_id)
            .order_by(Photo.created_at)  # Natural ordering by created time
            .all()
        )
        
        return [p.hothash for p in photos]
    
    def get_photo_count(self, stack_id: int, user_id: int) -> int:
        """Get number of photos in a stack"""
        stack = self.get_by_id(stack_id, user_id)
        if not stack:
            return 0
        
        return (
            self.db.query(Photo)
            .filter(Photo.stack_id == stack_id)
            .filter(Photo.user_id == user_id)
            .count()
        )
    
    def get_photo_stack(self, photo_hothash: str, user_id: int) -> Optional[PhotoStack]:
        """Get the stack containing a specific photo (one-to-many: max one stack per photo)"""
        # Use direct join to get the stack via photo.stack relationship
        return (
            self.db.query(PhotoStack)
            .join(Photo, PhotoStack.id == Photo.stack_id)
            .filter(Photo.hothash == photo_hothash)
            .filter(Photo.user_id == user_id)
            .filter(PhotoStack.user_id == user_id)
            .first()
        )