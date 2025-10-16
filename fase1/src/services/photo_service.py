"""
Photo Service - Business Logic Layer for Photo operations
Orchestrates photo operations and implements business rules
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pathlib import Path
import json
import time

from repositories.photo_repository import PhotoRepository
from repositories.image_file_repository import ImageFileRepository
from schemas.photo_schemas import (
    PhotoResponse, PhotoCreateRequest, PhotoUpdateRequest, PhotoSearchRequest,
    AuthorSummary, ImageFileSummary
)
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, DuplicatePhotoError, ValidationError
from models import Photo, ImageFile


class PhotoService:
    """Service layer for Photo operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.photo_repo = PhotoRepository(db)
    
    def get_photos(
        self,
        offset: int = 0,
        limit: int = 100,
        author_id: Optional[int] = None,
        search_params: Optional[PhotoSearchRequest] = None
    ) -> PaginatedResponse[PhotoResponse]:
        """Get paginated list of photos"""
        
        # Get photos from repository
        photos = self.photo_repo.get_photos(
            offset=offset,
            limit=limit,
            author_id=author_id,
            search_params=search_params
        )
        
        # Count total photos
        total = self.photo_repo.count_photos(
            author_id=author_id,
            search_params=search_params
        )
        
        # Convert to response models
        photo_responses = [self._convert_to_response(photo) for photo in photos]
        
        return create_paginated_response(
            data=photo_responses,
            total=total,
            offset=offset,
            limit=limit
        )
    
    def get_photo_by_hash(self, hothash: str) -> PhotoResponse:
        """Get single photo by hash"""
        photo = self.photo_repo.get_by_hash(hothash)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        return self._convert_to_response(photo)
    
    # NOTE: Photo creation removed - Photos are now created automatically via ImageFile service
    # When an ImageFile is created without hothash, a new Photo is auto-generated
    # This architecture change makes ImageFile the entry point for photo management
    
    def update_photo(self, hothash: str, photo_data: PhotoUpdateRequest) -> PhotoResponse:
        """Update existing photo"""
        
        # Validate tags if provided
        if photo_data.tags:
            self._validate_tags(photo_data.tags)
        
        # Update photo
        photo = self.photo_repo.update(hothash, photo_data)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        self.db.commit()
        return self._convert_to_response(photo)
    
    def delete_photo(self, hothash: str) -> bool:
        """Delete photo"""
        success = self.photo_repo.delete(hothash)
        if not success:
            raise NotFoundError("Photo", hothash)
        
        self.db.commit()
        return True
    
    def get_hotpreview(self, hothash: str) -> Optional[bytes]:
        """Get hotpreview data for photo"""
        hotpreview_data = self.photo_repo.get_hotpreview(hothash)
        if not hotpreview_data:
            raise NotFoundError("Hotpreview", hothash)
        
        return hotpreview_data
    
    def search_photos(self, search_params: PhotoSearchRequest) -> PaginatedResponse[PhotoResponse]:
        """Search photos with advanced filtering"""
        return self.get_photos(
            offset=search_params.offset,
            limit=search_params.limit,
            search_params=search_params
        )
    
    def _convert_to_response(self, photo: Photo) -> PhotoResponse:
        """Convert Photo model to PhotoResponse"""
        
        # Convert author if present
        author = None
        if photo.author:
            author = AuthorSummary(
                id=photo.author.id,
                name=photo.author.name
            )
        
        # Convert associated image files
        files = []
        if photo.image_files:
            for image_file in photo.image_files:
                file_format = self._get_file_format(image_file.filename)
                files.append(ImageFileSummary(
                    id=image_file.id,
                    filename=image_file.filename,
                    file_format=file_format,
                    file_size=image_file.file_size
                ))
        
        # Compute derived properties
        has_gps = photo.has_gps
        has_raw_companion = photo.has_raw_companion
        primary_filename = photo.primary_filename
        
        # Convert hotpreview binary to base64 string
        hotpreview_b64 = None
        hotpreview_data = getattr(photo, 'hotpreview', None)
        if hotpreview_data:
            import base64
            hotpreview_b64 = base64.b64encode(hotpreview_data).decode('utf-8')
        
        return PhotoResponse(
            hothash=getattr(photo, 'hothash'),
            hotpreview=hotpreview_b64,
            width=getattr(photo, 'width', None),
            height=getattr(photo, 'height', None),
            taken_at=getattr(photo, 'taken_at', None),
            gps_latitude=getattr(photo, 'gps_latitude', None),
            gps_longitude=getattr(photo, 'gps_longitude', None),
            title=getattr(photo, 'title', None),
            description=getattr(photo, 'description', None),
            tags=getattr(photo, 'tags', []) or [],
            rating=getattr(photo, 'rating', 0),
            created_at=getattr(photo, 'created_at'),
            updated_at=getattr(photo, 'updated_at'),
            author=author,
            author_id=getattr(photo, 'author_id', None),
            import_session_id=getattr(photo, 'import_session_id', None),
            has_gps=has_gps,
            has_raw_companion=has_raw_companion,
            primary_filename=primary_filename,
            files=files
        )
    
    def _validate_tags(self, tags: List[str]) -> None:
        """Validate tag format and constraints"""
        if len(tags) > 20:  # Max 20 tags
            raise ValidationError("Maximum 20 tags allowed per photo")
        
        for tag in tags:
            if not tag or len(tag.strip()) == 0:
                raise ValidationError("Empty tags are not allowed")
            if len(tag) > 50:  # Max 50 chars per tag
                raise ValidationError(f"Tag '{tag}' is too long (max 50 characters)")
            if not tag.replace(" ", "").replace("-", "").replace("_", "").isalnum():
                raise ValidationError(f"Tag '{tag}' contains invalid characters")
    
    def _get_file_format(self, filename: str) -> str:
        """Determine file format from filename"""
        if not filename:
            return "unknown"
        
        ext = Path(filename).suffix.lower()
        
        # Map extensions to formats
        format_map = {
            ".jpg": "jpeg",
            ".jpeg": "jpeg",
            ".png": "png",
            ".gif": "gif",
            ".bmp": "bmp",
            ".tiff": "tiff",
            ".tif": "tiff",
            ".webp": "webp",
            ".cr2": "raw",
            ".nef": "raw", 
            ".arw": "raw",
            ".dng": "raw",
            ".orf": "raw",
            ".rw2": "raw",
            ".raw": "raw"
        }
        
        return format_map.get(ext, "unknown")
    
