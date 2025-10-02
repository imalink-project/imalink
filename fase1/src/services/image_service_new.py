"""
Image Service - Business Logic Layer for Image operations
Orchestrates image operations and implements business rules
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pathlib import Path
import json

from repositories.image_repository import ImageRepository
from schemas.image_schemas import (
    ImageResponse, ImageCreateRequest, ImageUpdateRequest, 
    ImageSearchRequest, ImageRotateRequest, AuthorSummary
)
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, DuplicateImageError, ValidationError


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
        """Generate thumbnail for image"""
        # TODO: Implement thumbnail generation
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
        
        # Business Logic: Check for duplicates
        if self.image_repo.exists_by_hash(image_data.image_hash):
            raise DuplicateImageError(f"Image with hash {image_data.image_hash} already exists")
        
        # Business Logic: Validate file exists
        if not Path(image_data.file_path).exists():
            raise ValidationError(f"File not found: {image_data.file_path}")
        
        # Create image record
        image = self.image_repo.create(image_data)
        
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
        
        # Business Logic: Validate rating range
        if update_data.rating is not None and not (1 <= update_data.rating <= 5):
            raise ValidationError("Rating must be between 1 and 5")
        
        # Business Logic: Normalize tags
        update_dict = update_data.dict(exclude_unset=True)
        if 'tags' in update_dict and update_dict['tags'] is not None:
            # Normalize tags: lowercase, trim, remove duplicates
            normalized_tags = []
            for tag in update_dict['tags']:
                tag = tag.strip().lower()
                if tag and tag not in normalized_tags:
                    normalized_tags.append(tag)
            update_dict['tags'] = normalized_tags
        
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
    
    async def rotate_image(
        self, 
        image_id: int, 
        rotate_request: ImageRotateRequest
    ) -> ImageResponse:
        """Rotate image (update user rotation)"""
        
        # Check image exists
        existing_image = self.image_repo.get_by_id(image_id)
        if not existing_image:
            raise NotFoundError("Image", image_id)
        
        # Rotate image
        rotated_image = self.image_repo.rotate_image(image_id, rotate_request.clockwise)
        if not rotated_image:
            raise NotFoundError("Image", image_id)
        
        # Business Logic: Invalidate cached pool images
        await self._invalidate_pool_cache(image_id)
        
        return await self._convert_to_response(rotated_image)
    
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
        
        # Business Logic: Generate pool image if needed
        return await self.image_processor.get_pool_image(
            getattr(image, 'file_path', ''), 
            pool_size, 
            getattr(image, 'user_rotation', 0) or 0
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

    async def get_image_statistics(self) -> Dict[str, Any]:
        """Get comprehensive image statistics"""
        base_stats = self.image_repo.get_statistics()
        
        # Business Logic: Add computed statistics
        base_stats.update({
            "total_size_mb": round(base_stats["total_size_bytes"] / (1024 * 1024), 2),
            "avg_image_size_mb": (
                round(base_stats["total_size_bytes"] / base_stats["total_images"] / (1024 * 1024), 2) 
                if base_stats["total_images"] > 0 else 0
            ),
            "gps_percentage": (
                round(base_stats["images_with_gps"] / base_stats["total_images"] * 100, 1)
                if base_stats["total_images"] > 0 else 0
            )
        })
        
        return base_stats
    
    # Private helper methods
    
    async def _convert_to_response(self, image) -> ImageResponse:
        """Convert database model to response model with business logic"""
        
        # Business Logic: Detect RAW companion
        has_raw_companion = False
        if image.file_path:
            has_raw_companion = await self.image_processor.has_raw_companion(image.file_path)
        
        # Business Logic: Check thumbnail availability
        has_thumbnail = bool(image.thumbnail) or await self.image_processor.can_generate_thumbnail(image.file_path)
        
        # Convert author if present
        author_summary = None
        if image.author:
            author_summary = AuthorSummary(
                id=image.author.id,
                name=image.author.name
            )
        
        # Parse tags from JSON string
        tags = []
        if image.tags:
            try:
                tags = json.loads(image.tags)
            except (json.JSONDecodeError, TypeError):
                # Fallback: split by comma
                tags = [tag.strip() for tag in str(image.tags).split(',') if tag.strip()]
        
        return ImageResponse(
            id=getattr(image, 'id'),
            image_hash=getattr(image, 'image_hash', ''),
            original_filename=getattr(image, 'original_filename', ''),
            file_path=getattr(image, 'file_path', ''),
            file_size=getattr(image, 'file_size', None),
            file_format=getattr(image, 'file_format', None),
            created_at=getattr(image, 'created_at'),
            taken_at=getattr(image, 'taken_at', None),
            width=getattr(image, 'width', None),
            height=getattr(image, 'height', None),
            gps_latitude=getattr(image, 'gps_latitude', None),
            gps_longitude=getattr(image, 'gps_longitude', None),
            has_gps=bool(getattr(image, 'gps_latitude', None) and getattr(image, 'gps_longitude', None)),
            title=getattr(image, 'title', None),
            description=getattr(image, 'description', None),
            tags=tags,
            rating=getattr(image, 'rating', None),
            user_rotation=getattr(image, 'user_rotation', 0) or 0,
            author=author_summary,
            author_id=getattr(image, 'author_id', None),
            import_source=getattr(image, 'import_source', None),
            has_raw_companion=has_raw_companion,
            has_thumbnail=has_thumbnail
        )
    
    async def _cleanup_image_files(self, image) -> None:
        """Clean up files associated with image"""
        await self.image_processor.cleanup_image_files(image.file_path, image.id)
    
    async def _invalidate_pool_cache(self, image_id: int) -> None:
        """Invalidate cached pool images for image"""
        await self.image_processor.invalidate_pool_cache(image_id)