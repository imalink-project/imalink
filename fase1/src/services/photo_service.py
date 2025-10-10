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
from repositories.image_repository import ImageRepository
from schemas.photo_schemas import (
    PhotoResponse, PhotoCreateRequest, PhotoUpdateRequest, 
    PhotoSearchRequest, PhotoRotateRequest, AuthorSummary,
    ImageFileSummary
)
from schemas.requests.photo_batch_requests import PhotoGroupBatchRequest, PhotoGroupRequest
from schemas.responses.photo_batch_responses import BatchPhotoResponse, PhotoGroupResult
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, DuplicatePhotoError, ValidationError
from models import Photo, Image


class PhotoService:
    """Service layer for Photo operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.photo_repo = PhotoRepository(db)
    
    async def get_photos(
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
    
    async def get_photo_by_hash(self, hothash: str) -> PhotoResponse:
        """Get single photo by hash"""
        photo = self.photo_repo.get_by_hash(hothash)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        return self._convert_to_response(photo)
    
    async def create_photo(self, photo_data: PhotoCreateRequest) -> PhotoResponse:
        """Create new photo with EXIF extraction from associated Images"""
        
        # Check for duplicate hash
        if self.photo_repo.exists_by_hash(photo_data.hothash):
            raise DuplicatePhotoError(f"Photo with hash {photo_data.hothash} already exists")
        
        # Validate tags if provided
        if photo_data.tags:
            self._validate_tags(photo_data.tags)
        
        # Create the photo (EXIF metadata should already be provided by caller)
        photo = self.photo_repo.create(photo_data)
        return self._convert_to_response(photo)
    
    async def update_photo(self, hothash: str, photo_data: PhotoUpdateRequest) -> PhotoResponse:
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
    
    async def create_photo_batch(self, batch_request: PhotoGroupBatchRequest) -> BatchPhotoResponse:
        """Create multiple photos with their associated images in batch with transaction handling"""
        start_time = time.time()
        results = []
        total_images_created = 0
        total_images_failed = 0
        total_images_added_to_existing = 0
        total_images_skipped_duplicate = 0
        photos_created = 0
        photos_failed = 0
        photos_duplicates = 0
        partial_duplicates = 0
        
        # Use database transaction for atomic batch processing
        try:
            for photo_group in batch_request.photo_groups:
                try:
                    # Process single photo group
                    result = await self._create_single_photo_group(photo_group, batch_request.author_id)
                    results.append(result)
                    
                    if result.success:
                        if result.is_duplicate:
                            photos_duplicates += 1
                            if result.partial_duplicate:
                                partial_duplicates += 1
                            total_images_added_to_existing += result.images_added_to_existing
                            total_images_skipped_duplicate += result.images_skipped_duplicate
                        else:
                            photos_created += 1
                        total_images_created += result.images_created
                    else:
                        photos_failed += 1
                        total_images_failed += result.images_failed
                        
                except Exception as e:
                    # Handle individual photo group failure
                    results.append(PhotoGroupResult(
                        success=False,
                        hothash=photo_group.hothash,
                        photo=None,
                        images_created=0,
                        is_duplicate=False,
                        existing_photo=None,
                        partial_duplicate=False,
                        images_added_to_existing=0,
                        images_skipped_duplicate=0,
                        error=f"Failed to create photo group: {str(e)}",
                        images_failed=len(photo_group.images)
                    ))
                    photos_failed += 1
                    total_images_failed += len(photo_group.images)
            
            # Commit all changes if no critical errors
            self.db.commit()
            
            processing_time = time.time() - start_time
            overall_success = photos_failed == 0
            
            return BatchPhotoResponse(
                success=overall_success,
                total_requested=len(batch_request.photo_groups),
                photos_created=photos_created,
                photos_failed=photos_failed,
                photos_duplicates=photos_duplicates,
                partial_duplicates=partial_duplicates,
                images_created=total_images_created,
                images_failed=total_images_failed,
                images_added_to_existing=total_images_added_to_existing,
                images_skipped_duplicate=total_images_skipped_duplicate,
                processing_time_seconds=processing_time,
                results=results,
                error=None
            )
            
        except Exception as e:
            # Rollback on critical error
            self.db.rollback()
            processing_time = time.time() - start_time
            
            return BatchPhotoResponse(
                success=False,
                total_requested=len(batch_request.photo_groups),
                photos_created=0,
                photos_failed=len(batch_request.photo_groups),
                photos_duplicates=0,
                partial_duplicates=0,
                images_created=0,
                images_failed=sum(len(group.images) for group in batch_request.photo_groups),
                images_added_to_existing=0,
                images_skipped_duplicate=0,
                processing_time_seconds=processing_time,
                results=[],
                error=f"Batch processing failed: {str(e)}"
            )
    
    async def _create_single_photo_group(self, photo_group: PhotoGroupRequest, default_author_id: Optional[int] = None) -> PhotoGroupResult:
        """Create a single photo with its associated images, handling duplicates intelligently"""
        try:
            # Generate consistent hash based on first image filename and metadata
            consistent_hash = self._generate_consistent_hash(photo_group)
            
            # Check if photo already exists with this consistent hash
            existing_photo = self.photo_repo.get_by_hash(consistent_hash)
            
            if existing_photo:
                # Photo exists - handle partial duplicates by adding missing files
                photo_group.hothash = consistent_hash  # Use consistent hash
                # Also update hothash on all images to match
                for img in photo_group.images:
                    img.hothash = consistent_hash
                return await self._handle_duplicate_photo(existing_photo, photo_group)
            
            # Photo doesn't exist - create new photo with all images
            photo_group.hothash = consistent_hash  # Use consistent hash
            # Also update hothash on all images to match
            for img in photo_group.images:
                img.hothash = consistent_hash
            return await self._create_new_photo_group(photo_group, default_author_id)
            
        except Exception as e:
            return PhotoGroupResult(
                success=False,
                hothash=photo_group.hothash,
                photo=None,
                images_created=0,
                is_duplicate=False,
                existing_photo=None,
                partial_duplicate=False,
                images_added_to_existing=0,
                images_skipped_duplicate=0,
                error=str(e),
                images_failed=len(photo_group.images)
            )

    def _generate_consistent_hash(self, photo_group: PhotoGroupRequest) -> str:
        """
        Generate a consistent hash for photo group based on metadata.
        This ensures the same photo will always get the same hash regardless of when it's imported.
        """
        import hashlib
        from pathlib import Path
        
        if not photo_group.images:
            raise ValueError("Photo group must contain at least one image")
        
        # Use the first image as the primary for hash generation
        primary_image = photo_group.images[0]
        
        # Normalize filename - use base name without path, consistent casing
        base_name = Path(primary_image.filename).stem.lower()
        extension = Path(primary_image.filename).suffix.lower()
        normalized_filename = f"{base_name}{extension}"
        
        # Create consistent hash input
        hash_input_parts = [
            normalized_filename,
            str(primary_image.file_size),
        ]
        
        # Add dimensions if available (for more precise deduplication)
        if photo_group.width and photo_group.height:
            hash_input_parts.extend([str(photo_group.width), str(photo_group.height)])
        
        # Join with consistent separator
        hash_input = "|".join(hash_input_parts)
        
        # Generate MD5 hash
        hash_bytes = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
        
        # Return first 32 characters (standard hothash length)
        return hash_bytes[:32]

    async def _handle_duplicate_photo(self, existing_photo, photo_group: PhotoGroupRequest) -> PhotoGroupResult:
        """Handle duplicate photo by adding any missing images to existing photo"""
        from repositories.image_repository import ImageRepository
        
        image_repo = ImageRepository(self.db)
        
        # Get existing image filenames for this photo
        existing_filenames = {img.filename for img in existing_photo.files}
        
        # Find new images that don't exist yet
        new_images = [img for img in photo_group.images if img.filename not in existing_filenames]
        
        if not new_images:
            # Complete duplicate - all files already exist
            return PhotoGroupResult(
                success=True,
                hothash=photo_group.hothash,
                photo=self._convert_to_response(existing_photo),
                images_created=0,
                is_duplicate=True,
                existing_photo=self._convert_to_response(existing_photo),
                partial_duplicate=False,
                images_added_to_existing=0,
                images_skipped_duplicate=len(photo_group.images),
                error=None,
                images_failed=0
            )
        
        # Partial duplicate - add missing files
        images_added = 0
        images_failed = 0
        
        for image_data in new_images:
            try:
                # Ensure the image uses the same hothash as existing photo
                image_data.hothash = existing_photo.hothash
                image = image_repo.create(image_data)
                images_added += 1
            except Exception as e:
                print(f"Failed to add image {image_data.filename} to existing photo: {str(e)}")
                images_failed += 1
        
        # Refresh the photo to include new images
        self.db.refresh(existing_photo)
        
        return PhotoGroupResult(
            success=True,
            hothash=photo_group.hothash,
            photo=self._convert_to_response(existing_photo),
            images_created=images_added,
            is_duplicate=True,
            existing_photo=self._convert_to_response(existing_photo),
            partial_duplicate=images_added > 0,
            images_added_to_existing=images_added,
            images_skipped_duplicate=len(photo_group.images) - len(new_images),
            error=None,
            images_failed=images_failed
        )

    async def _create_new_photo_group(self, photo_group: PhotoGroupRequest, default_author_id: Optional[int] = None) -> PhotoGroupResult:
        """Create a completely new photo with all its images"""
        from repositories.image_repository import ImageRepository
        
        # Extract metadata from first image's raw EXIF if available
        enhanced_photo_data = await self._extract_metadata_from_raw_exif_images(photo_group)
        
        # Generate hotpreview from the first JPEG file in storage
        hotpreview_data = await self._generate_hotpreview_from_storage(enhanced_photo_data)
        
        # Create PhotoCreateRequest with enhanced metadata
        photo_data = PhotoCreateRequest(
            hothash=enhanced_photo_data.hothash,
            hotpreview=hotpreview_data,
            width=enhanced_photo_data.width,
            height=enhanced_photo_data.height,
            taken_at=enhanced_photo_data.taken_at,
            gps_latitude=enhanced_photo_data.gps_latitude,
            gps_longitude=enhanced_photo_data.gps_longitude,
            title=enhanced_photo_data.title,
            description=enhanced_photo_data.description,
            tags=enhanced_photo_data.tags,
            rating=enhanced_photo_data.rating,
            import_session_id=enhanced_photo_data.import_session_id,
            author_id=default_author_id  # Use default author if provided
        )
        
        # Create the photo
        photo = self.photo_repo.create(photo_data)
        
        # Create associated images
        image_repo = ImageRepository(self.db)
        images_created = 0
        images_failed = 0
        
        for image_data in photo_group.images:
            try:
                # Create image and associate with photo
                image = image_repo.create(image_data)
                images_created += 1
            except Exception as e:
                images_failed += 1
        
        # Flush to ensure images are persisted before refresh
        self.db.flush()
        
        # Refresh photo to load associated images with eager loading
        from sqlalchemy.orm import selectinload
        self.db.refresh(photo, ['files'])
        
        # Convert to response
        photo_response = self._convert_to_response(photo)
        
        return PhotoGroupResult(
            success=True,
            hothash=photo_group.hothash,
            photo=photo_response,
            images_created=images_created,
            is_duplicate=False,
            existing_photo=None,
            partial_duplicate=False,
            images_added_to_existing=0,
            images_skipped_duplicate=0,
            error=None,
            images_failed=images_failed
        )
    
    async def delete_photo(self, hothash: str) -> bool:
        """Delete photo"""
        success = self.photo_repo.delete(hothash)
        if not success:
            raise NotFoundError("Photo", hothash)
        
        self.db.commit()
        return True
    
    async def rotate_photo(self, hothash: str, rotate_request: PhotoRotateRequest) -> PhotoResponse:
        """Rotate photo by 90 degrees"""
        photo = self.photo_repo.rotate_photo(hothash, rotate_request.clockwise)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        self.db.commit()
        return self._convert_to_response(photo)
    
    async def get_hotpreview(self, hothash: str) -> Optional[bytes]:
        """Get hotpreview data for photo"""
        hotpreview_data = self.photo_repo.get_hotpreview(hothash)
        if not hotpreview_data:
            raise NotFoundError("Hotpreview", hothash)
        
        return hotpreview_data
    
    async def search_photos(self, search_params: PhotoSearchRequest) -> PaginatedResponse[PhotoResponse]:
        """Search photos with advanced filtering"""
        return await self.get_photos(
            offset=search_params.offset,
            limit=search_params.limit,
            search_params=search_params
        )
    
    async def get_photo_statistics(self) -> Dict[str, Any]:
        """Get photo collection statistics"""
        return self.photo_repo.get_statistics()
    
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
        if photo.files:
            for image_file in photo.files:
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
            user_rotation=getattr(photo, 'user_rotation', 0),
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
    
    async def _extract_metadata_from_raw_exif_images(self, photo_group: PhotoGroupRequest) -> PhotoGroupRequest:
        """
        Extract EXIF metadata from raw EXIF bytes in images and enhance PhotoGroupRequest
        
        This method uses the ImageProcessor to extract metadata from raw EXIF data
        instead of relying on frontend-parsed metadata.
        """
        from services.importing.image_processor import ImageProcessor
        
        processor = ImageProcessor()
        
        # Find the first image with raw EXIF data
        primary_image = None
        raw_exif_bytes = None
        
        for image in photo_group.images:
            if image.exif_data and len(image.exif_data) > 0:
                primary_image = image
                raw_exif_bytes = image.exif_data
                break
        
        if raw_exif_bytes and primary_image:
            print(f"Extracting metadata from raw EXIF for {primary_image.filename}")
            
            # Use existing dimensions if available, otherwise use defaults
            width = photo_group.width or 0
            height = photo_group.height or 0
            
            try:
                # Extract metadata using ImageProcessor
                metadata = processor.extract_metadata_from_raw_exif(raw_exif_bytes, width, height)
                
                # Create enhanced PhotoGroupRequest with extracted metadata
                enhanced_group = photo_group.model_copy()
                
                # Update with extracted metadata (only if not already provided)
                if not enhanced_group.width and metadata.width:
                    enhanced_group.width = metadata.width
                if not enhanced_group.height and metadata.height:
                    enhanced_group.height = metadata.height
                if not enhanced_group.taken_at and metadata.taken_at:
                    enhanced_group.taken_at = metadata.taken_at
                if not enhanced_group.gps_latitude and metadata.gps_latitude:
                    enhanced_group.gps_latitude = metadata.gps_latitude
                if not enhanced_group.gps_longitude and metadata.gps_longitude:
                    enhanced_group.gps_longitude = metadata.gps_longitude
                
                print(f"  Enhanced metadata: {metadata.width}x{metadata.height}, "
                      f"taken: {metadata.taken_at}, GPS: {metadata.gps_latitude}, {metadata.gps_longitude}")
                
                return enhanced_group
                
            except Exception as e:
                print(f"Failed to extract metadata from raw EXIF: {e}")
        else:
            print(f"No raw EXIF data found in images for {photo_group.hothash}")
        
        # Return original photo group if no EXIF processing possible
        return photo_group

    async def _generate_hotpreview_from_storage(self, photo_group: PhotoGroupRequest) -> Optional[str]:
        """
        Generate hotpreview (base64 JPEG thumbnail) from the first JPEG file in storage.
        Returns base64-encoded JPEG data suitable for inline display.
        """
        import os
        from pathlib import Path
        from core.config import settings
        from PIL import Image, ImageOps
        from io import BytesIO
        import base64
        
        # Find first JPEG file
        jpeg_image = None
        for image in photo_group.images:
            ext = Path(image.filename).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                jpeg_image = image
                break
        
        if not jpeg_image:
            print(f"No JPEG file found for preview generation in {photo_group.hothash}")
            return None
        
        # Get import session to find storage location
        from repositories.import_session_repository import ImportSessionRepository
        from core.config import Config
        session_repo = ImportSessionRepository(self.db)
        
        if not photo_group.import_session_id:
            print(f"No import session ID for {photo_group.hothash}")
            return None
            
        import_session = session_repo.get_import_by_id(photo_group.import_session_id)
        if not import_session or not import_session.storage_name:
            print(f"No storage name found for import session {photo_group.import_session_id}")
            return None
        
        # Build file path - storage_name is the directory name under STORAGE_ROOT
        storage_path = Path(Config.STORAGE_ROOT) / import_session.storage_name / jpeg_image.filename
        
        if not storage_path.exists():
            print(f"File not found for preview: {storage_path}")
            return None
        
        try:
            # Open image and apply EXIF rotation
            with Image.open(storage_path) as img:
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail (max 300x300, maintain aspect ratio)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # Convert to RGB for consistent output
                img = img.convert('RGB')
                
                # Convert to JPEG bytes
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                jpeg_bytes = buffer.getvalue()
                
                # Convert to base64 string (without data URL prefix)
                base64_str = base64.b64encode(jpeg_bytes).decode('utf-8')
                
                print(f"Generated hotpreview for {jpeg_image.filename}: {len(base64_str)} chars")
                return base64_str
                
        except Exception as e:
            print(f"Failed to generate hotpreview for {jpeg_image.filename}: {e}")
            return None


