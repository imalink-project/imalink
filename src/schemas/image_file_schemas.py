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
    
    # Import tracking
    input_channel_id: Optional[int] = Field(None, description="Input channel ID")
    imported_time: Optional[datetime] = Field(None, description="When this file was imported")
    imported_info: Optional[Dict[str, Any]] = Field(None, description="Import context and original location")
    
    # Storage location tracking
    local_storage_info: Optional[Dict[str, Any]] = Field(None, description="Local storage metadata")
    cloud_storage_info: Optional[Dict[str, Any]] = Field(None, description="Cloud storage metadata")
    
    # Computed fields (provided by service layer)
    file_format: Optional[str] = Field(None, description="File format computed from filename")
    file_path: Optional[str] = Field(None, description="Full path computed by storage service")
    original_filename: Optional[str] = Field(None, description="Original filename from import session")
    
    # Timestamps
    created_at: datetime = Field(..., description="When image was imported")
    
    # NOTE: Visual data (hotpreview, exif_dict) moved to Photo model
    # NOTE: Metadata (taken_at, GPS, width, height) moved to Photo model
    # Access these via photo relationship: image_file.photo.hotpreview, etc.
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ImageFileCreateRequest(BaseModel):
    """
    Request model for creating new ImageFile - DEPRECATED
    
    Use image_file_upload_schemas instead:
    - ImageFileNewPhotoRequest: For creating new Photo with ImageFile
    - ImageFileAddToPhotoRequest: For adding ImageFile to existing Photo
    """
    filename: str = Field(..., min_length=1, max_length=255, description="Filename with extension")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    
    # Import context
    input_channel_id: Optional[int] = Field(None, description="Input channel ID")
    imported_info: Optional[Dict[str, Any]] = Field(None, description="Import context and original location")
    local_storage_info: Optional[Dict[str, Any]] = Field(None, description="Local storage info")
    cloud_storage_info: Optional[Dict[str, Any]] = Field(None, description="Cloud storage info")


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