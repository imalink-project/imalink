"""
PhotoStack Request Schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class PhotoStackCreateRequest(BaseModel):
    """Request model for creating a new PhotoStack"""
    
    stack_type: Optional[str] = Field(None, max_length=50, description="Type of stack: burst, panorama, timelapse, etc.")
    title: Optional[str] = Field(None, max_length=200, description="Optional user-friendly name for the stack")
    
    @field_validator('stack_type')
    @classmethod
    def validate_stack_type(cls, v):
        if v is not None and not v.strip():
            return None  # Convert empty strings to None
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and not v.strip():
            return None
        return v


class PhotoStackUpdateRequest(BaseModel):
    """Request model for updating PhotoStack metadata"""
    
    stack_type: Optional[str] = Field(None, max_length=50, description="Updated stack type")
    title: Optional[str] = Field(None, max_length=200, description="Updated title")
    
    @field_validator('stack_type')
    @classmethod
    def validate_stack_type(cls, v):
        if v is not None and not v.strip():
            return None
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and not v.strip():
            return None
        return v


class PhotoStackAddPhotoRequest(BaseModel):
    """Request model for adding a single photo to stack"""
    
    photo_hothash: str = Field(..., description="Photo hash to add to stack")
    
    @field_validator('photo_hothash')
    @classmethod
    def validate_photo_hothash(cls, v):
        if not v or not v.strip():
            raise ValueError("Photo hash is required")
        return v.strip()