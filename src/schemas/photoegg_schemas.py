"""
PhotoEgg Schemas - Pydantic models for PhotoEgg API

PhotoEgg is the complete JSON package from imalink-core server containing
all image processing results (previews, metadata, hashes).

STRUCTURE: PhotoEgg has FLAT structure matching imalink-core output.
All EXIF fields are at root level for direct access.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PhotoEggCreate(BaseModel):
    """
    PhotoEgg from imalink-core server (FLAT structure)
    
    This matches the actual JSON from imalink-core service.
    All EXIF metadata is at root level (not nested).
    
    Philosophy:
    - exif_dict: Complete EXIF "DNA" (readonly, never modified)
    - Root fields: Indexed copies for queries (taken_at, GPS, camera)
    """
    # === IDENTITY ===
    hothash: str = Field(..., description="SHA256 hash of hotpreview (unique identifier)")
    
    # === PREVIEWS (base64-encoded JPEG) ===
    hotpreview_base64: str = Field(..., description="150x150px thumbnail, base64-encoded")
    hotpreview_width: int = Field(150, description="Hotpreview width in pixels")
    hotpreview_height: int = Field(150, description="Hotpreview height in pixels")
    
    coldpreview_base64: Optional[str] = Field(None, description="Variable size preview, base64-encoded (optional)")
    coldpreview_width: Optional[int] = Field(None, description="Coldpreview width in pixels")
    coldpreview_height: Optional[int] = Field(None, description="Coldpreview height in pixels")
    
    # === FILE INFO ===
    primary_filename: str = Field(..., description="Original filename")
    width: int = Field(..., description="Original image width in pixels")
    height: int = Field(..., description="Original image height in pixels")
    
    # === TIME & LOCATION (indexed copies from EXIF) ===
    taken_at: Optional[datetime] = Field(None, description="DateTime from EXIF")
    gps_latitude: Optional[float] = Field(None, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, description="GPS longitude")
    has_gps: bool = Field(False, description="Whether GPS data exists")
    
    # === CAMERA (indexed copies from EXIF) ===
    camera_make: Optional[str] = Field(None, description="Camera manufacturer")
    camera_model: Optional[str] = Field(None, description="Camera model")
    
    # === CAMERA SETTINGS ===
    iso: Optional[int] = Field(None, description="ISO speed")
    aperture: Optional[float] = Field(None, description="Aperture (f-number)")
    shutter_speed: Optional[str] = Field(None, description="Shutter speed")
    focal_length: Optional[float] = Field(None, description="Focal length in mm")
    lens_model: Optional[str] = Field(None, description="Lens model")
    lens_make: Optional[str] = Field(None, description="Lens manufacturer")
    
    # === COMPLETE EXIF (readonly "DNA") ===
    exif_dict: Optional[Dict[str, Any]] = Field(None, description="Complete EXIF metadata (readonly)")
    
    # === VALIDATION & EXTENDED INFO ===
    is_valid_image: bool = Field(True, description="Image validation status")
    image_format: str = Field("JPEG", description="Image format: JPEG, PNG, HEIC, etc.")
    file_size_bytes: int = Field(0, description="Original file size in bytes")


class PhotoEggRequest(BaseModel):
    """
    Complete request to create Photo from PhotoEgg
    
    Combines PhotoEgg data with user-specific organization metadata.
    
    If import_session_id is not provided, the user's default "Quick Add" session is used.
    This allows immediate photo uploads without requiring import session setup.
    """
    # PhotoEgg from imalink-core
    photo_egg: PhotoEggCreate
    
    # Import context (OPTIONAL) - defaults to user's "Quick Add" session if not provided
    import_session_id: Optional[int] = Field(
        None, 
        description="Import session ID (groups photos by import batch). If not provided, uses default 'Quick Add' session."
    )
    
    # User organization fields
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
    rating: int
    visibility: str
    width: int
    height: int
    taken_at: Optional[datetime]
    created_at: datetime
    is_duplicate: bool = Field(default=False, description="True if hothash already existed")
    
    class Config:
        from_attributes = True
