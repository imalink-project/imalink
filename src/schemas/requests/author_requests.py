"""
Author request schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


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