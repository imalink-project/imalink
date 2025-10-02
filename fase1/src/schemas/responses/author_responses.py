"""
Author response schemas
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


class AuthorListResponse(BaseModel):
    """Response for author listing endpoints"""
    authors: List[AuthorResponse] = Field(..., description="Array of authors")
    total: int = Field(..., description="Total number of authors")
    
    class Config:
        from_attributes = True


class AuthorStatistics(BaseModel):
    """Author statistics model"""
    total_authors: int
    authors_with_images: int
    avg_images_per_author: float
    top_authors: List[AuthorResponse]