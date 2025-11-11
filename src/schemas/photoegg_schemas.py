"""
PhotoEgg Schemas - Pydantic models for PhotoEgg API

PhotoEgg is the complete JSON package from imalink-core server containing
all image processing results (previews, metadata, hashes).
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PhotoEggMetadata(BaseModel):
    """
    Metadata section of PhotoEgg from imalink-core
    """
    # Core dimensions
    width: int
    height: int
    
    # DateTime information
    taken_at: Optional[datetime] = None
    
    # Camera information
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    
    # Camera settings
    focal_length: Optional[float] = None
    f_number: Optional[float] = None
    iso: Optional[int] = None
    exposure_time: Optional[str] = None
    
    # GPS information
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None


class PhotoEggCreate(BaseModel):
    """
    PhotoEgg from imalink-core server
    
    This is the complete image processing result that backend receives
    from frontend (which got it from imalink-core server).
    
    NEW (v2.0+): Added validation fields (is_valid_image, image_format, 
    file_size_bytes) with defaults for backwards compatibility.
    """
    # Identity
    hothash: str = Field(..., description="SHA256 hash of hotpreview (unique identifier)")
    
    # Previews (base64-encoded JPEG)
    hotpreview_base64: str = Field(..., description="150x150px thumbnail, base64-encoded")
    coldpreview_base64: Optional[str] = Field(None, description="Variable size preview, base64-encoded (optional)")
    
    # Dimensions
    width: int = Field(..., description="Original image width in pixels")
    height: int = Field(..., description="Original image height in pixels")
    
    # Metadata
    metadata: Optional[PhotoEggMetadata] = None
    
    # Complete EXIF dictionary (optional, for advanced use)
    exif_dict: Optional[Dict[str, Any]] = None
    
    # Validation & Extended Info (v2.0+) - with defaults for backwards compatibility
    is_valid_image: bool = Field(True, description="Image validation status (always True if PhotoEgg created)")
    image_format: str = Field("JPEG", description="Image format: JPEG, PNG, HEIC, etc.")
    file_size_bytes: int = Field(0, description="Original file size in bytes")


class PhotoEggRequest(BaseModel):
    """
    Complete request to create Photo from PhotoEgg
    
    Combines PhotoEgg data with user-specific organization metadata.
    """
    # PhotoEgg from imalink-core
    photo_egg: PhotoEggCreate
    
    # User organization fields
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    rating: int = Field(0, ge=0, le=5, description="Star rating 0-5")
    visibility: str = Field("private", pattern="^(private|space|authenticated|public)$")
    tags: list[str] = Field(default_factory=list, description="Tag names to associate")
    author_id: Optional[int] = Field(None, description="Optional author association")


class PhotoEggResponse(BaseModel):
    """
    Response after creating Photo from PhotoEgg
    """
    id: int
    hothash: str
    title: Optional[str]
    rating: int
    visibility: str
    width: int
    height: int
    taken_at: Optional[datetime]
    created_at: datetime
    is_duplicate: bool = Field(default=False, description="True if hothash already existed")
    
    class Config:
        from_attributes = True
