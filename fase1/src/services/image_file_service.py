"""
ImageFile Service - Business Logic Layer for ImageFile operations
Orchestrates image_file operations and implements business rules
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pathlib import Path
import json
import hashlib
import base64
from PIL import Image as PILImage
import imagehash
import io

from repositories.image_file_repository import ImageFileRepository
from repositories.photo_repository import PhotoRepository
from schemas.image_file_schemas import (
    ImageFileResponse, ImageFileCreateRequest, ImageFileUpdateRequest, 
    ImageFileSearchRequest, StorageInfoUpdateRequest
)
from schemas.photo_schemas import PhotoCreateRequest
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, DuplicateImageError, ValidationError
from models import Photo, ImageFile


# Placeholder ImageProcessor class (would be implemented separately)
class ImageProcessor:
    """ImageFile processing utilities"""
    
    def has_raw_companion(self, file_path: str) -> bool:
        """Check if image_file has RAW companion file"""
        # TODO: Implement RAW companion detection
        return False
    
    def can_generate_hotpreview(self, file_path: str) -> bool:
        """Check if hotpreview can be generated"""
        return Path(file_path).exists()
    
    def generate_hotpreview(self, file_path: str) -> Optional[bytes]:
        """Generate hotpreview for image_file with EXIF rotation and stripped metadata"""
        try:
            from PIL import ImageFile, ImageOps
            import io
            
            if not Path(file_path).exists():
                return None
                
            # Open and resize image_file to hotpreview size
            with ImageFile.open(file_path) as img:
                # CRITICAL: Apply EXIF rotation before any processing
                img_fixed = ImageOps.exif_transpose(img.copy())
                
                # Strip EXIF data (not needed in hotpreviews)
                if img_fixed and hasattr(img_fixed, 'info') and img_fixed.info:
                    img_fixed.info.pop('exif', None)
                
                # Convert to RGB if needed (for JPEG output)  
                if img_fixed and img_fixed.mode in ('RGBA', 'LA', 'P'):
                    img_fixed = img_fixed.convert('RGB')
                
                # Create hotpreview using PIL's thumbnail method (maintaining aspect ratio)
                if img_fixed:
                    img_fixed.thumbnail((200, 200), ImageFile.Resampling.LANCZOS)
                    
                    # Save as JPEG bytes
                    hotpreview_io = io.BytesIO()
                    img_fixed.save(hotpreview_io, format='JPEG', quality=85, optimize=True)
                    return hotpreview_io.getvalue()
                
                return None
                
        except Exception as e:
            print(f"Error generating hotpreview for {file_path}: {e}")
            return None
    
    def cleanup_image_files(self, file_path: str, image_id: int) -> None:
        """Clean up image_file files"""
        # TODO: Implement file cleanup
        pass


class ImageFileService:
    """Service class for ImageFile business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.image_file_repo = ImageFileRepository(db)
        self.photo_repo = PhotoRepository(db)
        self.image_processor = ImageProcessor()
    
    def get_image_files(
        self, 
        offset: int = 0, 
        limit: int = 100,
        search_params: Optional[ImageFileSearchRequest] = None
    ) -> PaginatedResponse[ImageFileResponse]:
        """Get paginated list of images with optional filtering"""
        
        # Get images and total count
        images = self.image_file_repo.get_image_files(offset, limit, search_params)
        total = self.image_file_repo.count_images(search_params)
        
        # Convert to response models with business logic
        image_responses = []
        for image_file in images:
            image_response = self._convert_to_response(image_file)
            image_responses.append(image_response)
        
        return create_paginated_response(
            data=image_responses,
            total=total,
            offset=offset,
            limit=limit
        )
    
    def get_image_file_by_id(self, image_id: int) -> ImageFileResponse:
        """Get specific image_file by ID"""
        image_file = self.image_file_repo.get_by_id(image_id)
        if not image_file:
            raise NotFoundError("ImageFile", image_id)
        
        return self._convert_to_response(image_file)
    
    def create_image_file(self, image_data: ImageFileCreateRequest) -> ImageFileResponse:
        """Create new image_file with business logic validation"""
        
        # Business Logic: No duplicate check needed - Images are unique files
        # Duplicate detection happens at Photo level via hothash
        
        # Create image_file record
        image_file = self.image_file_repo.create(image_data)
        
        return self._convert_to_response(image_file)
    
    def create_image_file_with_photo(self, image_data: ImageFileCreateRequest) -> ImageFileResponse:
        """
        Create new image_file with automatic Photo creation/association
        
        New architecture: Images drive Photo creation
        - ImageFile has hotpreview - REQUIRED
        - Photo.hothash automatically generated from ImageFile.hotpreview via SHA256
        - First ImageFile with new hotpreview → creates new Photo
        - Subsequent Images with same hotpreview → added to existing Photo
        
        Flow:
        1. Validate hotpreview is provided
        2. Generate hothash from hotpreview (SHA256)
        3. Check if Photo with this hothash exists
        4. If not exists → create new Photo
        5. Create ImageFile with photo_hothash
        """
        
        # 1. Validate hotpreview is provided
        if not image_data.hotpreview:
            raise ValidationError("hotpreview is required when creating ImageFile")
        
        # 2. Generate hothash from hotpreview
        hothash = self._generate_hothash_from_hotpreview(image_data.hotpreview)
        
        # 2.5. Generate perceptual hash if not provided
        if not image_data.perceptual_hash:
            perceptual_hash = self._generate_perceptual_hash_from_hotpreview(image_data.hotpreview)
        else:
            perceptual_hash = image_data.perceptual_hash
        
        # 3. Check if Photo exists
        existing_photo = self.photo_repo.get_by_hash(hothash)
        
        # 4. If Photo doesn't exist, create it
        if not existing_photo:
            # Extract metadata from ImageFile for Photo creation
            photo_data = self._extract_photo_metadata_from_image(image_data, hothash)
            
            # Create Photo
            photo = self.photo_repo.create(photo_data)
        
        # 5. Create ImageFile with the generated photo_hothash and perceptual_hash
        image_data_dict = image_data.model_dump()
        image_data_dict['photo_hothash'] = hothash
        image_data_dict['perceptual_hash'] = perceptual_hash
        
        # Set imported_time automatically if not provided
        if 'imported_time' not in image_data_dict or not image_data_dict['imported_time']:
            from datetime import datetime
            image_data_dict['imported_time'] = datetime.utcnow()
        
        image_file = self.image_file_repo.create(image_data_dict)
        
        return self._convert_to_response(image_file)
    
    def update_image_file(
        self, 
        image_id: int, 
        update_data: ImageFileUpdateRequest
    ) -> ImageFileResponse:
        """Update existing image_file"""
        
        # Check image_file exists
        existing_image = self.image_file_repo.get_by_id(image_id)
        if not existing_image:
            raise NotFoundError("ImageFile", image_id)
        
        # Convert update data to dict (only ImageFile model fields)
        update_dict = update_data.dict(exclude_unset=True)
        
        # Update image_file
        updated_image = self.image_file_repo.update(image_id, update_dict)
        if not updated_image:
            raise NotFoundError("ImageFile", image_id)
        
        return self._convert_to_response(updated_image)
    
    def delete_image_file(self, image_id: int) -> bool:
        """Delete image_file with cleanup"""
        
        # Check image_file exists
        image_file = self.image_file_repo.get_by_id(image_id)
        if not image_file:
            raise NotFoundError("ImageFile", image_id)
        
        # Business Logic: Cleanup associated files
        self._cleanup_image_files(image_file)
        
        # Delete from database
        return self.image_file_repo.delete(image_id)
    
    # NOTE: rotate_image removed - rotation is a Photo-level concern, not ImageFile-level
    
    def get_image_hotpreview(self, image_id: int) -> Optional[bytes]:
        """Get image_file hotpreview binary data"""
        image_file = self.image_file_repo.get_by_id(image_id)
        if not image_file:
            raise NotFoundError("ImageFile", image_id)
        
        # Return stored hotpreview
        if getattr(image_file, 'hotpreview', None):
            return getattr(image_file, 'hotpreview')
        
        # Business Logic: Return hotpreview if available
        if getattr(image_file, 'hotpreview', None):
            return getattr(image_file, 'hotpreview')
        
        return None
    
    # NOTE: search_images removed - use get_image_files (list_images) with search_params instead
    # The standard list method already supports filtering and searching
    
    # NOTE: get_recent_images removed - use list_images with sort_by=created_at instead
    # NOTE: get_image_files_by_author removed - author is a Photo-level concern, not ImageFile-level
    
    # Private helper methods
    
    def _convert_to_response(self, image_file) -> ImageFileResponse:
        """Convert database model to response model with business logic"""
        
        # Business Logic: Detect RAW companion
        has_raw_companion = False
        if hasattr(image_file, 'filename') and image_file.filename:
            # Note: We no longer have full file path, only filename
            # For now, disable RAW companion detection
            has_raw_companion = False
        
        # Business Logic: Check hotpreview availability
        # Note: We no longer have full file path, so hotpreview is always stored
        has_hotpreview = bool(getattr(image_file, 'hotpreview', None))
        
        # NOTE: author removed - author is a Photo-level concern, not ImageFile-level
        
        # ImageFile model doesn't have tags - they're in Photo model
        tags = []
        if image_file.photo and image_file.photo.tags:
            tags = image_file.photo.tags if isinstance(image_file.photo.tags, list) else []
        
        # Compute derived values from filename
        filename = getattr(image_file, 'filename', '')
        from utils.file_utils import get_file_format
        computed_format = get_file_format(filename) if filename else None
        
        return ImageFileResponse(
            id=getattr(image_file, 'id'),
            photo_hothash=getattr(image_file, 'photo_hothash', None),
            filename=filename,
            file_size=getattr(image_file, 'file_size', None),
            has_hotpreview=bool(getattr(image_file, 'hotpreview', None)),
            perceptual_hash=getattr(image_file, 'perceptual_hash', None),
            
            # NEW - Import tracking fields
            import_session_id=getattr(image_file, 'import_session_id', None),
            imported_time=getattr(image_file, 'imported_time', None),
            imported_info=getattr(image_file, 'imported_info', None),
            
            # NEW - Storage location fields
            local_storage_info=getattr(image_file, 'local_storage_info', None),
            cloud_storage_info=getattr(image_file, 'cloud_storage_info', None),
            
            # Computed fields
            file_format=computed_format,
            file_path=None,  # Could be computed by storage service if needed
            original_filename=filename,  # Could be computed from import session if needed
            created_at=getattr(image_file, 'created_at'),
            taken_at=None,  # taken_at is in Photo model, not ImageFile
            width=None,  # width/height are in Photo model, not ImageFile
            height=None,
            gps_latitude=None,  # GPS is in Photo model, not ImageFile
            gps_longitude=None,
            has_gps=False,  # GPS is in Photo model
            # NOTE: title, description, tags, rating, user_rotation, author in Photo model
            # import_source available via import_session relationship if needed
            has_raw_companion=computed_format in ['cr2', 'nef', 'arw', 'dng', 'orf', 'rw2', 'raw'] if computed_format else False
        )
    
    def _cleanup_image_files(self, image_file) -> None:
        """Clean up files associated with image_file"""
        # Note: We no longer have full file path, so disable file cleanup for now
        pass
    
    def _generate_hothash_from_hotpreview(self, hotpreview: bytes) -> str:
        """
        Generate hothash from hotpreview
        Uses SHA256 hash of hotpreview bytes
        """
        hothash = hashlib.sha256(hotpreview).hexdigest()
        return hothash
    
    def _generate_perceptual_hash_from_hotpreview(self, hotpreview: bytes) -> Optional[str]:
        """
        Generate perceptual hash from hotpreview for similarity search
        Uses pHash algorithm (16-bit hash)
        """
        try:
            # Convert bytes to PIL Image
            img = PILImage.open(io.BytesIO(hotpreview))
            
            # Generate perceptual hash
            phash = imagehash.phash(img)
            
            # Return as hex string (16 characters)
            return str(phash)
        except Exception as e:
            # Enhanced debugging for hotpreview issues
            print(f"Warning: Could not generate perceptual hash from hotpreview (ImageFileService): {e}")
            print(f"DEBUG: Hotpreview data type: {type(hotpreview)}, size: {len(hotpreview) if hotpreview else 'None'}")
            
            if hotpreview and len(hotpreview) > 0:
                # Check if it's Base64 encoded data
                if isinstance(hotpreview, str):
                    print("DEBUG: Hotpreview is string (possibly Base64), trying to decode...")
                    try:
                        import base64
                        decoded = base64.b64decode(hotpreview)
                        print(f"DEBUG: Successfully decoded Base64, new size: {len(decoded)}")
                        # Try again with decoded data
                        img = PILImage.open(io.BytesIO(decoded))
                        phash = imagehash.phash(img)
                        return str(phash)
                    except Exception as decode_err:
                        print(f"DEBUG: Base64 decode failed: {decode_err}")
                
                # Convert to bytes if it's memoryview
                if isinstance(hotpreview, memoryview):
                    hotpreview_bytes = hotpreview.tobytes()
                else:
                    hotpreview_bytes = hotpreview
                
                # Check first few bytes to see file format
                header = hotpreview_bytes[:10] if len(hotpreview_bytes) >= 10 else hotpreview_bytes
                print(f"DEBUG: Hotpreview header bytes: {[hex(b) for b in header]}")
                
                # Check for JPEG magic bytes (FF D8)
                if len(hotpreview_bytes) >= 2:
                    if hotpreview_bytes[0] == 0xFF and hotpreview_bytes[1] == 0xD8:
                        print("DEBUG: JPEG magic bytes detected")
                    else:
                        print(f"DEBUG: Not JPEG format - first bytes: {hex(hotpreview_bytes[0])}, {hex(hotpreview_bytes[1])}")
                        
                        # Try to detect if it's text/base64
                        try:
                            text_sample = hotpreview_bytes[:50].decode('utf-8', errors='ignore')
                            print(f"DEBUG: Hotpreview as text sample: '{text_sample}'")
                            if all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in text_sample if c.isprintable()):
                                print("DEBUG: Looks like Base64 text")
                        except:
                            pass
            
            import traceback
            traceback.print_exc()
            return None
    
    def find_similar_images(self, image_id: int, threshold: int = 5, limit: int = 10) -> List[ImageFileResponse]:
        """
        Find images similar to the given image using perceptual hash
        
        Args:
            image_id: ID of the reference image
            threshold: Hamming distance threshold (0-16, lower = more similar)
            limit: Maximum number of results to return
            
        Returns:
            List of similar images sorted by similarity (most similar first)
        """
        # Get the reference image
        reference_image = self.image_file_repo.get_by_id(image_id)
        if not reference_image:
            raise NotFoundError(resource="ImageFile", id=image_id)
        
        if not getattr(reference_image, 'perceptual_hash', None):
            raise ValidationError(f"ImageFile {image_id} has no perceptual hash")
        
        # Get all images with perceptual hash
        all_images = self.image_file_repo.get_image_files(offset=0, limit=10000)
        similar_images = []
        
        try:
            reference_hash = imagehash.hex_to_hash(getattr(reference_image, 'perceptual_hash'))
            
            for image in all_images:
                # Skip the reference image itself and images without perceptual hash
                image_id_val = getattr(image, 'id')
                image_phash = getattr(image, 'perceptual_hash', None)
                
                if image_id_val == image_id or not image_phash:
                    continue
                
                try:
                    image_hash = imagehash.hex_to_hash(image_phash)
                    distance = reference_hash - image_hash  # Hamming distance
                    
                    if distance <= threshold:
                        similar_images.append((image, distance))
                except ValueError:
                    # Skip images with invalid perceptual hash
                    continue
            
            # Sort by similarity (lowest distance first)
            similar_images.sort(key=lambda x: x[1])
            
            # Limit results and convert to response objects
            limited_images = similar_images[:limit]
            return [self._convert_to_response(image) for image, _ in limited_images]
            
        except ValueError as e:
            raise ValidationError(f"Invalid perceptual hash format: {e}")
    
    def _generate_hothash_from_image(self, image_data: ImageFileCreateRequest) -> str:
        """
        Generate hothash from image_file data
        Uses filename and file_size to create a unique hash
        """
        # Create hash from available data
        hash_input = f"{image_data.filename}_{image_data.file_size or 0}"
        hothash = hashlib.sha256(hash_input.encode()).hexdigest()
        return hothash
    
    def _extract_photo_metadata_from_image(
        self, 
        image_data: ImageFileCreateRequest, 
        hothash: str
    ) -> PhotoCreateRequest:
        """
        Extract Photo metadata from ImageFile data
        This creates the Photo record for the first (master) ImageFile
        NOTE: hotpreview is stored in ImageFile, not Photo
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
                from PIL import ImageFile as PILImage
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
            author_id=None
        )
    
    def update_storage_info(self, image_file_id: int, storage_info: 'StorageInfoUpdateRequest') -> 'ImageFileResponse':
        """Update storage information for an image file"""
        # Check if image file exists
        image_file = self.image_file_repo.get_by_id(image_file_id)
        if not image_file:
            raise NotFoundError("ImageFile", image_file_id)
        
        # Update storage info
        update_data = {}
        if storage_info.local_storage_info is not None:
            update_data['local_storage_info'] = storage_info.local_storage_info
        if storage_info.cloud_storage_info is not None:
            update_data['cloud_storage_info'] = storage_info.cloud_storage_info
        
        # Apply updates
        updated_image_file = self.image_file_repo.update(image_file_id, update_data)
        return self._convert_to_response(updated_image_file)
    
    def get_storage_info(self, image_file_id: int) -> dict:
        """Get storage information for an image file"""
        image_file = self.image_file_repo.get_by_id(image_file_id)
        if not image_file:
            raise NotFoundError("ImageFile", image_file_id)
        
        return {
            "local_storage_info": getattr(image_file, 'local_storage_info', None),
            "cloud_storage_info": getattr(image_file, 'cloud_storage_info', None),
            "imported_info": getattr(image_file, 'imported_info', None),
            "imported_time": getattr(image_file, 'imported_time', None)
        }