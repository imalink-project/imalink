"""
Image Service - Business Logic Layer for Image operations
Orchestrates image operations and implements business rules
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pathlib import Path
import json
import hashlib
import base64

from repositories.image_repository import ImageRepository
from repositories.photo_repository import PhotoRepository
from schemas.image_schemas import (
    ImageResponse, ImageCreateRequest, ImageUpdateRequest, 
    ImageSearchRequest, AuthorSummary
)
from schemas.photo_schemas import PhotoCreateRequest
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, DuplicateImageError, ValidationError
from models import Photo, Image


# Placeholder ImageProcessor class (would be implemented separately)
class ImageProcessor:
    """Image processing utilities"""
    
    async def has_raw_companion(self, file_path: str) -> bool:
        """Check if image has RAW companion file"""
        # TODO: Implement RAW companion detection
        return False
    
    async def can_generate_thumbnail(self, file_path: str) -> bool:
        """Check if thumbnail can be generated"""
        return Path(file_path).exists()
    
    async def generate_thumbnail(self, file_path: str) -> Optional[bytes]:
        """Generate thumbnail for image with EXIF rotation and stripped metadata"""
        try:
            from PIL import Image, ImageOps
            import io
            
            if not Path(file_path).exists():
                return None
                
            # Open and resize image to thumbnail size
            with Image.open(file_path) as img:
                # CRITICAL: Apply EXIF rotation before any processing
                img_fixed = ImageOps.exif_transpose(img.copy())
                
                # Strip EXIF data (not needed in thumbnails)
                if img_fixed and hasattr(img_fixed, 'info') and img_fixed.info:
                    img_fixed.info.pop('exif', None)
                
                # Convert to RGB if needed (for JPEG output)  
                if img_fixed and img_fixed.mode in ('RGBA', 'LA', 'P'):
                    img_fixed = img_fixed.convert('RGB')
                
                # Create thumbnail (maintaining aspect ratio)
                if img_fixed:
                    img_fixed.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    
                    # Save as JPEG bytes
                    thumbnail_io = io.BytesIO()
                    img_fixed.save(thumbnail_io, format='JPEG', quality=85, optimize=True)
                    return thumbnail_io.getvalue()
                
                return None
                
        except Exception as e:
            print(f"Error generating thumbnail for {file_path}: {e}")
            return None
    
    async def get_pool_image(self, file_path: str, pool_size: str, rotation: int) -> Optional[str]:
        """Get or create pooled image"""
        # TODO: Implement pool image generation
        return file_path
    
    async def cleanup_image_files(self, file_path: str, image_id: int) -> None:
        """Clean up image files"""
        # TODO: Implement file cleanup
        pass
    
    async def invalidate_pool_cache(self, image_id: int) -> None:
        """Invalidate pool cache"""
        # TODO: Implement cache invalidation
        pass


class ImageService:
    """Service class for Image business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.image_repo = ImageRepository(db)
        self.photo_repo = PhotoRepository(db)
        self.image_processor = ImageProcessor()
    
    async def get_images(
        self, 
        offset: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None,
        search_params: Optional[ImageSearchRequest] = None
    ) -> PaginatedResponse[ImageResponse]:
        """Get paginated list of images with optional filtering"""
        
        # Get images and total count
        images = self.image_repo.get_images(offset, limit, author_id, search_params)
        total = self.image_repo.count_images(author_id, search_params)
        
        # Convert to response models with business logic
        image_responses = []
        for image in images:
            image_response = await self._convert_to_response(image)
            image_responses.append(image_response)
        
        return create_paginated_response(
            data=image_responses,
            total=total,
            offset=offset,
            limit=limit
        )
    
    async def get_image_by_id(self, image_id: int) -> ImageResponse:
        """Get specific image by ID"""
        image = self.image_repo.get_by_id(image_id)
        if not image:
            raise NotFoundError("Image", image_id)
        
        return await self._convert_to_response(image)
    
    async def create_image(self, image_data: ImageCreateRequest) -> ImageResponse:
        """Create new image with business logic validation"""
        
        # Business Logic: No duplicate check needed - Images are unique files
        # Duplicate detection happens at Photo level via hothash
        
        # Create image record
        image = self.image_repo.create(image_data)
        
        return await self._convert_to_response(image)
    
    async def create_image_with_photo(self, image_data: ImageCreateRequest) -> ImageResponse:
        """
        Create new image with automatic Photo creation/association
        
        New architecture: Images drive Photo creation
        - Image has hotpreview (thumbnail) - REQUIRED
        - Photo.hothash automatically generated from Image.hotpreview via SHA256
        - First Image with new hotpreview → creates new Photo
        - Subsequent Images with same hotpreview → added to existing Photo
        
        Flow:
        1. Validate hotpreview is provided
        2. Generate hothash from hotpreview (SHA256)
        3. Check if Photo with this hothash exists
        4. If not exists → create new Photo
        5. Create Image with photo_hothash
        """
        
        # 1. Validate hotpreview is provided
        if not image_data.hotpreview:
            raise ValidationError("hotpreview is required when creating Image")
        
        # 2. Generate hothash from hotpreview
        hothash = await self._generate_hothash_from_hotpreview(image_data.hotpreview)
        
        # 3. Check if Photo exists
        existing_photo = self.photo_repo.get_by_hash(hothash)
        
        # 4. If Photo doesn't exist, create it
        if not existing_photo:
            # Extract metadata from Image for Photo creation
            photo_data = await self._extract_photo_metadata_from_image(image_data, hothash)
            
            # Create Photo
            photo = self.photo_repo.create(photo_data)
        
        # 5. Create Image with the generated photo_hothash
        image_data_dict = image_data.model_dump()
        image_data_dict['photo_hothash'] = hothash
        
        image = self.image_repo.create(image_data_dict)
        
        return await self._convert_to_response(image)
    
    async def update_image(
        self, 
        image_id: int, 
        update_data: ImageUpdateRequest
    ) -> ImageResponse:
        """Update existing image"""
        
        # Check image exists
        existing_image = self.image_repo.get_by_id(image_id)
        if not existing_image:
            raise NotFoundError("Image", image_id)
        
        # Convert update data to dict (only Image model fields)
        update_dict = update_data.dict(exclude_unset=True)
        
        # Update image
        updated_image = self.image_repo.update(image_id, update_dict)
        if not updated_image:
            raise NotFoundError("Image", image_id)
        
        return await self._convert_to_response(updated_image)
    
    async def delete_image(self, image_id: int) -> bool:
        """Delete image with cleanup"""
        
        # Check image exists
        image = self.image_repo.get_by_id(image_id)
        if not image:
            raise NotFoundError("Image", image_id)
        
        # Business Logic: Cleanup associated files
        await self._cleanup_image_files(image)
        
        # Delete from database
        return self.image_repo.delete(image_id)
    
    # NOTE: rotate_image removed - rotation is a Photo-level concern, not Image-level
    
    async def get_image_thumbnail(self, image_id: int) -> Optional[bytes]:
        """Get image thumbnail binary data"""
        image = self.image_repo.get_by_id(image_id)
        if not image:
            raise NotFoundError("Image", image_id)
        
        # Return stored thumbnail or generate on demand
        if getattr(image, 'thumbnail', None):
            return getattr(image, 'thumbnail')
        
        # Business Logic: Generate thumbnail on demand
        return await self.image_processor.generate_thumbnail(getattr(image, 'file_path', ''))
    
    async def search_images(self, search_request: ImageSearchRequest) -> PaginatedResponse[ImageResponse]:
        """Search images with advanced criteria"""
        
        # Business Logic: Validate search parameters
        if search_request.rating_min and search_request.rating_max:
            if search_request.rating_min > search_request.rating_max:
                raise ValidationError("rating_min cannot be greater than rating_max")
        
        if search_request.taken_after and search_request.taken_before:
            if search_request.taken_after > search_request.taken_before:
                raise ValidationError("taken_after cannot be after taken_before")
        
        # Use repository for search
        return await self.get_images(
            offset=search_request.offset,
            limit=search_request.limit,
            search_params=search_request
        )
    
    async def get_image_pool(self, image_id: int, pool_size: str) -> Optional[str]:
        """Get pooled image path for specific size"""
        image = self.image_repo.get_by_id(image_id)
        if not image:
            raise NotFoundError("Image", image_id)
        
        # NOTE: user_rotation now in Photo model, not Image
        # For pool image generation, we don't apply rotation (it's applied in Photo display)
        # Business Logic: Generate pool image if needed
        return await self.image_processor.get_pool_image(
            getattr(image, 'file_path', ''), 
            pool_size, 
            0  # No rotation at Image level
        )
    
    async def get_recent_images(self, limit: int = 50) -> List[ImageResponse]:
        """Get recently imported images"""
        images = self.image_repo.get_recent_images(limit)
        
        image_responses = []
        for image in images:
            image_response = await self._convert_to_response(image)
            image_responses.append(image_response)
        
        return image_responses
    
    async def get_images_by_author(self, author_id: int, limit: int = 100) -> List[ImageResponse]:
        """Get images by specific author"""
        images = self.image_repo.get_images_by_author(author_id, limit)
        
        image_responses = []
        for image in images:
            image_response = await self._convert_to_response(image)
            image_responses.append(image_response)
        
        return image_responses
    
    # Private helper methods
    
    async def _convert_to_response(self, image) -> ImageResponse:
        """Convert database model to response model with business logic"""
        
        # Business Logic: Detect RAW companion
        has_raw_companion = False
        if hasattr(image, 'filename') and image.filename:
            # Note: We no longer have full file path, only filename
            # For now, disable RAW companion detection
            has_raw_companion = False
        
        # Business Logic: Check thumbnail availability
        # Note: We no longer have full file path, so disable thumbnail generation for now
        has_thumbnail = bool(getattr(image, 'thumbnail', None))
        
        # Convert author if present (from Photo relationship)
        author_summary = None
        if hasattr(image, 'photo') and image.photo and hasattr(image.photo, 'author') and image.photo.author:
            author_summary = AuthorSummary(
                id=image.photo.author.id,
                name=image.photo.author.name
            )
        
        # Image model doesn't have tags - they're in Photo model
        tags = []
        if image.photo and image.photo.tags:
            tags = image.photo.tags if isinstance(image.photo.tags, list) else []
        
        # Compute derived values from filename
        filename = getattr(image, 'filename', '')
        from utils.file_utils import get_file_format
        computed_format = get_file_format(filename) if filename else None
        
        return ImageResponse(
            id=getattr(image, 'id'),
            photo_hothash=getattr(image, 'photo_hothash', None),
            filename=filename,
            file_size=getattr(image, 'file_size', None),
            has_hotpreview=bool(getattr(image, 'hotpreview', None)),
            # Computed fields
            file_format=computed_format,
            file_path=None,  # Could be computed by storage service if needed
            original_filename=filename,  # Could be computed from import session if needed
            created_at=getattr(image, 'created_at'),
            taken_at=None,  # taken_at is in Photo model, not Image
            width=None,  # width/height are in Photo model, not Image
            height=None,
            gps_latitude=None,  # GPS is in Photo model, not Image
            gps_longitude=None,
            has_gps=False,  # GPS is in Photo model
            # NOTE: title, description, tags, rating, user_rotation in Photo model
            author=author_summary,
            author_id=None,  # author_id is in Photo model
            # import_source available via import_session relationship if needed
            has_raw_companion=computed_format in ['cr2', 'nef', 'arw', 'dng', 'orf', 'rw2', 'raw'] if computed_format else False
        )
    
    async def _cleanup_image_files(self, image) -> None:
        """Clean up files associated with image"""
        # Note: We no longer have full file path, so disable file cleanup for now
        # await self.image_processor.cleanup_image_files(image.filename, image.id)
        pass
    
    async def _invalidate_pool_cache(self, image_id: int) -> None:
        """Invalidate cached pool images for image"""
        await self.image_processor.invalidate_pool_cache(image_id)
    
    async def _generate_hothash_from_hotpreview(self, hotpreview: bytes) -> str:
        """
        Generate hothash from hotpreview (thumbnail)
        Uses SHA256 hash of hotpreview bytes
        """
        hothash = hashlib.sha256(hotpreview).hexdigest()
        return hothash
    
    async def _generate_hothash_from_image(self, image_data: ImageCreateRequest) -> str:
        """
        Generate hothash from image data
        Uses filename and file_size to create a unique hash
        """
        # Create hash from available data
        hash_input = f"{image_data.filename}_{image_data.file_size or 0}"
        hothash = hashlib.sha256(hash_input.encode()).hexdigest()
        return hothash
    
    async def _extract_photo_metadata_from_image(
        self, 
        image_data: ImageCreateRequest, 
        hothash: str
    ) -> PhotoCreateRequest:
        """
        Extract Photo metadata from Image data
        This creates the Photo record for the first (master) Image
        NOTE: hotpreview is stored in Image, not Photo
        """
        # Extract EXIF metadata if available
        width = None
        height = None
        taken_at = None
        gps_latitude = None
        gps_longitude = None
        
        if image_data.exif_data:
            # Parse EXIF data to extract metadata
            # This is a simplified version - in production, use proper EXIF parsing
            try:
                from PIL import Image as PILImage
                from PIL.ExifTags import TAGS
                import io
                
                # Try to extract dimensions and other metadata from EXIF
                # Note: This is placeholder logic - real implementation would be more robust
                pass
            except Exception as e:
                print(f"Warning: Failed to parse EXIF data: {e}")
        
        # Create PhotoCreateRequest with extracted data (NO hotpreview)
        return PhotoCreateRequest(
            hothash=hothash,
            width=width,
            height=height,
            taken_at=taken_at,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            title=None,
            description=None,
            tags=[],
            rating=0,
            author_id=None,
            import_session_id=image_data.import_session_id
        )