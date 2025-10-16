"""
Image-related Pydantic schemas for API requests and responses
Provides type-safe data models for image operations
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json


class AuthorSummary(BaseModel):
    """Lightweight author info for image responses"""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    """Complete image response model"""
    id: int
    photo_hothash: Optional[str] = Field(None, description="Photo hothash - links to Photo")
    filename: str = Field(..., description="Filename with extension (e.g. IMG_1234.jpg)")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    # NEW: hotpreview is now stored in Image
    has_hotpreview: bool = Field(False, description="Whether hotpreview is available")
    
    # Computed fields (provided by service layer)
    file_format: Optional[str] = Field(None, description="File format computed from filename")
    file_path: Optional[str] = Field(None, description="Full path computed by storage service")
    original_filename: Optional[str] = Field(None, description="Original filename from import session")
    
    # Timestamps
    created_at: datetime = Field(..., description="When image was imported")
    taken_at: Optional[datetime] = Field(None, description="When photo was taken (from EXIF)")
    
    # Dimensions
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    
    # Location
    gps_latitude: Optional[float] = Field(None, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, description="GPS longitude")
    has_gps: bool = Field(False, description="Whether image has GPS coordinates")
    
    # NOTE: User metadata moved to separate ImageMetadata table
    # title, description, tags, rating will be handled by ImageMetadataService
    # These fields removed from Image model to support multiple files per motif (JPEG/RAW)
    
    # User modifications
    user_rotation: int = Field(0, ge=0, le=3, description="User rotation (0=0°, 1=90°, 2=180°, 3=270°)")
    
    # Relationships
    author: Optional[AuthorSummary] = Field(None, description="Image author/photographer")
    author_id: Optional[int] = Field(None, description="Author ID")
    
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


class ImageListResponse(BaseModel):
    """Response for image listing endpoints"""
    images: List[ImageResponse] = Field(..., description="Array of images")
    total: int = Field(..., description="Total number of images matching criteria")
    
    class Config:
        from_attributes = True


class ImageCreateRequest(BaseModel):
    """Request model for creating new images - file-specific data only"""
    filename: str = Field(..., min_length=1, max_length=255, description="Filename with extension")
    
    # NEW ARCHITECTURE: hotpreview stored in Image, photo_hothash auto-generated
    # - hotpreview: Thumbnail/preview binary data (required to generate photo_hothash)
    # - photo_hothash: Auto-calculated from hotpreview via SHA256 hash
    hotpreview: Optional[bytes] = Field(None, description="Thumbnail/preview image binary data (required)")
    
    # Optional file metadata
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    
    # Optional binary EXIF data
    exif_data: Optional[bytes] = Field(None, description="Raw EXIF data as binary blob")
    
    # Optional import tracking
    import_session_id: Optional[int] = Field(None, description="Import session ID")
    
    # NOTE: Visual metadata (taken_at, width, height, GPS, author_id) belongs to Photo model


class ImageUpdateRequest(BaseModel):
    """Request model for updating existing images"""
    # NOTE: title, description, tags, rating moved to ImageMetadata table
    user_rotation: Optional[int] = Field(None, ge=0, le=3, description="User rotation")
    author_id: Optional[int] = Field(None, description="Author/photographer ID")


class ImageSearchRequest(BaseModel):
    """Request model for image search"""
    q: Optional[str] = Field(None, description="Search query (filename)")
    author_id: Optional[int] = Field(None, description="Filter by author ID")
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


class ImageRotateRequest(BaseModel):
    """Request model for rotating images"""
    clockwise: bool = Field(True, description="Rotate clockwise (90°) or counter-clockwise (-90°)")


class ImageHotpreviewResponse(BaseModel):
    """Response model for hot preview requests"""
    image_id: int = Field(..., description="Image ID")
    hotpreview_data: bytes = Field(..., description="Hot preview binary data")
    content_type: str = Field("image/jpeg", description="MIME type")
    
    class Config:
        arbitrary_types_allowed = True


class ImagePoolResponse(BaseModel):
    """Response model for image pool requests"""
    image_id: int = Field(..., description="Image ID")
    pool_size: str = Field(..., description="Pool size (small/medium/large)")
    file_path: str = Field(..., description="Path to pooled image file")
    width: int = Field(..., description="Pool image width")
    height: int = Field(..., description="Pool image height")
    
    class Config:
        from_attributes = True