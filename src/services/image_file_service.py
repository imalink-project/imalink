"""
ImageFile Service - Simplified Business Logic for ImageFile operations

SIMPLIFIED ARCHITECTURE:
ImageFiles are immutable file records that only support two operations:
1. create_image_file_new_photo - Creates Photo + ImageFile (with visual data)
2. add_image_file_to_photo - Adds ImageFile to existing Photo (file metadata only)

ImageFiles cannot be:
- Listed independently (use Photos API instead)
- Updated (immutable file records)
- Deleted individually (delete via Photo cascade)
"""
from typing import Optional
from sqlalchemy.orm import Session
import hashlib
import imagehash
import io
from PIL import Image as PILImage
from datetime import datetime

from src.repositories.image_file_repository import ImageFileRepository
from src.repositories.photo_repository import PhotoRepository
from src.schemas.image_file_upload_schemas import (
    ImageFileNewPhotoRequest, ImageFileAddToPhotoRequest, ImageFileUploadResponse
)
from src.schemas.photo_schemas import PhotoCreateRequest
from src.core.exceptions import NotFoundError, DuplicateImageError, ValidationError
from src.models import ImageFile


class ImageFileService:
    """Simplified service for ImageFile creation and retrieval"""
    
    def __init__(self, db: Session):
        self.db = db
        self.image_file_repo = ImageFileRepository(db)
        self.photo_repo = PhotoRepository(db)
    
    def get_image_file_by_id(self, image_file_id: int, user_id: int) -> ImageFile:
        """
        Get ImageFile by ID (with user access validation)
        
        Args:
            image_file_id: ImageFile database ID
            user_id: User requesting access
        
        Returns:
            ImageFile object
            
        Raises:
            NotFoundError: If ImageFile not found or user lacks access
        """
        image_file = self.image_file_repo.get_by_id(image_file_id)
        if not image_file:
            raise NotFoundError("ImageFile", image_file_id)
        
        # Verify user access through Photo ownership
        if image_file.photo and image_file.photo.user_id != user_id:
            raise NotFoundError("ImageFile", image_file_id)
        
        return image_file
    
    def create_image_file_new_photo(self, image_data: ImageFileNewPhotoRequest, user_id: int) -> ImageFileUploadResponse:
        """
        Create ImageFile that will create a new Photo
        
        USE CASE: Uploading a completely new, unique photo
        - Hotpreview, exif_dict, perceptual_hash stored in Photo
        - ImageFile only stores file metadata
        
        WORKFLOW:
        1. Validate hotpreview data
        2. Generate photo_hothash from hotpreview (SHA256)
        3. Check if Photo already exists (if yes, raise DuplicateImageError)
        4. Create new Photo with hotpreview, exif_dict, perceptual_hash
        5. Create ImageFile with only file metadata
        6. Return success response
        """
        # 1. Validate hotpreview is provided
        if not image_data.hotpreview:
            raise ValidationError("hotpreview is required when creating new photo")
        
        # 2. Cast hotpreview to bytes
        if isinstance(image_data.hotpreview, str):
            hotpreview_bytes = image_data.hotpreview.encode('utf-8')
        else:
            hotpreview_bytes = image_data.hotpreview
        
        # 3. Generate hothash from hotpreview (SHA256)
        hothash = self._generate_hothash_from_hotpreview(hotpreview_bytes)
        
        # 4. Check if Photo already exists (user-scoped) - if yes, this is an error for this endpoint
        existing_photo = self.photo_repo.get_by_hash(hothash, user_id)
        if existing_photo:
            raise DuplicateImageError(f"Photo with this image already exists (hothash: {hothash[:8]}...)")
        
        # 5. Generate perceptual hash if not provided
        perceptual_hash = self._generate_perceptual_hash_if_missing(
            image_data.perceptual_hash, 
            hotpreview_bytes
        )
        
        # 6. Create new Photo + ImageFile
        image_file = self._create_new_photo_with_image_file(
            image_data, hothash, perceptual_hash, hotpreview_bytes, user_id
        )
        
        # 7. Commit transaction
        self.db.commit()
        self.db.refresh(image_file)
        
        # 8. Return success response
        return ImageFileUploadResponse(
            image_file_id=getattr(image_file, 'id'),
            filename=getattr(image_file, 'filename'),
            file_size=getattr(image_file, 'file_size', None),
            photo_hothash=hothash,
            photo_created=True,
            success=True,
            message="New photo created successfully"
        )
    
    def add_image_file_to_photo(self, image_data: ImageFileAddToPhotoRequest, user_id: int) -> ImageFileUploadResponse:
        """
        Add new ImageFile to an existing Photo
        
        USE CASE: Adding companion files (RAW, different resolution, etc.)
        - Photo already exists with visual data
        - ImageFile only stores file metadata (no hotpreview/exif/perceptual_hash)
        
        WORKFLOW:
        1. Validate that Photo exists and belongs to user
        2. Create ImageFile with only file metadata
        3. Return success response
        """
        # 1. Validate that Photo exists and belongs to user
        existing_photo = self.photo_repo.get_by_hash(image_data.photo_hothash, user_id)
        if not existing_photo:
            raise NotFoundError("Photo", image_data.photo_hothash)
        
        # 2. Create ImageFile for existing Photo (no visual data)
        image_file = self._create_image_file_for_existing_photo(image_data, existing_photo, user_id)
        
        # 3. Commit transaction
        self.db.commit()
        self.db.refresh(image_file)
        
        # 4. Return success response
        return ImageFileUploadResponse(
            image_file_id=getattr(image_file, 'id'),
            filename=getattr(image_file, 'filename'),
            file_size=getattr(image_file, 'file_size', None),
            photo_hothash=image_data.photo_hothash,
            photo_created=False,
            success=True,
            message="Image file added to existing photo successfully"
        )
    
    # ========== Private Helper Methods ==========
    
    def _create_new_photo_with_image_file(
        self, 
        image_data: ImageFileNewPhotoRequest, 
        hothash: str, 
        perceptual_hash: Optional[str], 
        hotpreview_bytes: bytes, 
        user_id: int
    ) -> ImageFile:
        """
        Create new Photo with visual data + ImageFile with file metadata
        """
        # 1. Create Photo with visual data
        photo_data_dict = {
            'hothash': hothash,
            'hotpreview': hotpreview_bytes,
            'exif_dict': image_data.exif_dict,
            'perceptual_hash': perceptual_hash,
            'taken_at': image_data.taken_at,
            'gps_latitude': image_data.gps_latitude,
            'gps_longitude': image_data.gps_longitude,
            # Extract width/height from EXIF if available
            'width': image_data.exif_dict.get('ImageWidth') if image_data.exif_dict else None,
            'height': image_data.exif_dict.get('ImageHeight') if image_data.exif_dict else None,
        }
        photo_data = PhotoCreateRequest(**photo_data_dict)
        photo = self.photo_repo.create(photo_data, user_id=user_id)
        
        # 2. Create ImageFile with only file metadata (no visual data)
        image_data_dict = {
            'filename': image_data.filename,
            'file_size': image_data.file_size,
            'photo_id': photo.id,  # Use integer photo_id instead of photo_hothash
            'import_session_id': image_data.import_session_id,
            'imported_time': datetime.utcnow(),
            'imported_info': image_data.imported_info,
            'local_storage_info': image_data.local_storage_info,
            'cloud_storage_info': image_data.cloud_storage_info,
        }
        
        image_file = self.image_file_repo.create(image_data_dict, user_id)
        
        return image_file
    
    def _create_image_file_for_existing_photo(
        self, 
        image_data: ImageFileAddToPhotoRequest,
        existing_photo,  # Photo object
        user_id: int
    ) -> ImageFile:
        """
        Create ImageFile for existing Photo (file metadata only)
        """
        image_data_dict = {
            'filename': image_data.filename,
            'file_size': image_data.file_size,
            'photo_id': existing_photo.id,  # Use integer photo_id instead of photo_hothash
            'import_session_id': image_data.import_session_id,
            'imported_time': datetime.utcnow(),
            'imported_info': image_data.imported_info,
            'local_storage_info': image_data.local_storage_info,
            'cloud_storage_info': image_data.cloud_storage_info,
        }
        
        image_file = self.image_file_repo.create(image_data_dict, user_id)
        
        return image_file
    
    def _generate_hothash_from_hotpreview(self, hotpreview_bytes: bytes) -> str:
        """Generate SHA256 hash from hotpreview bytes"""
        return hashlib.sha256(hotpreview_bytes).hexdigest()
    
    def _generate_perceptual_hash_if_missing(
        self, 
        provided_hash: Optional[str], 
        hotpreview_bytes: bytes
    ) -> Optional[str]:
        """Generate perceptual hash from hotpreview if not provided"""
        if provided_hash:
            return provided_hash
        
        try:
            # Generate perceptual hash from hotpreview
            img = PILImage.open(io.BytesIO(hotpreview_bytes))
            phash = imagehash.phash(img)
            return str(phash)
        except Exception:
            # Silently ignore perceptual hash generation errors
            return None
