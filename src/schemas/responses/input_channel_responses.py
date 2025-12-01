"""
Input channel response schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class InputChannelResponse(BaseModel):
    """Input channel metadata response"""
    id: int
    imported_at: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    default_author_id: Optional[int] = None
    images_count: int = Field(0, description="Number of images in this input channel")
    
    class Config:
        from_attributes = True


class InputChannelListResponse(BaseModel):
    """Response for input channel list"""
    channels: list[InputChannelResponse]
    total: int = Field(..., description="Total number of channels")
    
    class Config:
        from_attributes = True