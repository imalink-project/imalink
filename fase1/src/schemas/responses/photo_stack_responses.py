"""
PhotoStack Response Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PhotoStackSummary(BaseModel):
    """Summary view of a PhotoStack (used in lists)"""
    
    id: int = Field(..., description="Unique identifier for the photo stack")
    stack_type: Optional[str] = Field(None, description="Type of stack")
    cover_photo_hothash: Optional[str] = Field(None, description="Hash of the cover photo")
    photo_count: int = Field(..., description="Number of photos in this stack")
    created_at: datetime = Field(..., description="When the stack was created")
    updated_at: datetime = Field(..., description="When the stack was last updated")
    
    class Config:
        from_attributes = True


class PhotoStackDetail(BaseModel):
    """Detailed view of a PhotoStack with photo hashes"""
    
    id: int = Field(..., description="Unique identifier for the photo stack")
    stack_type: Optional[str] = Field(None, description="Type of stack")
    cover_photo_hothash: Optional[str] = Field(None, description="Hash of the cover photo")
    photo_hothashes: List[str] = Field(default_factory=list, description="List of photo hashes in the stack")
    created_at: datetime = Field(..., description="When the stack was created")
    updated_at: datetime = Field(..., description="When the stack was last updated")
    
    class Config:
        from_attributes = True


class PhotoStackListResponse(BaseModel):
    """Paginated response for PhotoStack listings"""
    
    stacks: List[PhotoStackSummary] = Field(default_factory=list, description="List of photo stacks")
    total_count: int = Field(..., description="Total number of stacks for user")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class PhotoStackOperationResponse(BaseModel):
    """Response for PhotoStack CRUD operations"""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    stack: Optional[PhotoStackDetail] = Field(None, description="The affected stack (for create/update operations)")
    
    class Config:
        from_attributes = True


class PhotoStackPhotoResponse(BaseModel):
    """Response for single photo add/remove operations"""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    stack: Optional[PhotoStackDetail] = Field(None, description="Updated stack details (null if stack was deleted)")
    
    class Config:
        from_attributes = True