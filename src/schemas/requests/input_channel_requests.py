"""
Input channel request schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class InputChannelCreateRequest(BaseModel):
    """Request to create an input channel (user's reference metadata)"""
    title: Optional[str] = Field(None, max_length=255, description="User's title for this channel (e.g., 'Italy Summer 2024')")
    description: Optional[str] = Field(None, description="User's notes or comments about this channel")
    default_author_id: Optional[int] = Field(None, description="Default photographer for this channel")


class InputChannelUpdateRequest(BaseModel):
    """Request to update input channel metadata"""
    title: Optional[str] = Field(None, max_length=255, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    default_author_id: Optional[int] = Field(None, description="Updated default author")