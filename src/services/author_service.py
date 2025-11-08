"""
Author Service - Business Logic Layer for Author operations

Authors are shared metadata tags for identifying photographers.
They are NOT user-owned - all users can see and use all authors.
Photo ownership is controlled via Photo.user_id.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.repositories.author_repository import AuthorRepository
from src.schemas.responses.author_responses import (
    AuthorResponse, AuthorListResponse
)
from src.schemas.requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest
from src.schemas.common import PaginatedResponse, create_paginated_response
from src.core.exceptions import NotFoundError, DuplicateImageError, ValidationError


class AuthorService:
    """Service class for Author business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.author_repo = AuthorRepository(db)
    
    def get_authors(
        self, 
        offset: int = 0, 
        limit: int = 100
    ) -> PaginatedResponse[AuthorResponse]:
        """Get paginated list of all authors (shared across users)"""
        
        authors = self.author_repo.get_all(offset, limit)
        total = self.author_repo.count_all()
        
        # Convert to response models
        author_responses = []
        for author in authors:
            author_response = self._convert_to_response(author)
            author_responses.append(author_response)
        
        return create_paginated_response(
            data=author_responses,
            total=total,
            offset=offset,
            limit=limit
        )
    
    def get_author_by_id(self, author_id: int) -> AuthorResponse:
        """Get specific author by ID"""
        author = self.author_repo.get_by_id(author_id)
        if not author:
            raise NotFoundError("Author", author_id)
        
        return self._convert_to_response(author)
    
    def create_author(self, author_data: AuthorCreateRequest, user_id: int) -> AuthorResponse:
        """Create new author with validation (requires authentication)"""
        
        # Business Logic: Check for duplicate names
        if self.author_repo.exists_by_name(author_data.name):
            raise ValidationError(f"Author with name '{author_data.name}' already exists")
        
        # Business Logic: Validate name format
        if not author_data.name.strip():
            raise ValidationError("Author name cannot be empty")
        
        if len(author_data.name.strip()) < 2:
            raise ValidationError("Author name must be at least 2 characters")
        
        # Business Logic: Validate email format if provided
        if author_data.email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, author_data.email):
                raise ValidationError("Invalid email format")
        
        author = self.author_repo.create(author_data, user_id)
        return self._convert_to_response(author)
    
    def update_author(
        self, 
        author_id: int, 
        update_data: AuthorUpdateRequest
    ) -> AuthorResponse:
        """Update existing author"""
        
        # Check author exists
        existing_author = self.author_repo.get_by_id(author_id)
        if not existing_author:
            raise NotFoundError("Author", author_id)
        
        update_dict = update_data.dict(exclude_unset=True)
        
        # Business Logic: Check name uniqueness if updating name
        if 'name' in update_dict:
            if self.author_repo.exists_by_name(update_dict['name'], exclude_id=author_id):
                raise ValidationError(f"Author with name '{update_dict['name']}' already exists")
            
            # Validate name length
            if len(update_dict['name'].strip()) < 2:
                raise ValidationError("Author name must be at least 2 characters")
        
        # Business Logic: Validate email if updating
        if 'email' in update_dict and update_dict['email']:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, update_dict['email']):
                raise ValidationError("Invalid email format")
        
        updated_author = self.author_repo.update(author_id, update_dict)
        if not updated_author:
            raise NotFoundError("Author", author_id)
        
        return self._convert_to_response(updated_author)
    
    def delete_author(self, author_id: int) -> bool:
        """Delete author with validation"""
        
        # Check author exists
        author = self.author_repo.get_by_id(author_id)
        if not author:
            raise NotFoundError("Author", author_id)
        
        # Business Logic: Check if author has images
        if hasattr(author, 'images') and author.images:
            raise ValidationError(
                f"Cannot delete author '{author.name}' because they have {len(author.images)} images. "
                "Please reassign or delete the images first."
            )
        
        return self.author_repo.delete(author_id)
        if not author:
            raise NotFoundError("Author", author_id)
        
        # Business Logic: Check if author has images
        if hasattr(author, 'images') and author.images:
            raise ValidationError(
                f"Cannot delete author '{author.name}' because they have {len(author.images)} images. "
                "Please reassign or delete the images first."
            )
        
        return self.author_repo.delete(author_id, user_id)
    
    # Private helper methods
    
    def _convert_to_response(self, author) -> AuthorResponse:
        """Convert database model to response model"""
        
        # Calculate image count
        image_count = 0
        if hasattr(author, 'images') and author.images:
            image_count = len(author.images)
        
        return AuthorResponse(
            id=getattr(author, 'id'),
            name=getattr(author, 'name', ''),
            email=getattr(author, 'email', None),
            bio=getattr(author, 'bio', None),
            created_at=getattr(author, 'created_at'),
            image_count=image_count
        )