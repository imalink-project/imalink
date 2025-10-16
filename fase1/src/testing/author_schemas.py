"""
Author-related Pydantic schemas for API requests and responses
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AuthorResponse(BaseModel):
    """Author response model"""
    id: int
    name: str
    email: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    image_count: int = Field(0, description="Number of images by this author")
    
    class Config:
        from_attributes = True


class AuthorCreateRequest(BaseModel):
    """Request model for creating authors"""
    name: str = Field(..., min_length=1, max_length=255, description="Author name")
    email: Optional[str] = Field(None, max_length=255, description="Author email")
    bio: Optional[str] = Field(None, max_length=2000, description="Author biography")


class AuthorUpdateRequest(BaseModel):
    """Request model for updating authors"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Author name")
    email: Optional[str] = Field(None, max_length=255, description="Author email")
    bio: Optional[str] = Field(None, max_length=2000, description="Author biography")


class AuthorListResponse(BaseModel):
    """Response for author listing endpoints"""
    authors: List[AuthorResponse] = Field(..., description="Array of authors")
    total: int = Field(..., description="Total number of authors")
    
    class Config:
        from_attributes = True