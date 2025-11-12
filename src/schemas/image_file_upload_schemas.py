"""
New ImageFile upload schemas for clear separation of concerns

CLEAR SEPARATION:
1. ImageFileNewPhotoRequest - For creating completely new photos (requires hotpreview)
2. ImageFileAddToPhotoRequest - For adding companion files to existing photos (NO hotpreview)

The key distinction:
- new-photo: Creates the visual representation of a photo (needs hotpreview for hothash generation)
- add-to-photo: Adds file variants to existing visual representation (no visual processing needed)
"""
from typing import Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import base64


class ImageFileNewPhotoRequest(BaseModel):
    """
    Request model for creating a new ImageFile that will create a new Photo
    
    This is used when uploading an image that represents a new, unique photo.
    The hotpreview is required and will be used to generate the Photo's hothash.
    """
    # Required file data
    filename: str = Field(..., min_length=1, max_length=255, description="Filename with extension")
    hotpreview: Union[bytes, str] = Field(..., description="Hotpreview image binary data or Base64 string (required for new Photo)")
    
    # Optional file metadata
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    
    # Parsed EXIF metadata (frontend responsibility)
    exif_dict: Optional[Dict[str, Any]] = Field(None, description="Parsed EXIF metadata as JSON structure (extracted by frontend)")
    
    # Photo metadata for new Photo creation (extracted from EXIF by frontend)
    taken_at: Optional[datetime] = Field(None, description="When photo was taken (from EXIF)")
    gps_latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude (from EXIF)")
    gps_longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude (from EXIF)")
    
    # Visibility control
    visibility: Optional[str] = Field(default="private", description="Visibility level: private, space, authenticated, or public")
    
    # Import context (REQUIRED) - every photo must belong to an import session
    # ImportSession groups photos by when imported and stores user's notes about source/storage
    import_session_id: int = Field(..., description="Import session ID (required)")
    imported_info: Optional[Dict[str, Any]] = Field(None, description="Import context and original location")
    local_storage_info: Optional[Dict[str, Any]] = Field(None, description="Local storage info")
    cloud_storage_info: Optional[Dict[str, Any]] = Field(None, description="Cloud storage info")
    
    @field_validator('hotpreview')
    @classmethod
    def validate_hotpreview(cls, v: Union[bytes, str]) -> bytes:
        """Convert hotpreview from Base64 string to bytes if needed"""
        if isinstance(v, bytes):
            return v
        
        if isinstance(v, str):
            try:
                # Remove data URL prefix if present
                if v.startswith('data:'):
                    _, data = v.split(',', 1)
                    v = data
                
                decoded = base64.b64decode(v)
                
                if len(decoded) < 10:
                    raise ValueError("Hotpreview too small after decoding")
                
                return decoded
                    
            except Exception as e:
                raise ValueError(f"Invalid hotpreview Base64 data: {str(e)}")
        
        raise ValueError("Hotpreview must be bytes or Base64 string")


class ImageFileAddToPhotoRequest(BaseModel):
    """
    Request model for adding an ImageFile to an existing Photo
    
    This is used when uploading a companion file (e.g., RAW file for existing JPEG)
    or additional format of the same photo. The photo_hothash must be provided
    to specify which existing Photo to add this ImageFile to.
    
    NOTE: hotpreview and exif_dict are NOT included since the Photo 
    already exists with its visual representation and metadata. This is purely for 
    adding file variants.
    """
    # Required file data
    filename: str = Field(..., min_length=1, max_length=255, description="Filename with extension")
    photo_hothash: str = Field(..., min_length=64, max_length=64, description="Hash of existing Photo to add this ImageFile to")
    
    # Optional file metadata
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    
    # Import context
    import_session_id: Optional[int] = Field(None, description="Import session ID")
    imported_info: Optional[Dict[str, Any]] = Field(None, description="Import context and original location")
    local_storage_info: Optional[Dict[str, Any]] = Field(None, description="Local storage info")
    cloud_storage_info: Optional[Dict[str, Any]] = Field(None, description="Cloud storage info")


class ImageFileUploadResponse(BaseModel):
    """
    Response model for both new-photo and add-to-photo uploads
    Contains the created ImageFile and related Photo information
    """
    # ImageFile info
    image_file_id: int = Field(..., description="ID of created ImageFile")
    filename: str = Field(..., description="Filename of uploaded file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    # Photo info
    photo_hothash: str = Field(..., description="Hash of associated Photo")
    photo_created: bool = Field(..., description="Whether a new Photo was created (true) or existing Photo was used (false)")
    
    # Status info
    success: bool = Field(True, description="Upload success status")
    message: str = Field("Upload successful", description="Status message")
    
    class Config:
        from_attributes = True