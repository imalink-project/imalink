"""
Photo Collection repository - Data access layer
"""
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models.photo_collection import PhotoCollection
from schemas.photo_collection import PhotoCollectionCreate, PhotoCollectionUpdate


class PhotoCollectionRepository:
    """Repository for PhotoCollection database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Basic CRUD operations
    
    def create(self, user_id: int, collection_data: PhotoCollectionCreate) -> PhotoCollection:
        """Create new photo collection"""
        collection = PhotoCollection(
            user_id=user_id,
            name=collection_data.name,
            description=collection_data.description,
            hothashes=collection_data.hothashes or []
        )
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        return collection
    
    def get_by_id(self, collection_id: int, user_id: int) -> Optional[PhotoCollection]:
        """Get collection by ID (must belong to user)"""
        stmt = select(PhotoCollection).where(
            PhotoCollection.id == collection_id,
            PhotoCollection.user_id == user_id
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_all_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PhotoCollection]:
        """Get all collections for user with pagination"""
        stmt = (
            select(PhotoCollection)
            .where(PhotoCollection.user_id == user_id)
            .order_by(PhotoCollection.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def count_for_user(self, user_id: int) -> int:
        """Count total collections for user"""
        stmt = select(func.count(PhotoCollection.id)).where(
            PhotoCollection.user_id == user_id
        )
        return self.db.execute(stmt).scalar() or 0
    
    def update(self, collection: PhotoCollection, update_data: PhotoCollectionUpdate) -> PhotoCollection:
        """Update collection metadata"""
        if update_data.name is not None:
            collection.name = update_data.name
        if update_data.description is not None:
            collection.description = update_data.description
        
        self.db.commit()
        self.db.refresh(collection)
        return collection
    
    def delete(self, collection: PhotoCollection) -> bool:
        """Delete collection"""
        self.db.delete(collection)
        self.db.commit()
        return True
    
    # Photo management operations
    
    def add_photos(self, collection: PhotoCollection, hothashes: List[str]) -> int:
        """
        Add photos to collection.
        Returns number of photos actually added (excludes duplicates).
        """
        added_count = collection.add_photos(hothashes)
        if added_count > 0:
            self.db.commit()
            self.db.refresh(collection)
        return added_count
    
    def remove_photos(self, collection: PhotoCollection, hothashes: List[str]) -> int:
        """
        Remove photos from collection.
        Returns number of photos actually removed.
        """
        removed_count = collection.remove_photos(hothashes)
        if removed_count > 0:
            self.db.commit()
            self.db.refresh(collection)
        return removed_count
    
    def reorder_photos(self, collection: PhotoCollection, hothashes: List[str]) -> bool:
        """
        Reorder photos in collection.
        Returns True if successful, False if hothashes don't match existing.
        """
        success = collection.reorder_photos(hothashes)
        if success:
            self.db.commit()
            self.db.refresh(collection)
        return success
    
    def cleanup_invalid_hothashes(self, collection: PhotoCollection, valid_hothashes: set) -> int:
        """
        Remove invalid hothashes from collection.
        Returns number of invalid hothashes removed.
        """
        removed_count = collection.cleanup_invalid_hothashes(valid_hothashes)
        if removed_count > 0:
            self.db.commit()
            self.db.refresh(collection)
        return removed_count
    
    # Utility queries
    
    def find_collections_containing_photo(self, user_id: int, hothash: str) -> List[PhotoCollection]:
        """Find all user's collections containing specific photo"""
        stmt = select(PhotoCollection).where(
            PhotoCollection.user_id == user_id,
            PhotoCollection.hothashes.contains([hothash])
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def get_collection_by_name(self, user_id: int, name: str) -> Optional[PhotoCollection]:
        """Find collection by exact name (case-sensitive)"""
        stmt = select(PhotoCollection).where(
            PhotoCollection.user_id == user_id,
            PhotoCollection.name == name
        )
        return self.db.execute(stmt).scalar_one_or_none()
