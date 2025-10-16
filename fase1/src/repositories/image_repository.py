"""
Image Repository - Data Access Layer for Image operations
Handles all database interactions for Image model
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime

from models import Image, Author
from schemas.image_schemas import ImageCreateRequest, ImageUpdateRequest, ImageSearchRequest


class ImageRepository:
    """Repository for Image data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, image_id: int) -> Optional[Image]:
        """Get image by ID"""
        return (
            self.db.query(Image)
            .filter(Image.id == image_id)
            .first()
        )
    
    # NOTE: get_by_hash and exists_by_hash removed - Image no longer has hothash field
    # Images are linked to Photos via photo_hothash instead
    # Use get_by_id or filter by photo_hothash if needed
    
    def get_images(
        self, 
        offset: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None,
        search_params: Optional[ImageSearchRequest] = None
    ) -> List[Image]:
        """Get images with optional filtering and pagination"""
        query = self.db.query(Image)
        
        # Apply filters
        query = self._apply_filters(query, author_id, search_params)
        
        # Apply sorting
        if search_params:
            query = self._apply_sorting(query, search_params.sort_by, search_params.sort_order)
        else:
            # Default sorting - use Image.id since other fields moved to Photo
            query = query.order_by(desc(Image.id))
        
        return query.offset(offset).limit(limit).all()
    
    def count_images(
        self, 
        author_id: Optional[int] = None,
        search_params: Optional[ImageSearchRequest] = None
    ) -> int:
        """Count images matching criteria"""
        query = self.db.query(Image)
        
        # Apply same filters as get_images
        query = self._apply_filters(query, author_id, search_params)
        
        return query.count()
    
    def create(self, image_data: ImageCreateRequest | Dict[str, Any]) -> Image:
        """Create new image record"""
        if isinstance(image_data, dict):
            image_dict = image_data
        else:
            image_dict = image_data.dict()
        
        image = Image(**image_dict)
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image
    
    def update(self, image_id: int, update_data: Dict[str, Any]) -> Optional[Image]:
        """Update existing image"""
        image = self.get_by_id(image_id)
        if not image:
            return None
        
        # Apply updates
        for key, value in update_data.items():
            if hasattr(image, key):
                setattr(image, key, value)
        
        self.db.commit()
        self.db.refresh(image)
        return image
    
    def delete(self, image_id: int) -> bool:
        """Delete image by ID"""
        image = self.get_by_id(image_id)
        if image:
            self.db.delete(image)
            self.db.commit()
            return True
        return False
    
    # NOTE: rotate_image removed - rotation is a Photo-level concern, not Image-level
    
    def get_images_by_author(self, author_id: int, limit: int = 100) -> List[Image]:
        """Get images by specific author (via Photo relationship)"""
        from models import Photo  # Import here to avoid circular imports
        return (
            self.db.query(Image)
            .join(Photo, Image.hothash == Photo.hothash)
            .filter(Photo.author_id == author_id)
            .order_by(desc(Image.id))
            .limit(limit)
            .all()
        )
    
    def get_images_by_import_session(self, import_session_id: int) -> List[Image]:
        """Get all images from a specific import session"""
        return (
            self.db.query(Image)
            .filter(Image.import_session_id == import_session_id)
            .order_by(desc(Image.created_at))
            .all()
        )
    
    def get_recent_images(self, limit: int = 50) -> List[Image]:
        """Get recently imported images"""
        return (
            self.db.query(Image)
            .order_by(desc(Image.created_at))
            .limit(limit)
            .all()
        )
    
    def get_images_with_gps(self, limit: int = 100) -> List[Image]:
        """
        Get images that have GPS coordinates (via Photo relationship)
        NOTE: GPS data is stored in Photo model, not Image
        """
        from models import Photo
        return (
            self.db.query(Image)
            .join(Photo, Image.photo_hothash == Photo.hothash)
            .filter(and_(Photo.gps_latitude.isnot(None), Photo.gps_longitude.isnot(None)))
            .order_by(desc(Photo.taken_at))
            .limit(limit)
            .all()
        )
    
    # Private helper methods
    
    def _apply_filters(
        self, 
        query, 
        author_id: Optional[int] = None,
        search_params: Optional[ImageSearchRequest] = None
    ):
        """Apply filters to query"""
        
        # Author filter (via Photo relationship)
        if author_id:
            from models import Photo  # Import here to avoid circular imports
            query = query.join(Photo, Image.photo_hothash == Photo.hothash).filter(Photo.author_id == author_id)
        
        if search_params:
            # Text search - only search filename since Image no longer has title/description
            if search_params.q:
                search_term = f"%{search_params.q}%"
                query = query.filter(
                    Image.filename.ilike(search_term)
                )
            
            # Author filter from search params (via Photo relationship)
            if search_params.author_id and not author_id:
                from models import Photo  # Import here to avoid circular imports
                query = query.join(Photo, Image.photo_hothash == Photo.hothash).filter(Photo.author_id == search_params.author_id)
            
            # NOTE: Tags and rating filters removed since user metadata was moved out of Image model
            # These will be implemented with ImageMetadata table in future
            
            # Date filters - NOTE: taken_at is in Photo model, not Image
            # These filters require joining Photo table
            if search_params.taken_after or search_params.taken_before:
                from models import Photo
                if not any(isinstance(mapper, Photo) for mapper in query.column_descriptions):
                    query = query.join(Photo, Image.photo_hothash == Photo.hothash)
                
                if search_params.taken_after:
                    query = query.filter(Photo.taken_at >= search_params.taken_after)
                if search_params.taken_before:
                    query = query.filter(Photo.taken_at <= search_params.taken_before)
            
            # GPS filter - NOTE: GPS is in Photo model, not Image
            if search_params.has_gps is not None:
                from models import Photo
                if not any(isinstance(mapper, Photo) for mapper in query.column_descriptions):
                    query = query.join(Photo, Image.photo_hothash == Photo.hothash)
                
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
                query = query.filter(Image.file_format == search_params.file_format)
        
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
            'filename': Image.original_filename,
            'created_at': Image.created_at,
            'taken_at': Image.taken_at,
            'file_size': Image.file_size,
            'rating': Image.rating,
            'width': Image.width,
            'height': Image.height,
            'id': Image.id
        }
        
        sort_attr = sort_field_map[sort_by]
        
        # Apply sort order
        if sort_order == 'asc':
            query = query.order_by(asc(sort_attr))
        else:
            query = query.order_by(desc(sort_attr))
        
        # Add secondary sort by ID for consistency
        if sort_by != 'id':
            query = query.order_by(desc(Image.id))
        
        return query