"""
Photo-related Pydantic schemas for API requests and responses
Provides type-safe data models for photo operations
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AuthorSummary(BaseModel):
    """Lightweight author info for photo responses"""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class ImageFileSummary(BaseModel):
    """Summary of image files associated with a photo"""
    id: int
    filename: str
    file_format: Optional[str] = Field(None, description="File format (jpeg, raw, etc)")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    class Config:
        from_attributes = True


class PhotoResponse(BaseModel):
    """Complete photo response model"""
    hothash: str = Field(..., description="Content-based hash identifier")
    
    # Visual presentation data (from master ImageFile)
    width: Optional[int] = Field(None, description="Original image width in pixels")
    height: Optional[int] = Field(None, description="Original image height in pixels")
    
    # Coldpreview metadata (medium-size preview for detail views) 
    # SIMPLIFIED: Only path stored, dimensions/size computed dynamically when needed
    coldpreview_path: Optional[str] = Field(None, description="Filesystem path to coldpreview file")
    coldpreview_width: Optional[int] = Field(None, description="Coldpreview width (computed from file)")
    coldpreview_height: Optional[int] = Field(None, description="Coldpreview height (computed from file)")  
    coldpreview_size: Optional[int] = Field(None, description="Coldpreview file size (computed from file)")
    
    # Content metadata (from master ImageFile)
    taken_at: Optional[datetime] = Field(None, description="When photo was taken (from EXIF)")
    gps_latitude: Optional[float] = Field(None, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, description="GPS longitude")
    exif_dict: Optional[dict] = Field(None, description="EXIF metadata from master image file")
    perceptual_hash: Optional[str] = Field(None, description="Perceptual hash for similarity search")
    
    # User metadata
    rating: int = Field(0, ge=0, le=5, description="User rating (0-5 stars)")
    
    # Timestamps
    created_at: datetime = Field(..., description="When photo was imported")
    updated_at: datetime = Field(..., description="When photo was last updated")
    
    # Relationships
    author: Optional[AuthorSummary] = Field(None, description="Photo author/photographer")
    author_id: Optional[int] = Field(None, description="Author ID")
    
    # Import information (computed from ImageFiles)
    import_sessions: List[int] = Field(default_factory=list, description="All import sessions for this photo's files")
    first_imported: Optional[datetime] = Field(None, description="Earliest import time")
    last_imported: Optional[datetime] = Field(None, description="Latest import time")
    
    # Computed properties
    has_gps: bool = Field(False, description="Whether photo has GPS coordinates")
    has_raw_companion: bool = Field(False, description="Whether photo has both JPEG and RAW files")
    primary_filename: Optional[str] = Field(None, description="Primary filename for display")
    files: List[ImageFileSummary] = Field(default_factory=list, description="Associated image files")
    
    class Config:
        from_attributes = True
    
    @field_validator('has_gps')
    @classmethod
    def compute_has_gps(cls, v, info):
        """Compute has_gps from latitude/longitude"""
        if info.data:
            lat = info.data.get('gps_latitude')
            lon = info.data.get('gps_longitude')
            return lat is not None and lon is not None
        return v


class PhotoListResponse(BaseModel):
    """Response for photo listing endpoints"""
    photos: List[PhotoResponse] = Field(..., description="Array of photos")
    total: int = Field(..., description="Total number of photos matching criteria")
    
    class Config:
        from_attributes = True


class PhotoCreateRequest(BaseModel):
    """Request model for creating new photos"""
    model_config = ConfigDict(extra='forbid')
    
    hothash: str = Field(..., min_length=1, max_length=64, description="Content-based hash identifier")
    
    # Visual data
    # NOTE: hotpreview removed - stored in Image model instead
    width: Optional[int] = Field(None, ge=1, description="Image width in pixels")
    height: Optional[int] = Field(None, ge=1, description="Image height in pixels")
    
    # Content metadata
    taken_at: Optional[datetime] = Field(None, description="When photo was taken")
    gps_latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    
    # User metadata
    rating: Optional[int] = Field(0, ge=0, le=5, description="User rating")
    
    # Relationships
    author_id: Optional[int] = Field(None, description="Author/photographer ID")
    # import_session_id removed - now tracked at ImageFile level


class PhotoUpdateRequest(BaseModel):
    """Request model for updating existing photos"""
    model_config = ConfigDict(extra='forbid')
    
    # User editable fields only
    rating: Optional[int] = Field(None, ge=0, le=5, description="User rating")
    author_id: Optional[int] = Field(None, description="Author/photographer ID")


class PhotoSearchRequest(BaseModel):
    """Request model for photo search"""
    model_config = ConfigDict(extra='forbid')
    
    author_id: Optional[int] = Field(None, description="Filter by author ID")
    rating_min: Optional[int] = Field(None, ge=0, le=5, description="Minimum rating")
    rating_max: Optional[int] = Field(None, ge=0, le=5, description="Maximum rating")
    taken_after: Optional[datetime] = Field(None, description="Taken after date")
    taken_before: Optional[datetime] = Field(None, description="Taken before date")
    has_gps: Optional[bool] = Field(None, description="Filter by GPS availability")
    has_raw: Optional[bool] = Field(None, description="Filter by RAW file availability")
    
    # Pagination
    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of items to return")
    
    # Sorting
    sort_by: str = Field("taken_at", description="Sort field (taken_at, created_at, rating)")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")