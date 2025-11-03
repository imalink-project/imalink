"""
Repository for SavedPhotoSearch operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.saved_photo_search import SavedPhotoSearch
from schemas.photo_search_schemas import SavedPhotoSearchCreate, SavedPhotoSearchUpdate


class PhotoSearchRepository:
    """Repository for saved photo search CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_id: int, data: SavedPhotoSearchCreate) -> SavedPhotoSearch:
        """Create a new saved photo search"""
        saved_search = SavedPhotoSearch(
            user_id=user_id,
            name=data.name,
            description=data.description,
            search_criteria=data.search_criteria,
            is_favorite=data.is_favorite
        )
        self.db.add(saved_search)
        self.db.commit()
        self.db.refresh(saved_search)
        return saved_search
    
    def get_by_id(self, search_id: int, user_id: int) -> Optional[SavedPhotoSearch]:
        """Get a saved search by ID (user-scoped)"""
        return self.db.query(SavedPhotoSearch).filter(
            SavedPhotoSearch.id == search_id,
            SavedPhotoSearch.user_id == user_id
        ).first()
    
    def list_by_user(
        self, 
        user_id: int, 
        offset: int = 0, 
        limit: int = 100,
        favorites_only: bool = False
    ) -> tuple[List[SavedPhotoSearch], int]:
        """List saved searches for a user with pagination"""
        query = self.db.query(SavedPhotoSearch).filter(
            SavedPhotoSearch.user_id == user_id
        )
        
        if favorites_only:
            query = query.filter(SavedPhotoSearch.is_favorite == True)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        searches = query.order_by(
            SavedPhotoSearch.is_favorite.desc(),
            SavedPhotoSearch.last_executed.desc().nullslast(),
            SavedPhotoSearch.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return searches, total
    
    def update(
        self, 
        search_id: int, 
        user_id: int, 
        data: SavedPhotoSearchUpdate
    ) -> Optional[SavedPhotoSearch]:
        """Update a saved search"""
        saved_search = self.get_by_id(search_id, user_id)
        if not saved_search:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(saved_search, field, value)
        
        self.db.commit()
        self.db.refresh(saved_search)
        return saved_search
    
    def delete(self, search_id: int, user_id: int) -> bool:
        """Delete a saved search"""
        saved_search = self.get_by_id(search_id, user_id)
        if not saved_search:
            return False
        
        self.db.delete(saved_search)
        self.db.commit()
        return True
    
    def update_execution_stats(
        self, 
        search_id: int, 
        user_id: int, 
        result_count: int
    ) -> Optional[SavedPhotoSearch]:
        """Update result count and last executed timestamp"""
        saved_search = self.get_by_id(search_id, user_id)
        if not saved_search:
            return None
        
        saved_search.result_count = result_count
        saved_search.last_executed = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(saved_search)
        return saved_search
