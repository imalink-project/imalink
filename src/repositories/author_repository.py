"""
Author Repository - Data Access Layer for Author operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from src.models import Author
from src.schemas.requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest


class AuthorRepository:
    """Repository for Author data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, author_id: int, user_id: int) -> Optional[Author]:
        """Get author by ID with photos (user-scoped)"""
        query = (
            self.db.query(Author)
            .options(joinedload(Author.photos))
            .filter(Author.id == author_id)
            .filter(Author.user_id == user_id)
        )
        
        return query.first()
    
    def get_by_name(self, name: str, user_id: int) -> Optional[Author]:
        """Get author by name (case-insensitive, user-scoped)"""
        query = (
            self.db.query(Author)
            .filter(func.lower(Author.name) == name.lower())
            .filter(Author.user_id == user_id)
        )
        
        return query.first()
    
    def get_all(self, user_id: int, offset: int = 0, limit: int = 100) -> List[Author]:
        """Get all authors with pagination (user-scoped)"""
        query = (
            self.db.query(Author)
            .options(joinedload(Author.photos))
            .filter(Author.user_id == user_id)
            .order_by(Author.name)
        )
        
        return query.offset(offset).limit(limit).all()
    
    def count_all(self, user_id: int) -> int:
        """Count total authors (user-scoped)"""
        query = self.db.query(Author).filter(Author.user_id == user_id)
        
        return query.count()
    
    def create(self, author_data: AuthorCreateRequest, user_id: int) -> Author:
        """Create new author (user-scoped)"""
        author = Author(
            user_id=user_id,
            name=author_data.name.strip(),
            email=author_data.email.strip() if author_data.email else None,
            bio=author_data.bio.strip() if author_data.bio else None
        )
        self.db.add(author)
        self.db.commit()
        self.db.refresh(author)
        return author
    
    def update(self, author_id: int, update_data: Dict[str, Any], user_id: int) -> Optional[Author]:
        """Update existing author (user-scoped)"""
        author = self.get_by_id(author_id, user_id)
        if not author:
            return None
        
        # Apply updates with trimming for string fields
        for key, value in update_data.items():
            if hasattr(author, key):
                if isinstance(value, str) and value is not None:
                    value = value.strip()
                setattr(author, key, value)
        
        self.db.commit()
        self.db.refresh(author)
        return author
    
    def delete(self, author_id: int, user_id: int) -> bool:
        """Delete author by ID (user-scoped)"""
        author = self.get_by_id(author_id, user_id)
        if author:
            self.db.delete(author)
            self.db.commit()
            return True
        return False
    
    def exists_by_name(self, name: str, user_id: int, exclude_id: Optional[int] = None) -> bool:
        """Check if author with name already exists (user-scoped)"""
        query = (
            self.db.query(Author)
            .filter(func.lower(Author.name) == name.lower())
            .filter(Author.user_id == user_id)
        )
        if exclude_id:
            query = query.filter(Author.id != exclude_id)
        return query.first() is not None
    
