"""
PhotoSearch Service - Handles both ad-hoc and saved photo searches
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from src.repositories.photo_search_repository import PhotoSearchRepository
from src.repositories.photo_repository import PhotoRepository
from schemas.photo_search_schemas import (
    SavedPhotoSearchCreate, SavedPhotoSearchUpdate, SavedPhotoSearchResponse,
    SavedPhotoSearchSummary, SavedPhotoSearchListResponse
)
from schemas.photo_schemas import PhotoSearchRequest, PhotoResponse
from schemas.common import PaginatedResponse, create_paginated_response
from src.core.exceptions import NotFoundError, ValidationError


class PhotoSearchService:
    """Service layer for photo search operations (both ad-hoc and saved)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.search_repo = PhotoSearchRepository(db)
        self.photo_repo = PhotoRepository(db)
    
    # =========================================================================
    # AD-HOC SEARCH (direct photo search without saving)
    # =========================================================================
    
    def execute_adhoc_search(
        self, 
        search_request: PhotoSearchRequest, 
        user_id: int
    ) -> PaginatedResponse[PhotoResponse]:
        """
        Execute an ad-hoc photo search without saving it
        
        This is the main search functionality - takes PhotoSearchRequest and
        returns matching photos directly.
        """
        # Use PhotoRepository's search functionality
        photos = self.photo_repo.get_photos(
            offset=search_request.offset,
            limit=search_request.limit,
            author_id=search_request.author_id,
            search_params=search_request,
            user_id=user_id
        )
        
        total = self.photo_repo.count_photos(
            author_id=search_request.author_id,
            search_params=search_request,
            user_id=user_id
        )
        
        # Convert to response models
        from services.photo_service import PhotoService
        photo_service = PhotoService(self.db)
        photo_responses = [photo_service._convert_to_response(photo) for photo in photos]
        
        return create_paginated_response(
            data=photo_responses,
            total=total,
            offset=search_request.offset,
            limit=search_request.limit
        )
    
    # =========================================================================
    # SAVED SEARCHES (CRUD operations)
    # =========================================================================
    
    def create_saved_search(
        self, 
        data: SavedPhotoSearchCreate, 
        user_id: int
    ) -> SavedPhotoSearchResponse:
        """Create a new saved photo search"""
        # Validate search criteria by attempting to parse as PhotoSearchRequest
        try:
            PhotoSearchRequest(**data.search_criteria)
        except Exception as e:
            raise ValidationError(f"Invalid search criteria: {str(e)}")
        
        saved_search = self.search_repo.create(user_id, data)
        return SavedPhotoSearchResponse.model_validate(saved_search)
    
    def get_saved_search(self, search_id: int, user_id: int) -> SavedPhotoSearchResponse:
        """Get a saved search by ID"""
        saved_search = self.search_repo.get_by_id(search_id, user_id)
        if not saved_search:
            raise NotFoundError("SavedPhotoSearch", search_id)
        
        return SavedPhotoSearchResponse.model_validate(saved_search)
    
    def list_saved_searches(
        self, 
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        favorites_only: bool = False
    ) -> SavedPhotoSearchListResponse:
        """List all saved searches for a user"""
        searches, total = self.search_repo.list_by_user(
            user_id=user_id,
            offset=offset,
            limit=limit,
            favorites_only=favorites_only
        )
        
        search_summaries = [
            SavedPhotoSearchSummary.model_validate(search) 
            for search in searches
        ]
        
        return SavedPhotoSearchListResponse(
            searches=search_summaries,
            total=total,
            offset=offset,
            limit=limit
        )
    
    def update_saved_search(
        self, 
        search_id: int, 
        data: SavedPhotoSearchUpdate, 
        user_id: int
    ) -> SavedPhotoSearchResponse:
        """Update a saved search"""
        # Validate new search criteria if provided
        if data.search_criteria:
            try:
                PhotoSearchRequest(**data.search_criteria)
            except Exception as e:
                raise ValidationError(f"Invalid search criteria: {str(e)}")
        
        saved_search = self.search_repo.update(search_id, user_id, data)
        if not saved_search:
            raise NotFoundError("SavedPhotoSearch", search_id)
        
        return SavedPhotoSearchResponse.model_validate(saved_search)
    
    def delete_saved_search(self, search_id: int, user_id: int) -> bool:
        """Delete a saved search"""
        success = self.search_repo.delete(search_id, user_id)
        if not success:
            raise NotFoundError("SavedPhotoSearch", search_id)
        return success
    
    # =========================================================================
    # EXECUTE SAVED SEARCH
    # =========================================================================
    
    def execute_saved_search(
        self, 
        search_id: int, 
        user_id: int,
        override_offset: Optional[int] = None,
        override_limit: Optional[int] = None
    ) -> PaginatedResponse[PhotoResponse]:
        """
        Execute a saved search and return photo results
        
        Args:
            search_id: ID of saved search to execute
            user_id: Current user ID
            override_offset: Override pagination offset from saved criteria
            override_limit: Override pagination limit from saved criteria
        
        Returns:
            Paginated photo results
        """
        # Get the saved search
        saved_search = self.search_repo.get_by_id(search_id, user_id)
        if not saved_search:
            raise NotFoundError("SavedPhotoSearch", search_id)
        
        # Convert JSON criteria to PhotoSearchRequest
        try:
            search_request = PhotoSearchRequest(**saved_search.search_criteria)
        except Exception as e:
            raise ValidationError(f"Invalid saved search criteria: {str(e)}")
        
        # Override pagination if provided
        if override_offset is not None:
            search_request.offset = override_offset
        if override_limit is not None:
            search_request.limit = override_limit
        
        # Execute the search
        results = self.execute_adhoc_search(search_request, user_id)
        
        # Update execution stats
        self.search_repo.update_execution_stats(
            search_id=search_id,
            user_id=user_id,
            result_count=results.meta.total
        )
        
        return results
