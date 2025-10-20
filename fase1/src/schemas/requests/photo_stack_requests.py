"""
PhotoStack Request Schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class PhotoStackCreateRequest(BaseModel):
    """Request model for creating a new PhotoStack"""
    
    cover_photo_hothash: Optional[str] = Field(None, description="Photo hash to use as cover image")
    stack_type: Optional[str] = Field(None, max_length=50, description="Type of stack: panorama, burst, animation, etc.")
    
    @validator('stack_type')
    def validate_stack_type(cls, v):
        if v is not None and not v.strip():
            return None  # Convert empty strings to None
        return v


class PhotoStackUpdateRequest(BaseModel):
    """Request model for updating PhotoStack metadata"""
    
    cover_photo_hothash: Optional[str] = Field(None, description="Updated cover photo")
    stack_type: Optional[str] = Field(None, max_length=50, description="Updated stack type")
    
    @validator('stack_type')
    def validate_stack_type(cls, v):
        if v is not None and not v.strip():
            return None
        return v


class PhotoStackAddPhotoRequest(BaseModel):
    """Request model for adding a single photo to stack"""
    
    photo_hothash: str = Field(..., description="Photo hash to add to stack")
    
    @validator('photo_hothash')
    def validate_photo_hothash(cls, v):
        if not v or not v.strip():
            raise ValueError("Photo hash is required")
        return v.strip()