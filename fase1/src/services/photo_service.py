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
        search_params: Optional[PhotoSearchRequest] = None,
        user_id: Optional[int] = None
    ) -> PaginatedResponse[PhotoResponse]:
        """Get paginated list of photos (user-scoped)"""
        
        # Get photos from repository
        photos = self.photo_repo.get_photos(
            offset=offset,
            limit=limit,
            author_id=author_id,
            search_params=search_params,
            user_id=user_id
        )
        
        # Count total photos
        total = self.photo_repo.count_photos(
            author_id=author_id,
            search_params=search_params,
            user_id=user_id
        )
        
        # Convert to response models
        photo_responses = [self._convert_to_response(photo) for photo in photos]
        
        return create_paginated_response(
            data=photo_responses,
            total=total,
            offset=offset,
            limit=limit
        )
    
    def get_photo_by_hash(self, hothash: str, user_id: int) -> PhotoResponse:
        """Get single photo by hash (user-scoped)"""
        photo = self.photo_repo.get_by_hash(hothash, user_id)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        return self._convert_to_response(photo)
    
    # NOTE: Photo creation removed - Photos are now created automatically via ImageFile service
    # When an ImageFile is created without hothash, a new Photo is auto-generated
    # This architecture change makes ImageFile the entry point for photo management
    
    def update_photo(self, hothash: str, photo_data: PhotoUpdateRequest, user_id: int) -> PhotoResponse:
        """Update existing photo (user-scoped)"""
        
        # Update photo
        photo = self.photo_repo.update(hothash, photo_data, user_id)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        self.db.commit()
        return self._convert_to_response(photo)
    
    def delete_photo(self, hothash: str, user_id: int) -> bool:
        """Delete photo (user-scoped)"""
        success = self.photo_repo.delete(hothash, user_id)
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
    
    def search_photos(self, search_params: PhotoSearchRequest, user_id: int) -> PaginatedResponse[PhotoResponse]:
        """Search photos with advanced filtering (user-scoped)"""
        return self.get_photos(
            offset=search_params.offset,
            limit=search_params.limit,
            search_params=search_params,
            user_id=user_id
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
        
        # Get coldpreview metadata dynamically from file
        coldpreview_path = getattr(photo, 'coldpreview_path', None)
        coldpreview_metadata = None
        if coldpreview_path:
            from utils.coldpreview_repository import ColdpreviewRepository
            repository = ColdpreviewRepository()
            coldpreview_metadata = repository.get_coldpreview_metadata(coldpreview_path)
        
        return PhotoResponse(
            hothash=getattr(photo, 'hothash'),
            width=getattr(photo, 'width', None),
            height=getattr(photo, 'height', None),
            coldpreview_path=coldpreview_path,
            coldpreview_width=coldpreview_metadata["width"] if coldpreview_metadata else None,
            coldpreview_height=coldpreview_metadata["height"] if coldpreview_metadata else None,
            coldpreview_size=coldpreview_metadata["size"] if coldpreview_metadata else None,
            taken_at=getattr(photo, 'taken_at', None),
            gps_latitude=getattr(photo, 'gps_latitude', None),
            gps_longitude=getattr(photo, 'gps_longitude', None),
            exif_dict=getattr(photo, 'exif_dict', None),
            perceptual_hash=getattr(photo, 'perceptual_hash', None),
            rating=getattr(photo, 'rating', 0),
            created_at=getattr(photo, 'created_at'),
            updated_at=getattr(photo, 'updated_at'),
            author=author,
            author_id=getattr(photo, 'author_id', None),
            import_sessions=photo.import_sessions,
            first_imported=photo.first_imported,
            last_imported=photo.last_imported,
            has_gps=has_gps,
            has_raw_companion=has_raw_companion,
            primary_filename=primary_filename,
            files=files
        )
    

    
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
    
    def upload_coldpreview(self, hothash: str, file_content: bytes) -> Dict[str, Any]:
        """Upload or update coldpreview for a photo"""
        print(f"DEBUG COLDPREVIEW: Starting coldpreview upload for hothash: {hothash}")
        print(f"DEBUG COLDPREVIEW: File content size: {len(file_content)} bytes")
        print(f"DEBUG COLDPREVIEW: This is the COLDPREVIEW service - no perceptual hash should be generated here")
        
        # Get photo to ensure it exists
        photo = self.photo_repo.get_by_hash(hothash)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        print(f"DEBUG COLDPREVIEW: Photo found: {photo.hothash}")
        
        # Use coldpreview repository utility
        from utils.coldpreview_repository import ColdpreviewRepository
        repository = ColdpreviewRepository()
        
        try:
            # Save coldpreview and get metadata (returns tuple)
            print("DEBUG COLDPREVIEW: Calling repository.save_coldpreview...")
            relative_path, width, height, file_size = repository.save_coldpreview(hothash, file_content)
            print(f"DEBUG COLDPREVIEW: Coldpreview saved successfully: {width}x{height}, {file_size} bytes")
        except Exception as e:
            print(f"DEBUG COLDPREVIEW: Error in save_coldpreview: {e}")
            raise
        
        # SIMPLIFIED: Only store path, dimensions/size will be read dynamically
        setattr(photo, 'coldpreview_path', relative_path)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(photo)
        
        print("DEBUG COLDPREVIEW: Database updated successfully")
        print("DEBUG COLDPREVIEW: Coldpreview upload completed - NO PERCEPTUAL HASH INVOLVED")
        
        return {
            'hothash': hothash,
            'width': width,
            'height': height,
            'size': file_size,
            'path': relative_path
        }
    
    def get_coldpreview(self, hothash: str, width: Optional[int] = None, height: Optional[int] = None) -> Optional[bytes]:
        """Get coldpreview image for photo with optional resizing"""
        # Get photo
        photo = self.photo_repo.get_by_hash(hothash)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        # Check if coldpreview exists
        if not getattr(photo, 'coldpreview_path', None):
            return None
        
        # Use coldpreview repository utility
        from utils.coldpreview_repository import ColdpreviewRepository
        repository = ColdpreviewRepository()
        
        # Load coldpreview with optional resizing
        if width or height:
            # First load the original image
            original_data = repository.load_coldpreview_by_hash(hothash)
            if not original_data:
                return None
            # Then resize it
            return repository.resize_coldpreview(original_data, target_width=width, target_height=height)
        else:
            return repository.load_coldpreview_by_hash(hothash)
    
    def delete_coldpreview(self, hothash: str) -> None:
        """Delete coldpreview for photo"""
        # Get photo
        photo = self.photo_repo.get_by_hash(hothash)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        # Check if coldpreview exists
        if not getattr(photo, 'coldpreview_path', None):
            raise NotFoundError("Coldpreview", hothash)
        
        # Use coldpreview repository utility
        from utils.coldpreview_repository import ColdpreviewRepository
        repository = ColdpreviewRepository()
        
        # Delete from filesystem (need to construct full path from relative path)
        # We need to pass the hothash since that's what the delete method expects
        try:
            repository.delete_coldpreview_by_hash(hothash)
        except Exception:
            pass  # File might already be deleted, continue with database cleanup
        
        # Clear metadata from database
        setattr(photo, 'coldpreview_path', None)
        setattr(photo, 'coldpreview_width', None)
        setattr(photo, 'coldpreview_height', None)
        setattr(photo, 'coldpreview_size', None)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(photo)

