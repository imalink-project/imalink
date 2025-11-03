"""
Photo search related schemas
Handles both ad-hoc searches and saved search CRUD operations
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SavedPhotoSearchCreate(BaseModel):
    """Request to create a new saved photo search"""
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(..., min_length=1, max_length=100, description="User-friendly name for the search")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    search_criteria: Dict[str, Any] = Field(..., description="PhotoSearchRequest as dict")
    is_favorite: bool = Field(False, description="Mark as favorite")


class SavedPhotoSearchUpdate(BaseModel):
    """Request to update a saved photo search"""
    model_config = ConfigDict(extra='forbid')
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    search_criteria: Optional[Dict[str, Any]] = Field(None, description="Updated search criteria")
    is_favorite: Optional[bool] = None


class SavedPhotoSearchResponse(BaseModel):
    """Response model for saved photo search"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    description: Optional[str]
    search_criteria: Dict[str, Any]
    is_favorite: bool
    result_count: Optional[int]
    last_executed: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SavedPhotoSearchSummary(BaseModel):
    """Summary view of saved photo search (for lists)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    is_favorite: bool
    result_count: Optional[int]
    last_executed: Optional[datetime]
    created_at: datetime


class SavedPhotoSearchListResponse(BaseModel):
    """Paginated list of saved photo searches"""
    searches: list[SavedPhotoSearchSummary]
    total: int
    offset: int
    limit: int
