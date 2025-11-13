"""
Author Repository - Data Access Layer for Author operations

Authors are shared metadata tags used to identify photographers.
They are NOT user-owned resources - all users can see and use all authors.
Photo ownership and visibility is controlled via Photo.user_id, not Author.
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
    
    def get_by_id(self, author_id: int) -> Optional[Author]:
        """Get author by ID with photos"""
        query = (
            self.db.query(Author)
            .options(joinedload(Author.photos))
            .filter(Author.id == author_id)
        )
        
        return query.first()
    
    def get_by_name(self, name: str) -> Optional[Author]:
        """Get author by name (case-insensitive)"""
        query = (
            self.db.query(Author)
            .filter(func.lower(Author.name) == name.lower())
        )
        
        return query.first()
    
    def get_all(self, offset: int = 0, limit: int = 100) -> List[Author]:
        """Get all authors with pagination"""
        query = (
            self.db.query(Author)
            .options(joinedload(Author.photos))
            .order_by(Author.name)
        )
        
        return query.offset(offset).limit(limit).all()
    
    def count_all(self) -> int:
        """Count total authors"""
        return self.db.query(Author).count()
    
    def create(self, author_data: AuthorCreateRequest, user_id: int) -> Author:
        """Create new author - user_id no longer needed (authors are shared)"""
        author = Author(
            name=author_data.name.strip(),
            email=author_data.email.strip() if author_data.email else None,
            bio=author_data.bio.strip() if author_data.bio else None
        )
        self.db.add(author)
        self.db.commit()
        self.db.refresh(author)
        return author
    
    def update(self, author_id: int, update_data: Dict[str, Any]) -> Optional[Author]:
        """Update existing author"""
        author = self.get_by_id(author_id)
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
    
    def delete(self, author_id: int) -> bool:
        """Delete author by ID"""
        author = self.get_by_id(author_id)
        if author:
            self.db.delete(author)
            self.db.commit()
            return True
        return False
    
    def exists_by_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if author with name already exists"""
        query = (
            self.db.query(Author)
            .filter(func.lower(Author.name) == name.lower())
        )
        if exclude_id:
            query = query.filter(Author.id != exclude_id)
        return query.first() is not None
    
