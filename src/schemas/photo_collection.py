"""
Photo Collection schemas - Pydantic models for API operations
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# Base schemas
class PhotoCollectionBase(BaseModel):
    """Base schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: Optional[str] = Field(None, description="Optional description")


class PhotoCollectionCreate(PhotoCollectionBase):
    """Schema for creating new collection"""
    hothashes: List[str] = Field(default_factory=list, description="Initial photos (optional)")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Collection name cannot be empty or whitespace only')
        return v.strip()


class PhotoCollectionUpdate(BaseModel):
    """Schema for updating collection metadata (not photos)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Collection name cannot be empty or whitespace only')
        return v.strip() if v else None


class PhotoCollectionResponse(PhotoCollectionBase):
    """Schema for collection in API responses"""
    id: int
    user_id: int
    hothashes: List[str] = Field(default_factory=list)
    photo_count: int = Field(..., description="Number of photos in collection")
    cover_photo_hothash: Optional[str] = Field(None, description="First photo (cover)")
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Photo management schemas
class AddPhotosRequest(BaseModel):
    """Request to add photos to collection"""
    hothashes: List[str] = Field(..., min_length=1, description="Photos to add")
    
    @field_validator('hothashes')
    @classmethod
    def validate_hothashes(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError('Must provide at least one hothash')
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for h in v:
            if h not in seen:
                seen.add(h)
                unique.append(h)
        return unique


class RemovePhotosRequest(BaseModel):
    """Request to remove photos from collection"""
    hothashes: List[str] = Field(..., min_length=1, description="Photos to remove")
    
    @field_validator('hothashes')
    @classmethod
    def validate_hothashes(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError('Must provide at least one hothash')
        return list(set(v))  # Remove duplicates


class ReorderPhotosRequest(BaseModel):
    """Request to reorder photos in collection"""
    hothashes: List[str] = Field(..., min_length=1, description="All photos in new order")
    
    @field_validator('hothashes')
    @classmethod
    def validate_hothashes(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError('Must provide at least one hothash')
        if len(v) != len(set(v)):
            raise ValueError('Duplicate hothashes not allowed in reorder')
        return v


class PhotoManagementResponse(BaseModel):
    """Response for photo add/remove/reorder operations"""
    collection_id: int
    photo_count: int = Field(..., description="New photo count after operation")
    affected_count: int = Field(..., description="Number of photos added/removed")
    cover_photo_hothash: Optional[str] = Field(None, description="New cover photo")


class CollectionListResponse(BaseModel):
    """Response for listing collections"""
    collections: List[PhotoCollectionResponse]
    total: int = Field(..., description="Total number of collections")
