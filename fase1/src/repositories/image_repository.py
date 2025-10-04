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
        """Get image by ID with author relationship loaded"""
        return (
            self.db.query(Image)
            .options(joinedload(Image.author))
            .filter(Image.id == image_id)
            .first()
        )
    
    def get_by_hash(self, image_hash: str) -> Optional[Image]:
        """Get image by hash (for duplicate detection)"""
        return (
            self.db.query(Image)
            .filter(Image.image_hash == image_hash)
            .first()
        )
    
    def exists_by_hash(self, image_hash: str) -> bool:
        """Check if image with hash already exists"""
        return (
            self.db.query(Image.id)
            .filter(Image.image_hash == image_hash)
            .first()
        ) is not None
    
    def get_images(
        self, 
        offset: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None,
        search_params: Optional[ImageSearchRequest] = None
    ) -> List[Image]:
        """Get images with optional filtering and pagination"""
        query = self.db.query(Image).options(joinedload(Image.author))
        
        # Apply filters
        query = self._apply_filters(query, author_id, search_params)
        
        # Apply sorting
        if search_params:
            query = self._apply_sorting(query, search_params.sort_by, search_params.sort_order)
        else:
            # Default sorting
            query = query.order_by(desc(Image.taken_at), desc(Image.created_at))
        
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
    
    def create(self, image_data: ImageCreateRequest) -> Image:
        """Create new image record"""
        # Convert tags to JSON string for storage
        image_dict = image_data.dict()
        if image_dict.get('tags'):
            import json
            image_dict['tags'] = json.dumps(image_dict['tags'])
        
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
        
        # Convert tags to JSON string if provided
        if 'tags' in update_data and update_data['tags'] is not None:
            import json
            update_data['tags'] = json.dumps(update_data['tags'])
        
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
    
    def rotate_image(self, image_id: int, clockwise: bool = True) -> Optional[Image]:
        """Rotate image by updating user_rotation field"""
        image = self.get_by_id(image_id)
        if not image:
            return None
        
        # Calculate new rotation (0-3 range)
        current_rotation = image.user_rotation or 0
        if clockwise:
            new_rotation = (current_rotation + 1) % 4
        else:
            new_rotation = (current_rotation - 1) % 4
        
        setattr(image, 'user_rotation', new_rotation)
        self.db.commit()
        self.db.refresh(image)
        return image
    
    def get_images_by_author(self, author_id: int, limit: int = 100) -> List[Image]:
        """Get images by specific author"""
        return (
            self.db.query(Image)
            .options(joinedload(Image.author))
            .filter(Image.author_id == author_id)
            .order_by(desc(Image.taken_at), desc(Image.created_at))
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
            .options(joinedload(Image.author))
            .order_by(desc(Image.created_at))
            .limit(limit)
            .all()
        )
    
    def get_images_with_gps(self, limit: int = 100) -> List[Image]:
        """Get images that have GPS coordinates"""
        return (
            self.db.query(Image)
            .options(joinedload(Image.author))
            .filter(and_(Image.gps_latitude.isnot(None), Image.gps_longitude.isnot(None)))
            .order_by(desc(Image.taken_at))
            .limit(limit)
            .all()
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get image statistics"""
        total_images = self.db.query(Image).count()
        total_size = self.db.query(func.sum(Image.file_size)).scalar() or 0
        images_with_gps = self.db.query(Image).filter(
            and_(Image.gps_latitude.isnot(None), Image.gps_longitude.isnot(None))
        ).count()
        
        # Get format distribution
        format_stats = (
            self.db.query(Image.file_format, func.count(Image.id))
            .group_by(Image.file_format)
            .all()
        )
        
        return {
            "total_images": total_images,
            "total_size_bytes": total_size,
            "images_with_gps": images_with_gps,
            "format_distribution": {fmt: count for fmt, count in format_stats}
        }
    
    # Private helper methods
    
    def _apply_filters(
        self, 
        query, 
        author_id: Optional[int] = None,
        search_params: Optional[ImageSearchRequest] = None
    ):
        """Apply filters to query"""
        
        # Author filter
        if author_id:
            query = query.filter(Image.author_id == author_id)
        
        if search_params:
            # Text search
            if search_params.q:
                search_term = f"%{search_params.q}%"
                query = query.filter(
                    or_(
                        Image.original_filename.ilike(search_term),
                        Image.title.ilike(search_term),
                        Image.description.ilike(search_term)
                    )
                )
            
            # Author filter from search params
            if search_params.author_id and not author_id:
                query = query.filter(Image.author_id == search_params.author_id)
            
            # Tags filter (requires JSON search - simplified for now)
            if search_params.tags:
                for tag in search_params.tags:
                    tag_pattern = f"%{tag}%"
                    query = query.filter(Image.tags.ilike(tag_pattern))
            
            # Rating filters
            if search_params.rating_min:
                query = query.filter(Image.rating >= search_params.rating_min)
            if search_params.rating_max:
                query = query.filter(Image.rating <= search_params.rating_max)
            
            # Date filters
            if search_params.taken_after:
                query = query.filter(Image.taken_at >= search_params.taken_after)
            if search_params.taken_before:
                query = query.filter(Image.taken_at <= search_params.taken_before)
            
            # GPS filter
            if search_params.has_gps is not None:
                if search_params.has_gps:
                    query = query.filter(
                        and_(Image.gps_latitude.isnot(None), Image.gps_longitude.isnot(None))
                    )
                else:
                    query = query.filter(
                        or_(Image.gps_latitude.is_(None), Image.gps_longitude.is_(None))
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