"""
Import session response schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ImportSessionResponse(BaseModel):
    """Import session metadata response"""
    id: int
    imported_at: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    default_author_id: Optional[int] = None
    images_count: int = Field(0, description="Number of images in this import session")
    
    class Config:
        from_attributes = True


class ImportSessionListResponse(BaseModel):
    """Response for import session list"""
    sessions: list[ImportSessionResponse]
    total: int = Field(..., description="Total number of sessions")
    
    class Config:
        from_attributes = True