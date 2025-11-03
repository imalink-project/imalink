"""
ImageFile Repository - Data Access Layer for ImageFile operations
Handles all database interactions for ImageFile model
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime

from src.models import ImageFile, Author
from src.schemas.image_file_schemas import ImageFileCreateRequest, ImageFileUpdateRequest, ImageFileSearchRequest


class ImageFileRepository:
    """Repository for ImageFile data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, image_file_id: int, user_id: Optional[int] = None) -> Optional[ImageFile]:
        """
        Get image file by ID
        
        NOTE: user_id parameter kept for API compatibility but not used.
        ImageFile has no user_id - access control happens via Photo.user_id
        """
        query = self.db.query(ImageFile).filter(ImageFile.id == image_file_id)
        return query.first()
    
    # NOTE: get_by_hash and exists_by_hash removed - ImageFile no longer has hothash field
    # ImageFiles are linked to Photos via photo_id instead
    # Use get_by_id or filter by photo_id if needed
    
    def get_image_files(
        self, 
        offset: int = 0, 
        limit: int = 100,
        search_params: Optional[ImageFileSearchRequest] = None,
        user_id: Optional[int] = None
    ) -> List[ImageFile]:
        """
        Get image_file files with optional filtering and pagination
        
        NOTE: user_id parameter kept for API compatibility but not used.
        ImageFile has no user_id - access control happens via Photo.user_id
        """
        query = self.db.query(ImageFile)
        
        # Apply filters
        query = self._apply_filters(query, search_params)
        
        # Apply sorting
        if search_params:
            query = self._apply_sorting(query, search_params.sort_by, search_params.sort_order)
        else:
            # Default sorting - use ImageFile.id since other fields moved to Photo
            query = query.order_by(desc(ImageFile.id))
        
        return query.offset(offset).limit(limit).all()
    
    def count_images(
        self, 
        search_params: Optional[ImageFileSearchRequest] = None,
        user_id: Optional[int] = None
    ) -> int:
        """
        Count images matching criteria
        
        NOTE: user_id parameter kept for API compatibility but not used.
        ImageFile has no user_id - access control happens via Photo.user_id
        """
        query = self.db.query(ImageFile)
        
        # Apply same filters as get_images
        query = self._apply_filters(query, search_params)
        
        return query.count()
    
    def create(self, image_file_data: ImageFileCreateRequest | Dict[str, Any], user_id: int) -> ImageFile:
        """Create new image_file record (user-scoped - user_id used for validation only)"""
        if isinstance(image_file_data, dict):
            image_dict = image_file_data
        else:
            image_dict = image_file_data.dict()
        
        # Filter out fields that belong to Photo model (not ImageFile)
        # taken_at, gps_latitude, gps_longitude, import_session_id are Photo fields
        # user_id is also NOT on ImageFile - access control via Photo.user_id
        photo_fields = {'taken_at', 'gps_latitude', 'gps_longitude', 'import_session_id', 'user_id'}
        filtered_dict = {k: v for k, v in image_dict.items() if k not in photo_fields}
        
        image_file = ImageFile(**filtered_dict)
        self.db.add(image_file)
        self.db.commit()
        self.db.refresh(image_file)
        return image_file
    
    def update(self, image_id: int, update_data: Dict[str, Any], user_id: int) -> Optional[ImageFile]:
        """Update existing image_file (user-scoped)"""
        image_file = self.get_by_id(image_id, user_id)
        if not image_file:
            return None
        
        # Apply updates
        for key, value in update_data.items():
            if hasattr(image_file, key):
                setattr(image_file, key, value)
        
        self.db.commit()
        self.db.refresh(image_file)
        return image_file
    
    def delete(self, image_id: int, user_id: int) -> bool:
        """Delete image_file by ID (user-scoped)"""
        image_file = self.get_by_id(image_id, user_id)
        if image_file:
            self.db.delete(image_file)
            self.db.commit()
            return True
        return False
    
    # NOTE: rotate_image removed - rotation is a Photo-level concern, not ImageFile-level
    # NOTE: get_images_by_author removed - author is a Photo-level concern, not ImageFile-level
    
    def get_images_by_import_session(self, import_session_id: int) -> List[ImageFile]:
        """Get all images from a specific import session"""
        return (
            self.db.query(ImageFile)
            .filter(ImageFile.import_session_id == import_session_id)
            .order_by(desc(ImageFile.created_at))
            .all()
        )
    
    # NOTE: get_recent_images removed - use standard list/search with sorting instead
    
    def get_images_with_gps(self, limit: int = 100) -> List[ImageFile]:
        """
        Get images that have GPS coordinates (via Photo relationship)
        NOTE: GPS data is stored in Photo model, not ImageFile
        """
        from models import Photo
        return (
            self.db.query(ImageFile)
            .join(Photo, ImageFile.photo_id == Photo.id)
            .filter(and_(Photo.gps_latitude.isnot(None), Photo.gps_longitude.isnot(None)))
            .order_by(desc(Photo.taken_at))
            .limit(limit)
            .all()
        )
    
    # Private helper methods
    
    def _apply_filters(
        self, 
        query, 
        search_params: Optional[ImageFileSearchRequest] = None
    ):
        """Apply filters to query"""
        
        # NOTE: Author filter removed - author is a Photo-level concern, not ImageFile-level
        
        if search_params:
            # Text search - only search filename since ImageFile no longer has title/description
            if search_params.q:
                search_term = f"%{search_params.q}%"
                query = query.filter(
                    ImageFile.filename.ilike(search_term)
                )
            
            # NOTE: Author filter removed - author is a Photo-level concern
            
            # NOTE: Tags and rating filters removed since user metadata was moved out of ImageFile model
            # These will be implemented with ImageMetadata table in future
            
            # Date filters - NOTE: taken_at is in Photo model, not ImageFile
            # These filters require joining Photo table
            if search_params.taken_after or search_params.taken_before:
                from models import Photo
                if not any(isinstance(mapper, Photo) for mapper in query.column_descriptions):
                    query = query.join(Photo, ImageFile.photo_id == Photo.id)
                
                if search_params.taken_after:
                    query = query.filter(Photo.taken_at >= search_params.taken_after)
                if search_params.taken_before:
                    query = query.filter(Photo.taken_at <= search_params.taken_before)
            
            # GPS filter - NOTE: GPS is in Photo model, not ImageFile
            if search_params.has_gps is not None:
                from models import Photo
                if not any(isinstance(mapper, Photo) for mapper in query.column_descriptions):
                    query = query.join(Photo, ImageFile.photo_id == Photo.id)
                
                if search_params.has_gps:
                    query = query.filter(
                        and_(Photo.gps_latitude.isnot(None), Photo.gps_longitude.isnot(None))
                    )
                else:
                    query = query.filter(
                        or_(Photo.gps_latitude.is_(None), Photo.gps_longitude.is_(None))
                    )
            
            # Format filter
            if search_params.file_format:
                query = query.filter(ImageFile.file_format == search_params.file_format)
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to query"""
        # Validate sort field
        valid_sort_fields = [
            'created_at', 'taken_at', 'filename', 'file_size', 
            'rating', 'width', 'height', 'id'
        ]
        
        if sort_by not in valid_sort_fields:
            sort_by = 'taken_at'  # Default fallback
        
        # Map sort field to model attribute
        sort_field_map = {
            'filename': ImageFile.original_filename,
            'created_at': ImageFile.created_at,
            'taken_at': ImageFile.taken_at,
            'file_size': ImageFile.file_size,
            'rating': ImageFile.rating,
            'width': ImageFile.width,
            'height': ImageFile.height,
            'id': ImageFile.id
        }
        
        sort_attr = sort_field_map[sort_by]
        
        # Apply sort order
        if sort_order == 'asc':
            query = query.order_by(asc(sort_attr))
        else:
            query = query.order_by(desc(sort_attr))
        
        # Add secondary sort by ID for consistency
        if sort_by != 'id':
            query = query.order_by(desc(ImageFile.id))
        
        return query