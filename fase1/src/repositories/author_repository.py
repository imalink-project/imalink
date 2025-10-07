"""
Author Repository - Data Access Layer for Author operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from models import Author
from schemas.requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest


class AuthorRepository:
    """Repository for Author data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, author_id: int) -> Optional[Author]:
        """Get author by ID with photos"""
        return (
            self.db.query(Author)
            .options(joinedload(Author.photos))
            .filter(Author.id == author_id)
            .first()
        )
    
    def get_by_name(self, name: str) -> Optional[Author]:
        """Get author by name (case-insensitive)"""
        return (
            self.db.query(Author)
            .filter(func.lower(Author.name) == name.lower())
            .first()
        )
    
    def get_all(self, offset: int = 0, limit: int = 100) -> List[Author]:
        """Get all authors with pagination"""
        return (
            self.db.query(Author)
            .options(joinedload(Author.photos))
            .order_by(Author.name)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def count_all(self) -> int:
        """Count total authors"""
        return self.db.query(Author).count()
    
    def create(self, author_data: AuthorCreateRequest) -> Author:
        """Create new author"""
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
        query = self.db.query(Author).filter(func.lower(Author.name) == name.lower())
        if exclude_id:
            query = query.filter(Author.id != exclude_id)
        return query.first() is not None
    
    def get_authors_with_photos(self, limit: int = 100) -> List[Author]:
        """Get authors who have photos"""
        from models.photo import Photo
        return (
            self.db.query(Author)
            .join(Photo)
            .options(joinedload(Author.photos))
            .group_by(Author.id)
            .order_by(func.count(Photo.hothash).desc())
            .limit(limit)
            .all()
        )
    
    def get_top_authors_by_photo_count(self, limit: int = 10) -> List[tuple]:
        """Get top authors by photo count"""
        from models.photo import Photo
        return (
            self.db.query(Author, func.count(Photo.hothash).label('photo_count'))
            .outerjoin(Photo)
            .group_by(Author.id)
            .order_by(desc('photo_count'))
            .limit(limit)
            .all()
        )
    
    def search_authors(self, query: str, limit: int = 50) -> List[Author]:
        """Search authors by name, email, or bio"""
        search_term = f"%{query}%"
        return (
            self.db.query(Author)
            .options(joinedload(Author.photos))
            .filter(
                Author.name.ilike(search_term) |
                Author.email.ilike(search_term) |
                Author.bio.ilike(search_term)
            )
            .order_by(Author.name)
            .limit(limit)
            .all()
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get author statistics"""
        from models.photo import Photo
        total_authors = self.db.query(Author).count()
        
        authors_with_photos = (
            self.db.query(Author.id)
            .join(Photo)
            .distinct()
            .count()
        )
        
        total_photos = self.db.query(Photo).count()
        avg_photos_per_author = (
            total_photos / total_authors if total_authors > 0 else 0
        )
        
        return {
            "total_authors": total_authors,
            "authors_with_photos": authors_with_photos,
            "total_photos": total_photos,
            "avg_photos_per_author": round(avg_photos_per_author, 2)
        }