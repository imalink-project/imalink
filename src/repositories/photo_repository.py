"""
Photo Repository - Data Access Layer for Photo operations
Handles all database interactions for Photo model
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text, String
from datetime import datetime

from src.models import Photo, Author, ImageFile
from src.schemas.photo_schemas import PhotoCreateRequest, PhotoUpdateRequest, PhotoSearchRequest


class PhotoRepository:
    """Repository for Photo data access operations with hybrid key support"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, photo_id: int, user_id: int) -> Optional[Photo]:
        """Get photo by integer ID with relationships loaded (user-scoped)"""
        query = (
            self.db.query(Photo)
            .options(
                joinedload(Photo.author),
                joinedload(Photo.image_files)
            )
            .filter(Photo.id == photo_id)
            .filter(Photo.user_id == user_id)
        )
        
        return query.first()
    
    def get_by_hash(self, hothash: str, user_id: Optional[int] = None) -> Optional[Photo]:
        """
        Get photo by hothash with relationships loaded
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public photos
        - If user_id is provided: Own photos + public photos
        """
        query = (
            self.db.query(Photo)
            .options(
                joinedload(Photo.author),
                joinedload(Photo.image_files)
            )
            .filter(Photo.hothash == hothash)
        )
        
        # Apply visibility filtering
        if user_id is None:
            # Anonymous user: only public photos
            query = query.filter(Photo.visibility == 'public')
        else:
            # Authenticated user: own photos OR public photos
            query = query.filter(
                or_(
                    Photo.user_id == user_id,
                    Photo.visibility == 'public'
                )
            )
        
        return query.first()
    
    def get_id_by_hash(self, hothash: str) -> Optional[int]:
        """Get photo ID by hothash (helper for internal operations)"""
        result = self.db.query(Photo.id).filter(Photo.hothash == hothash).first()
        return result[0] if result else None
    
    def exists_by_hash(self, hothash: str) -> bool:
        """Check if photo with hash already exists"""
        return (
            self.db.query(Photo.hothash)
            .filter(Photo.hothash == hothash)
            .first()
        ) is not None
    
    def get_by_hothashes(self, hothashes: List[str], user_id: int) -> List[Photo]:
        """Get multiple photos by hothashes (user-scoped)"""
        return (
            self.db.query(Photo)
            .options(
                joinedload(Photo.author),
                joinedload(Photo.image_files)
            )
            .filter(
                Photo.hothash.in_(hothashes),
                Photo.user_id == user_id
            )
            .all()
        )
    
    def get_photos(
        self, 
        user_id: Optional[int] = None,
        offset: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None,
        search_params: Optional[PhotoSearchRequest] = None
    ) -> List[Photo]:
        """
        Get photos with optional filtering and pagination
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public photos
        - If user_id is provided: Own photos + public photos
        """
        query = self.db.query(Photo).options(
            joinedload(Photo.author),
            joinedload(Photo.image_files)
        )
        
        # Apply filters
        query = self._apply_filters(query, author_id, search_params, user_id=user_id)
        
        # Apply sorting
        if search_params:
            query = self._apply_sorting(query, search_params.sort_by, search_params.sort_order)
        else:
            # Default sorting: taken_at desc, created_at desc
            query = query.order_by(desc(Photo.taken_at), desc(Photo.created_at))
        
        return query.offset(offset).limit(limit).all()
    
    def count_photos(
        self, 
        user_id: Optional[int] = None,
        author_id: Optional[int] = None,
        search_params: Optional[PhotoSearchRequest] = None
    ) -> int:
        """
        Count photos matching criteria
        
        Access rules (Phase 1):
        - If user_id is None (anonymous): Only public photos
        - If user_id is provided: Own photos + public photos
        """
        query = self.db.query(Photo)
        
        # Apply same filters as get_photos
        query = self._apply_filters(query, author_id, search_params, user_id=user_id)
        
        return query.count()
    
    def create(self, photo_data: PhotoCreateRequest, user_id: int) -> Photo:
        """
        Create new photo (user-scoped)
        
        Photo stores visual representation and content metadata:
        - hotpreview: 150x150px thumbnail (visual identity)
        - exif_dict: Full EXIF metadata from master file
        - GPS, dimensions, taken_at: Extracted metadata for fast queries
        - rating, author: User-editable metadata
        - import_session_id: Which import session created this photo
        - visibility: 'private' or 'public' (defaults to 'private')
        """
        photo = Photo(
            hothash=photo_data.hothash,
            user_id=user_id,
            hotpreview=photo_data.hotpreview,
            exif_dict=photo_data.exif_dict,
            width=photo_data.width,
            height=photo_data.height,
            taken_at=photo_data.taken_at,
            gps_latitude=photo_data.gps_latitude,
            gps_longitude=photo_data.gps_longitude,
            rating=photo_data.rating or 0,
            visibility=photo_data.visibility or 'private',  # Default to private for backwards compatibility
            author_id=photo_data.author_id,
            import_session_id=photo_data.import_session_id
        )
        
        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)
        return photo
    
    def update(self, hothash: str, photo_data: PhotoUpdateRequest, user_id: int) -> Optional[Photo]:
        """Update existing photo (user-scoped - only owner can update)"""
        # For updates, we MUST be the owner (no public access)
        photo = self.db.query(Photo).filter(
            Photo.hothash == hothash,
            Photo.user_id == user_id
        ).first()
        
        if not photo:
            return None
        
        # Update only provided fields
        if photo_data.rating is not None:
            setattr(photo, 'rating', photo_data.rating)
        if photo_data.category is not None:
            setattr(photo, 'category', photo_data.category)
        if photo_data.author_id is not None:
            setattr(photo, 'author_id', photo_data.author_id)
        if photo_data.visibility is not None:
            setattr(photo, 'visibility', photo_data.visibility)
        
        self.db.flush()
        return photo
    
    def delete(self, hothash: str, user_id: int) -> bool:
        """Delete photo and associated files (user-scoped - only owner can delete)"""
        # For deletes, we MUST be the owner (no public access)
        photo = self.db.query(Photo).filter(
            Photo.hothash == hothash,
            Photo.user_id == user_id
        ).first()
        
        if not photo:
            return False
        
        self.db.delete(photo)
        self.db.flush()
        return True
    
    def get_hotpreview(self, hothash: str) -> Optional[bytes]:
        """
        Get hotpreview thumbnail data for photo (150x150px JPEG)
        
        Hotpreview is stored directly in Photo model as binary data.
        Used for gallery thumbnails and duplicate detection.
        """
        photo = self.db.query(Photo).filter(Photo.hothash == hothash).first()
        return photo.hotpreview if photo else None  # type: ignore[return-value]
    
    def _apply_filters(
        self, 
        query, 
        author_id: Optional[int] = None,
        search_params: Optional[PhotoSearchRequest] = None,
        *,
        user_id: Optional[int] = None
    ):
        """
        Apply filters to photo query
        
        Rules:
        - All filters are optional (None = ignore)
        - Multiple filters use AND logic
        - tag_ids uses OR logic (photos with ANY of the tags)
        - user_id=None: Only public photos (anonymous access)
        - user_id provided: Own photos OR public/authenticated photos
        """
        
        # Apply visibility filtering (Phase 1 - 4 levels)
        if user_id is None:
            # Anonymous user: only public photos
            query = query.filter(Photo.visibility == 'public')
        else:
            # Authenticated user: own photos OR public OR authenticated
            # Note: 'space' treated as private in Phase 1
            query = query.filter(
                or_(
                    Photo.user_id == user_id,
                    Photo.visibility == 'public',
                    Photo.visibility == 'authenticated'
                )
            )
        
        # Filter by author
        if author_id:
            query = query.filter(Photo.author_id == author_id)
        
        if not search_params:
            return query
        
        # Filter by author_id from search params
        if search_params.author_id:
            query = query.filter(Photo.author_id == search_params.author_id)
        
        # Filter by import_session_id
        if search_params.import_session_id:
            query = query.filter(Photo.import_session_id == search_params.import_session_id)
        
        # Filter by tags (OR logic: photos with ANY of the specified tags)
        if search_params.tag_ids:
            from models.tag import Tag
            # Join with photo_tags association table
            query = query.join(Photo.tags).filter(Tag.id.in_(search_params.tag_ids)).distinct()
        
        # Filter by rating range
        if search_params.rating_min is not None:
            query = query.filter(Photo.rating >= search_params.rating_min)
        if search_params.rating_max is not None:
            query = query.filter(Photo.rating <= search_params.rating_max)
        
        # Filter by category
        if search_params.category is not None:
            query = query.filter(Photo.category == search_params.category)
        
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
            # This requires joining with ImageFile table to check file types
            if search_params.has_raw:
                # Photo must have at least one RAW file
                query = query.join(Photo.image_files).filter(
                    ImageFile.filename.op("~*")(r'\.(cr2|nef|arw|dng|orf|rw2|raw)$')
                ).distinct()
            else:
                # Photo must not have any RAW files
                raw_subquery = (
                    self.db.query(Photo.hothash)
                    .join(Photo.image_files)
                    .filter(ImageFile.filename.op("~*")(r'\.(cr2|nef|arw|dng|orf|rw2|raw)$'))
                )
                query = query.filter(~Photo.hothash.in_(raw_subquery))
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to photo query"""
        
        # Map sort fields to Photo model attributes
        sort_field_map = {
            "taken_at": Photo.taken_at,
            "created_at": Photo.created_at,
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