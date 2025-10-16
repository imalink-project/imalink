"""
Photo Repository - Data Access Layer for Photo operations
Handles all database interactions for Photo model
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text, String
from datetime import datetime

from models import Photo, Author, Image
from schemas.photo_schemas import PhotoCreateRequest, PhotoUpdateRequest, PhotoSearchRequest


class PhotoRepository:
    """Repository for Photo data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_hash(self, hothash: str) -> Optional[Photo]:
        """Get photo by hash with relationships loaded"""
        return (
            self.db.query(Photo)
            .options(
                joinedload(Photo.author),
                joinedload(Photo.files),
                joinedload(Photo.import_session)
            )
            .filter(Photo.hothash == hothash)
            .first()
        )
    
    def exists_by_hash(self, hothash: str) -> bool:
        """Check if photo with hash already exists"""
        return (
            self.db.query(Photo.hothash)
            .filter(Photo.hothash == hothash)
            .first()
        ) is not None
    
    def get_photos(
        self, 
        offset: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None,
        search_params: Optional[PhotoSearchRequest] = None
    ) -> List[Photo]:
        """Get photos with optional filtering and pagination"""
        query = self.db.query(Photo).options(
            joinedload(Photo.author),
            joinedload(Photo.files),
            joinedload(Photo.import_session)
        )
        
        # Apply filters
        query = self._apply_filters(query, author_id, search_params)
        
        # Apply sorting
        if search_params:
            query = self._apply_sorting(query, search_params.sort_by, search_params.sort_order)
        else:
            # Default sorting: taken_at desc, created_at desc
            query = query.order_by(desc(Photo.taken_at), desc(Photo.created_at))
        
        return query.offset(offset).limit(limit).all()
    
    def count_photos(
        self, 
        author_id: Optional[int] = None,
        search_params: Optional[PhotoSearchRequest] = None
    ) -> int:
        """Count photos matching criteria"""
        query = self.db.query(Photo)
        
        # Apply same filters as get_photos
        query = self._apply_filters(query, author_id, search_params)
        
        return query.count()
    
    def create(self, photo_data: PhotoCreateRequest) -> Photo:
        """Create new photo"""
        # Convert tags list to JSON if provided
        tags_json = photo_data.tags if photo_data.tags else []
        
        # NOTE: hotpreview removed - stored in Image model instead
        # Access via photo.files[0].hotpreview (first Image = master)
        
        photo = Photo(
            hothash=photo_data.hothash,
            width=photo_data.width,
            height=photo_data.height,
            taken_at=photo_data.taken_at,
            gps_latitude=photo_data.gps_latitude,
            gps_longitude=photo_data.gps_longitude,
            title=photo_data.title,
            description=photo_data.description,
            tags=tags_json,
            rating=photo_data.rating or 0,
            author_id=photo_data.author_id,
            import_session_id=photo_data.import_session_id
        )
        
        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)
        return photo
    
    def update(self, hothash: str, photo_data: PhotoUpdateRequest) -> Optional[Photo]:
        """Update existing photo"""
        photo = self.get_by_hash(hothash)
        if not photo:
            return None
        
        # Update only provided fields
        if photo_data.title is not None:
            setattr(photo, 'title', photo_data.title)
        if photo_data.description is not None:
            setattr(photo, 'description', photo_data.description)
        if photo_data.tags is not None:
            setattr(photo, 'tags', photo_data.tags)
        if photo_data.rating is not None:
            setattr(photo, 'rating', photo_data.rating)
        if photo_data.user_rotation is not None:
            setattr(photo, 'user_rotation', photo_data.user_rotation)
        if photo_data.author_id is not None:
            setattr(photo, 'author_id', photo_data.author_id)
        
        self.db.flush()
        return photo
    
    def delete(self, hothash: str) -> bool:
        """Delete photo and associated files"""
        photo = self.get_by_hash(hothash)
        if not photo:
            return False
        
        self.db.delete(photo)
        self.db.flush()
        return True
    
    def rotate_photo(self, hothash: str, clockwise: bool = True) -> Optional[Photo]:
        """Rotate photo by 90 degrees"""
        photo = self.get_by_hash(hothash)
        if not photo:
            return None
        
        # Update rotation (0-3 representing 0°, 90°, 180°, 270°)
        current_rotation = getattr(photo, 'user_rotation', 0)
        if clockwise:
            new_rotation = (current_rotation + 1) % 4
        else:
            new_rotation = (current_rotation - 1) % 4
        setattr(photo, 'user_rotation', new_rotation)
        
        self.db.flush()
        return photo
    
    def get_hotpreview(self, hothash: str) -> Optional[bytes]:
        """
        Get hotpreview data for photo
        NOTE: hotpreview is now stored in Image model (first Image = master)
        """
        photo = self.db.query(Photo).filter(Photo.hothash == hothash).first()
        if photo and photo.files and len(photo.files) > 0:
            return photo.files[0].hotpreview
        return None
    
    def _apply_filters(
        self, 
        query, 
        author_id: Optional[int] = None,
        search_params: Optional[PhotoSearchRequest] = None
    ):
        """Apply filters to photo query"""
        
        # Filter by author
        if author_id:
            query = query.filter(Photo.author_id == author_id)
        
        if not search_params:
            return query
        
        # Text search in title, description
        if search_params.q:
            search_term = f"%{search_params.q}%"
            query = query.filter(
                or_(
                    Photo.title.ilike(search_term),
                    Photo.description.ilike(search_term),
                    # Search in tags (JSON array) - cast to string for text search
                    func.cast(Photo.tags, String).ilike(search_term)
                )
            )
        
        # Filter by author_id from search params
        if search_params.author_id:
            query = query.filter(Photo.author_id == search_params.author_id)
        
        # Filter by tags (AND logic - photo must have all specified tags)
        if search_params.tags:
            for tag in search_params.tags:
                # Use JSON contains operator for tags
                query = query.filter(func.cast(Photo.tags, String).ilike(f"%{tag}%"))
        
        # Filter by rating range
        if search_params.rating_min is not None:
            query = query.filter(Photo.rating >= search_params.rating_min)
        if search_params.rating_max is not None:
            query = query.filter(Photo.rating <= search_params.rating_max)
        
        # Filter by date range
        if search_params.taken_after:
            query = query.filter(Photo.taken_at >= search_params.taken_after)
        if search_params.taken_before:
            query = query.filter(Photo.taken_at <= search_params.taken_before)
        
        # Filter by GPS availability
        if search_params.has_gps is not None:
            if search_params.has_gps:
                query = query.filter(
                    and_(
                        Photo.gps_latitude.isnot(None),
                        Photo.gps_longitude.isnot(None)
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Photo.gps_latitude.is_(None),
                        Photo.gps_longitude.is_(None)
                    )
                )
        
        # Filter by RAW file availability
        if search_params.has_raw is not None:
            # This requires joining with Image table to check file types
            if search_params.has_raw:
                # Photo must have at least one RAW file
                query = query.join(Photo.files).filter(
                    Image.filename.op("~*")(r'\.(cr2|nef|arw|dng|orf|rw2|raw)$')
                ).distinct()
            else:
                # Photo must not have any RAW files
                raw_subquery = (
                    self.db.query(Photo.hothash)
                    .join(Photo.files)
                    .filter(Image.filename.op("~*")(r'\.(cr2|nef|arw|dng|orf|rw2|raw)$'))
                )
                query = query.filter(~Photo.hothash.in_(raw_subquery))
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to photo query"""
        
        # Map sort fields to Photo model attributes
        sort_field_map = {
            "taken_at": Photo.taken_at,
            "created_at": Photo.created_at,
            "title": Photo.title,
            "rating": Photo.rating,
            "updated_at": Photo.updated_at
        }
        
        # Default to taken_at if invalid field
        sort_field = sort_field_map.get(sort_by, Photo.taken_at)
        
        # Apply sort direction
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # Always add secondary sort for consistency
        if sort_by != "created_at":
            query = query.order_by(desc(Photo.created_at))
        
        return query