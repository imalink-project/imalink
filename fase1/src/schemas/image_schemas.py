"""
Image-related Pydantic schemas for API requests and responses
Provides type-safe data models for image operations
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
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
    hash: str = Field(..., alias="image_hash", description="Perceptual hash of the image")
    filename: str = Field(..., alias="original_filename", description="Original filename")
    file_path: str = Field(..., description="Full path to image file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_format: Optional[str] = Field(None, description="File format (jpg, png, raw, etc.)")
    
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
    
    # User metadata
    title: Optional[str] = Field(None, description="User-assigned title")
    description: Optional[str] = Field(None, description="User-assigned description")
    tags: List[str] = Field(default_factory=list, description="User-assigned tags")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating (1-5 stars)")
    
    # User modifications
    user_rotation: int = Field(0, ge=0, le=3, description="User rotation (0=0°, 1=90°, 2=180°, 3=270°)")
    
    # Relationships
    author: Optional[AuthorSummary] = Field(None, description="Image author/photographer")
    author_id: Optional[int] = Field(None, description="Author ID")
    
    # Import info
    import_source: Optional[str] = Field(None, description="Import source description")
    
    # Computed fields (set by service layer)
    has_raw_companion: bool = Field(False, description="Whether image has RAW companion file")
    has_thumbnail: bool = Field(False, description="Whether thumbnail is available")
    
    class Config:
        from_attributes = True
        populate_by_name = True
    
    @validator('has_gps', pre=False, always=True)
    def compute_has_gps(cls, v, values):
        """Compute has_gps from latitude/longitude"""
        lat = values.get('gps_latitude')
        lon = values.get('gps_longitude')
        return lat is not None and lon is not None
    
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        """Parse tags from JSON string if needed"""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                # Fallback: split by comma
                return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v or []


class ImageListResponse(BaseModel):
    """Response for image listing endpoints"""
    images: List[ImageResponse] = Field(..., description="Array of images")
    total: int = Field(..., description="Total number of images matching criteria")
    
    class Config:
        from_attributes = True


class ImageCreateRequest(BaseModel):
    """Request model for creating new images"""
    original_filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_path: str = Field(..., description="Full path to image file")
    image_hash: str = Field(..., min_length=1, max_length=64, description="Perceptual hash")
    
    # Optional file metadata
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_format: Optional[str] = Field(None, max_length=10, description="File format")
    
    # Optional timestamps
    taken_at: Optional[datetime] = Field(None, description="When photo was taken")
    
    # Optional dimensions
    width: Optional[int] = Field(None, ge=1, description="Image width in pixels")
    height: Optional[int] = Field(None, ge=1, description="Image height in pixels")
    
    # Optional GPS
    gps_latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    
    # Optional metadata
    title: Optional[str] = Field(None, max_length=255, description="Image title")
    description: Optional[str] = Field(None, max_length=2000, description="Image description")
    tags: List[str] = Field(default_factory=list, description="Image tags")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Image rating")
    
    # Relationships
    author_id: Optional[int] = Field(None, description="Author/photographer ID")
    import_source: Optional[str] = Field(None, max_length=255, description="Import source")


class ImageUpdateRequest(BaseModel):
    """Request model for updating existing images"""
    title: Optional[str] = Field(None, max_length=255, description="Image title")
    description: Optional[str] = Field(None, max_length=2000, description="Image description")
    tags: Optional[List[str]] = Field(None, description="Image tags")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Image rating")
    user_rotation: Optional[int] = Field(None, ge=0, le=3, description="User rotation")
    author_id: Optional[int] = Field(None, description="Author/photographer ID")


class ImageSearchRequest(BaseModel):
    """Request model for image search"""
    q: Optional[str] = Field(None, description="Search query (filename, title, description)")
    author_id: Optional[int] = Field(None, description="Filter by author ID")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    rating_min: Optional[int] = Field(None, ge=1, le=5, description="Minimum rating")
    rating_max: Optional[int] = Field(None, ge=1, le=5, description="Maximum rating")
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


class ImageThumbnailResponse(BaseModel):
    """Response model for thumbnail requests"""
    image_id: int = Field(..., description="Image ID")
    thumbnail_data: bytes = Field(..., description="Thumbnail binary data")
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