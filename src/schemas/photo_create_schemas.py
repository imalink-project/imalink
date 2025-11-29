"""
Backend-specific schemas for Photo API.

PhotoCreateSchema and ImageFileCreateSchema are now imported from imalink-schemas package.
This file contains backend-specific wrappers and response schemas.
"""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Import shared schemas from imalink-schemas package
from imalink_schemas import PhotoCreateSchema, ImageFileCreateSchema


class PhotoUpdateSchema(BaseModel):
    """Schema for updating a Photo"""
    rating: Optional[int] = Field(None, ge=0, le=5)
    category: Optional[str] = None
    visibility: Optional[str] = None
    author_id: Optional[int] = None
    stack_id: Optional[int] = None
    timeloc_correction: Optional[dict[str, Any]] = None
    view_correction: Optional[dict[str, Any]] = None


class PhotoResponse(BaseModel):
    """Base response schema for Photo"""
    id: int
    hothash: str
    width: int
    height: int
    rating: int
    visibility: str
    taken_at: Optional[datetime] = None
    created_at: datetime
    user_id: int  # Included in response (for ownership display)


class PhotoCreateRequest(BaseModel):
    """
    Request wrapper for creating Photo via API.
    
    PhotoCreateSchema contains image data from imalink-core + frontend organization fields.
    This wrapper adds tags (handled via separate PhotoTag relationship).
    
    Backend will add user_id from JWT token (not in PhotoCreateSchema).
    """
    photo_create_schema: PhotoCreateSchema
    tags: list[str] = Field(default_factory=list, description="Tag names to associate")


class PhotoCreateResponse(PhotoResponse):
    """
    Response after creating Photo.
    
    Extends PhotoResponse with creation-specific fields.
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
