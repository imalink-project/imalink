"""
ImageFile-related Pydantic schemas for API requests and responses
Provides type-safe data models for image operations
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json
import base64


class AuthorSummary(BaseModel):
    """Lightweight author info for image responses"""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class ImageFileResponse(BaseModel):
    """Complete image response model"""
    id: int
    photo_hothash: Optional[str] = Field(None, description="Photo hothash - links to Photo")
    filename: str = Field(..., description="Filename with extension (e.g. IMG_1234.jpg)")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    # NEW: hotpreview is now stored in ImageFile
    has_hotpreview: bool = Field(False, description="Whether hotpreview is available")
    perceptual_hash: Optional[str] = Field(None, description="Perceptual hash for similarity search")
    
    # Import tracking (NEW EXPANDED FIELDS)
    import_session_id: Optional[int] = Field(None, description="Import session ID")
    imported_time: Optional[datetime] = Field(None, description="When this file was imported")
    imported_info: Optional[Dict[str, Any]] = Field(None, description="Import context and original location")
    
    # Storage location tracking (NEW)
    local_storage_info: Optional[Dict[str, Any]] = Field(None, description="Local storage metadata")
    cloud_storage_info: Optional[Dict[str, Any]] = Field(None, description="Cloud storage metadata")
    
    # Computed fields (provided by service layer)
    file_format: Optional[str] = Field(None, description="File format computed from filename")
    file_path: Optional[str] = Field(None, description="Full path computed by storage service")
    original_filename: Optional[str] = Field(None, description="Original filename from import session")
    
    # Timestamps
    created_at: datetime = Field(..., description="When image was imported")
    taken_at: Optional[datetime] = Field(None, description="When photo was taken (from EXIF)")
    
    # Dimensions
    width: Optional[int] = Field(None, description="ImageFile width in pixels")
    height: Optional[int] = Field(None, description="ImageFile height in pixels")
    
    # Location
    gps_latitude: Optional[float] = Field(None, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, description="GPS longitude")
    has_gps: bool = Field(False, description="Whether image has GPS coordinates")
    
    # NOTE: User metadata moved to separate ImageMetadata table
    # title, description, tags, rating will be handled by ImageMetadataService
    # These fields removed from ImageFile model to support multiple files per motif (JPEG/RAW)
    
    # NOTE: user_rotation removed - rotation is a Photo-level concern, not ImageFile-level
    # NOTE: author removed - author is a Photo-level concern, not ImageFile-level
    
    # Import info available via import_session_id relationship in service layer
    
    # Computed fields (set by service layer)
    has_raw_companion: bool = Field(False, description="Whether image has RAW companion file")
    has_hotpreview: bool = Field(False, description="Whether hot preview is available")
    
    class Config:
        from_attributes = True
        populate_by_name = True
    
    @field_validator('has_gps')
    @classmethod
    def compute_has_gps(cls, v, info):
        """Compute has_gps from latitude/longitude"""
        if info.data:
            lat = info.data.get('gps_latitude')
            lon = info.data.get('gps_longitude')
            return lat is not None and lon is not None
        return v
    
    # NOTE: tags validator removed since tags moved to ImageMetadata table


class ImageFileCreateRequest(BaseModel):
    """Request model for creating new images - file-specific data only"""
    filename: str = Field(..., min_length=1, max_length=255, description="Filename with extension")
    
    # NEW ARCHITECTURE: hotpreview stored in ImageFile, photo_hothash auto-generated
    # - hotpreview: Hotpreview binary data (required to generate photo_hothash)
    # - photo_hothash: Auto-calculated from hotpreview via SHA256 hash
    hotpreview: Optional[Union[bytes, str]] = Field(None, description="Hotpreview image binary data or Base64 string (required)")
    perceptual_hash: Optional[str] = Field(None, description="Perceptual hash for similarity search (auto-generated if not provided)")
    
    # Optional file metadata
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    
    # Parsed EXIF metadata (frontend responsibility)
    exif_dict: Optional[Dict[str, Any]] = Field(None, description="Parsed EXIF metadata as JSON structure (extracted by frontend)")
    
    # Import context (NEW EXPANDED FIELDS)
    import_session_id: Optional[int] = Field(None, description="Import session ID")
    imported_info: Optional[Dict[str, Any]] = Field(None, description="Import context and original location")
    local_storage_info: Optional[Dict[str, Any]] = Field(None, description="Local storage info")
    cloud_storage_info: Optional[Dict[str, Any]] = Field(None, description="Cloud storage info")
    
    # NOTE: Visual metadata (taken_at, width, height, GPS, author_id) belongs to Photo model
    
    @field_validator('hotpreview')
    @classmethod
    def validate_hotpreview(cls, v: Union[bytes, str, None]) -> Optional[bytes]:
        """
        Convert hotpreview from Base64 string to bytes if needed
        Supports both direct bytes and Base64-encoded strings
        """
        if v is None:
            return None
        
        # If already bytes, return as-is
        if isinstance(v, bytes):
            return v
        
        # If string, try to decode as Base64
        if isinstance(v, str):
            try:
                # Remove data URL prefix if present (data:image/jpeg;base64,...)
                if v.startswith('data:'):
                    # Split on comma and take the data part
                    _, data = v.split(',', 1)
                    v = data
                
                # Decode Base64
                decoded = base64.b64decode(v)
                
                # Basic validation: should have some content
                if len(decoded) < 10:
                    raise ValueError("Hotpreview too small after decoding")
                
                # Basic JPEG validation: check for JPEG magic bytes
                if decoded[0] == 0xFF and decoded[1] == 0xD8:
                    return decoded
                else:
                    # Not JPEG, but might be valid image data - let PIL handle it later
                    return decoded
                    
            except Exception as e:
                raise ValueError(f"Invalid hotpreview Base64 data: {str(e)}")
        
        raise ValueError("Hotpreview must be bytes or Base64 string")


class ImageFileUpdateRequest(BaseModel):
    """Request model for updating existing images"""
    # NOTE: title, description, tags, rating moved to ImageMetadata table
    # NOTE: user_rotation removed - rotation is a Photo-level concern
    author_id: Optional[int] = Field(None, description="Author/photographer ID")


class StorageInfoUpdateRequest(BaseModel):
    """Request model for updating storage information"""
    local_storage_info: Optional[Dict[str, Any]] = Field(None, description="Local storage info")
    cloud_storage_info: Optional[Dict[str, Any]] = Field(None, description="Cloud storage info")


class ImageFileSearchRequest(BaseModel):
    """Request model for image search"""
    q: Optional[str] = Field(None, description="Search query (filename)")
    # NOTE: author_id removed - author is a Photo-level concern, not ImageFile-level
    # NOTE: tags, rating search moved to ImageMetadata table
    taken_after: Optional[datetime] = Field(None, description="Taken after date")
    taken_before: Optional[datetime] = Field(None, description="Taken before date")
    has_gps: Optional[bool] = Field(None, description="Filter by GPS availability")
    file_format: Optional[str] = Field(None, description="Filter by file format")
    
    # Pagination
    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of items to return")
    
    # Sorting
    sort_by: str = Field("taken_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# NOTE: ImageRotateRequest removed - rotation is a Photo-level concern, not ImageFile-level