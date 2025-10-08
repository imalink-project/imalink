"""
Photo batch request schemas for bulk photo creation operations
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from ..image_schemas import ImageCreateRequest


class PhotoGroupRequest(BaseModel):
    """Single photo group in batch request - represents one photo with associated image files"""
    hothash: str = Field(..., min_length=1, max_length=64, description="Content-based hash identifier")
    
    # Visual presentation data
    hotpreview: Optional[str] = Field(None, description="Base64 encoded preview image")
    width: Optional[int] = Field(None, ge=1, description="Original image width in pixels")
    height: Optional[int] = Field(None, ge=1, description="Original image height in pixels")
    
    # Content metadata
    taken_at: Optional[datetime] = Field(None, description="When photo was taken (from EXIF)")
    gps_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="GPS longitude")
    
    # User metadata
    title: Optional[str] = Field(None, max_length=255, description="User-assigned title")
    description: Optional[str] = Field(None, max_length=1000, description="User description/notes") 
    tags: Optional[List[str]] = Field(None, description="List of tags")
    rating: int = Field(0, ge=0, le=5, description="User rating (0-5 stars)")
    user_rotation: int = Field(0, ge=0, le=3, description="User rotation (0=0°, 1=90°, 2=180°, 3=270°)")
    
    # Import tracking
    import_session_id: Optional[int] = Field(None, description="Import session ID")
    
    # Associated image files (RAW, JPEG, etc.)
    images: List[ImageCreateRequest] = Field(..., min_length=1, description="Associated image files")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            # Remove empty strings and duplicates
            v = list(set(tag.strip() for tag in v if tag.strip()))
            # Limit number of tags
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            # Validate tag length
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Tags cannot exceed 50 characters")
        return v
    
    class Config:
        from_attributes = True


class PhotoGroupBatchRequest(BaseModel):
    """Batch request for creating multiple photos with their associated images"""
    photo_groups: List[PhotoGroupRequest] = Field(..., min_length=1, max_length=1000, description="Photo groups to create")
    author_id: Optional[int] = Field(None, description="Default author ID for all photos (can be overridden per photo)")
    
    @field_validator('photo_groups')
    @classmethod
    def validate_unique_hashes(cls, v):
        """Ensure all hothashes are unique within the batch"""
        hashes = [group.hothash for group in v]
        if len(hashes) != len(set(hashes)):
            raise ValueError("All hothashes must be unique within the batch")
        return v
    
    class Config:
        from_attributes = True