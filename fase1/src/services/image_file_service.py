"""
ImageFile Service - Business Logic Layer for ImageFile operations
Orchestrates image_file operations and implements business rules
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import hashlib
import imagehash
import io
from PIL import Image as PILImage

from repositories.image_file_repository import ImageFileRepository
from repositories.photo_repository import PhotoRepository
from schemas.image_file_schemas import (
    ImageFileResponse, ImageFileCreateRequest, ImageFileUpdateRequest, 
    ImageFileSearchRequest, StorageInfoUpdateRequest
)
from schemas.image_file_upload_schemas import (
    ImageFileNewPhotoRequest, ImageFileAddToPhotoRequest, ImageFileUploadResponse
)
from schemas.photo_schemas import PhotoCreateRequest
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, DuplicateImageError, ValidationError
from models import Photo, ImageFile





class ImageFileService:
    """Service class for ImageFile business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.image_file_repo = ImageFileRepository(db)
        self.photo_repo = PhotoRepository(db)
    
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
        Create ImageFile with automatic Photo creation/linking
        
        Backend receives hotpreview from frontend and:
        1. Generate hothash from hotpreview (SHA256)
        2. Check if Photo exists by hothash (duplicate detection)
        3. If exists: Add ImageFile to existing Photo
        4. If not: Create new Photo + ImageFile
        
        Note: coldpreview is sent separately via PUT /photos/{hash}/coldpreview
        """
        
        # 1. Validate hotpreview is provided
        if not image_data.hotpreview:
            raise ValidationError("hotpreview is required when creating ImageFile")
        
        # 2. Cast hotpreview to bytes - Pydantic validator can return Union[bytes, str] 
        # but our processing methods expect bytes
        if isinstance(image_data.hotpreview, str):
            hotpreview_bytes = image_data.hotpreview.encode('utf-8')
        else:
            hotpreview_bytes = image_data.hotpreview
        
        # 3. Generate hothash from hotpreview (SHA256)
        hothash = self._generate_hothash_from_hotpreview(hotpreview_bytes)
        
        # 4. Check if Photo exists by hothash (duplicate detection)
        existing_photo = self._simple_photo_exists_check(hothash)
        
        perceptual_hash = self._generate_perceptual_hash_if_missing(
            image_data.perceptual_hash, 
            hotpreview_bytes
        )
        
        # 5. If Photo exists: Add ImageFile to existing Photo
        if existing_photo:
            return self._create_image_file_for_existing_photo(image_data, hothash, perceptual_hash)
        
        # 6. If Photo doesn't exist: Create new Photo + ImageFile (no coldpreview generation)
        return self._create_new_photo_with_previews(image_data, hothash, perceptual_hash, hotpreview_bytes)
    
    def create_image_file_new_photo(self, image_data: ImageFileNewPhotoRequest) -> ImageFileUploadResponse:
        """
        Create ImageFile that will create a new Photo
        
        USE CASE: Uploading a completely new, unique photo
        - Hotpreview is REQUIRED and will generate the Photo's hothash
        - A new Photo will always be created
        - This ImageFile becomes the master file for the new Photo
        
        WORKFLOW:
        1. Validate hotpreview data
        2. Generate photo_hothash from hotpreview (SHA256)
        3. Check if Photo already exists (if yes, raise DuplicateImageError)
        4. Create new Photo with generated hothash
        5. Create ImageFile linked to new Photo
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
        
        # 4. Check if Photo already exists - if yes, this is an error for this endpoint
        existing_photo = self._simple_photo_exists_check(hothash)
        if existing_photo:
            raise DuplicateImageError(f"Photo with this image already exists (hothash: {hothash[:8]}...)")
        
        # 5. Generate perceptual hash
        perceptual_hash = self._generate_perceptual_hash_if_missing(
            image_data.perceptual_hash, 
            hotpreview_bytes
        )
        
        # 6. Create new Photo + ImageFile
        image_file = self._create_new_photo_with_previews_v2(image_data, hothash, perceptual_hash, hotpreview_bytes)
        
        # 7. Return success response
        return ImageFileUploadResponse(
            image_file_id=getattr(image_file, 'id'),
            filename=getattr(image_file, 'filename'),
            file_size=getattr(image_file, 'file_size', None),
            photo_hothash=hothash,
            photo_created=True,
            success=True,
            message="New photo created successfully"
        )
    
    def add_image_file_to_photo(self, image_data: ImageFileAddToPhotoRequest) -> ImageFileUploadResponse:
        """
        Add new ImageFile to an existing Photo
        
        USE CASE: Adding companion files to existing photos
        - RAW file for existing JPEG photo
        - Different format/resolution of same photo
        - Additional file versions
        
        REQUIREMENTS:
        - photo_hothash must reference an existing Photo
        - No hotpreview or perceptual_hash needed (Photo already exists)
        
        WORKFLOW:
        1. Validate that Photo with photo_hothash exists
        2. Create ImageFile linked to existing Photo
        3. Return success response
        """
        # 1. Validate that Photo exists
        existing_photo = self.photo_repo.get_by_hash(image_data.photo_hothash)
        if not existing_photo:
            raise NotFoundError("Photo", image_data.photo_hothash)
        
        # 2. Create ImageFile for existing Photo (no hotpreview/perceptual_hash processing)
        image_file = self._create_image_file_for_existing_photo_v2(image_data, image_data.photo_hothash)
        
        # 3. Return success response
        return ImageFileUploadResponse(
            image_file_id=getattr(image_file, 'id'),
            filename=getattr(image_file, 'filename'),
            file_size=getattr(image_file, 'file_size', None),
            photo_hothash=image_data.photo_hothash,
            photo_created=False,
            success=True,
            message="Image file added to existing photo successfully"
        )
    
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
        NOTE: Frontend now provides taken_at, gps_latitude, gps_longitude directly
        """
        # Get metadata directly from frontend (no EXIF extraction needed)
        taken_at = image_data.taken_at
        gps_latitude = image_data.gps_latitude
        gps_longitude = image_data.gps_longitude
        
        # Extract image dimensions from EXIF for now (could also be moved to frontend later)
        width = None
        height = None
        
        if image_data.exif_dict:
            try:
                # Extract image dimensions from image_info
                if "image_info" in image_data.exif_dict and image_data.exif_dict["image_info"]:
                    image_info = image_data.exif_dict["image_info"]
                    if isinstance(image_info, dict):
                        if "width" in image_info and image_info["width"] is not None:
                            width = int(image_info["width"])
                        if "height" in image_info and image_info["height"] is not None:
                            height = int(image_info["height"])
            except Exception:
                # Silently fail if EXIF processing fails - fields will remain None
                pass
        
        # Create PhotoCreateRequest with frontend-provided data
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
    
    # ===== VANNTETT ARKITEKTUR HJELPEMETODER =====
    
    def _simple_photo_exists_check(self, hothash: str) -> Optional[object]:
        """
        VANNTETT SJEKK: Simple check if Photo exists by hothash
        Returns Photo object if exists, None if not
        """
        return self.photo_repo.get_by_hash(hothash)
    
    def _generate_perceptual_hash_if_missing(self, existing_hash: Optional[str], hotpreview: bytes) -> Optional[str]:
        """Generate perceptual hash if not provided"""
        if existing_hash:
            return existing_hash
        return self._generate_perceptual_hash_from_hotpreview(hotpreview)
    
    def _create_image_file_for_existing_photo(self, image_data: ImageFileCreateRequest, 
                                             hothash: str, perceptual_hash: Optional[str]) -> ImageFileResponse:
        """Create ImageFile for existing Photo (duplicate case)"""
        
        # Create ImageFile linked to existing Photo
        image_data_dict = image_data.model_dump()
        image_data_dict['photo_hothash'] = hothash
        image_data_dict['perceptual_hash'] = perceptual_hash
        
        # Set imported_time automatically if not provided
        if 'imported_time' not in image_data_dict or not image_data_dict['imported_time']:
            from datetime import datetime
            image_data_dict['imported_time'] = datetime.utcnow()
        
        image_file = self.image_file_repo.create(image_data_dict)
        
        return self._convert_to_response(image_file)
    
    def _create_new_photo_with_previews(self, image_data: ImageFileCreateRequest, 
                                       hothash: str, perceptual_hash: Optional[str], 
                                       hotpreview_bytes: bytes) -> ImageFileResponse:
        """
        Create new Photo + ImageFile (hotpreview only)
        
        Flow:
        1. Create Photo with hothash (hotpreview stored in ImageFile)
        2. Create ImageFile linked to new Photo
        
        Note: coldpreview sent separately via PUT /photos/{hash}/coldpreview
        """
        
        # 1. Create Photo with basic metadata
        photo_data = self._extract_photo_metadata_from_image(image_data, hothash)
        photo = self.photo_repo.create(photo_data)
        
        # 2. Create ImageFile linked to new Photo
        # Note: coldpreview will be sent separately via PUT /photos/{hash}/coldpreview
        image_data_dict = image_data.model_dump()
        image_data_dict['photo_hothash'] = hothash
        image_data_dict['perceptual_hash'] = perceptual_hash
        
        # Set imported_time automatically if not provided
        if 'imported_time' not in image_data_dict or not image_data_dict['imported_time']:
            from datetime import datetime
            image_data_dict['imported_time'] = datetime.utcnow()
        
        image_file = self.image_file_repo.create(image_data_dict)
        
        return self._convert_to_response(image_file)
    
    def _create_new_photo_with_previews_v2(self, image_data: ImageFileNewPhotoRequest, 
                                          hothash: str, perceptual_hash: Optional[str], 
                                          hotpreview_bytes: bytes) -> ImageFile:
        """
        Create new Photo + ImageFile for new upload endpoint
        
        Returns the created ImageFile (not the response model)
        """
        
        # 1. Create Photo with basic metadata (TODO: add user_id parameter)
        photo_data_dict = self._extract_photo_metadata_from_new_photo_request(image_data, hothash)
        photo_data = PhotoCreateRequest(**photo_data_dict)
        photo = self.photo_repo.create(photo_data, user_id=1)  # TODO: get actual user_id
        
        # 2. Create ImageFile linked to new Photo
        image_data_dict = image_data.model_dump()
        image_data_dict['photo_hothash'] = hothash
        image_data_dict['perceptual_hash'] = perceptual_hash
        
        # Set imported_time automatically if not provided
        if 'imported_time' not in image_data_dict or not image_data_dict['imported_time']:
            from datetime import datetime
            image_data_dict['imported_time'] = datetime.utcnow()
        
        image_file = self.image_file_repo.create(image_data_dict)
        
        return image_file
    
    def _create_image_file_for_existing_photo_v2(self, image_data: ImageFileAddToPhotoRequest, 
                                                hothash: str, perceptual_hash: Optional[str] = None) -> ImageFile:
        """
        Create ImageFile for existing Photo for add-to-photo endpoint
        
        Returns the created ImageFile (not the response model)
        """
        
        # Create ImageFile linked to existing Photo
        image_data_dict = image_data.model_dump()
        image_data_dict['photo_hothash'] = hothash
        image_data_dict['perceptual_hash'] = perceptual_hash
        
        # Set imported_time automatically if not provided
        if 'imported_time' not in image_data_dict or not image_data_dict['imported_time']:
            from datetime import datetime
            image_data_dict['imported_time'] = datetime.utcnow()
        
        image_file = self.image_file_repo.create(image_data_dict)
        
        return image_file
    
    def _extract_photo_metadata_from_new_photo_request(self, image_data: ImageFileNewPhotoRequest, hothash: str) -> Dict[str, Any]:
        """
        Extract Photo metadata from ImageFileNewPhotoRequest
        """
        return {
            'hothash': hothash,
            'taken_at': image_data.taken_at,
            'gps_latitude': image_data.gps_latitude,
            'gps_longitude': image_data.gps_longitude,
            'title': None,  # Will be set later via Photo API
            'description': None,  # Will be set later via Photo API
        }

    
