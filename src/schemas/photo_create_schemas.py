"""
PhotoCreateSchema - Re-export from imalink-schemas package

All schemas now imported from imalink-schemas to ensure consistency across:
- imalink (backend)
- imalink-core (image processing)
- imalink-desktop (Rust client)
- imalink-web (TypeScript client)

PhotoCreateSchema structure (matches MY_OVERVIEW.md):
- hothash, hotpreview (base64), width, height
- exif_dict: ALL EXIF metadata (camera_make, iso, etc.)
- taken_at, gps_latitude, gps_longitude (indexed copies for queries)
- user_id, rating, category, visibility, etc.
- image_file_list: list of ImageFileCreateSchema (JPEG + RAW companions)
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Import schemas from shared package
from imalink_schemas import (
    PhotoCreateSchema,
    ImageFileCreateSchema,
    PhotoUpdateSchema,
    PhotoResponse,
)


class PhotoCreateRequest(BaseModel):
    """
    SIMPLIFIED: PhotoCreateSchema now contains all fields.
    
    PhotoCreateSchema from imalink_schemas already includes:
    - user_id (set by frontend after auth)
    - rating, category, visibility
    - import_session_id, author_id, stack_id
    - image_file_list (replaces primary_filename)
    
    This wrapper only adds tags (handled via separate PhotoTag relationship).
    
    TODO: Consider removing this wrapper and using PhotoCreateSchema directly.
    """
    photo_create_schema: PhotoCreateSchema
    tags: list[str] = Field(default_factory=list, description="Tag names to associate")


class PhotoCreateResponse(PhotoResponse):
    """
    Response after creating Photo.
    
    Extends PhotoResponse (from imalink_schemas) with creation-specific fields.
    """
    created_at: datetime = Field(..., description="When photo was created in database")
    is_duplicate: bool = Field(default=False, description="True if hothash already existed")
    
    class Config:
        from_attributes = True


# Re-export for convenience
__all__ = [
    "PhotoCreateSchema",
    "ImageFileCreateSchema",
    "PhotoUpdateSchema",
    "PhotoResponse",
    "PhotoCreateRequest",
    "PhotoCreateResponse",
]
