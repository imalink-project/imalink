"""
Tag schemas for request/response validation
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TagBase(BaseModel):
    """Base tag schema with name validation"""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name (will be normalized to lowercase)")
    
    @field_validator('name')
    @classmethod
    def normalize_and_validate_name(cls, v: str) -> str:
        """Normalize tag name to lowercase and validate format"""
        # Strip whitespace
        v = v.strip()
        
        # Validate length after strip
        if not v or len(v) > 50:
            raise ValueError('Tag name must be 1-50 characters after trimming whitespace')
        
        # Validate characters (alphanumeric, space, hyphen, underscore)
        if not all(c.isalnum() or c in (' ', '-', '_') for c in v):
            raise ValueError('Tag name can only contain alphanumeric characters, spaces, hyphens, and underscores')
        
        # Convert to lowercase for consistency
        return v.lower()


class TagCreate(TagBase):
    """Schema for creating a new tag"""
    pass


class TagUpdate(BaseModel):
    """Schema for updating/renaming a tag"""
    new_name: str = Field(..., min_length=1, max_length=50, description="New tag name")
    
    @field_validator('new_name')
    @classmethod
    def normalize_and_validate_name(cls, v: str) -> str:
        """Normalize tag name to lowercase and validate format"""
        v = v.strip()
        if not v or len(v) > 50:
            raise ValueError('Tag name must be 1-50 characters after trimming whitespace')
        if not all(c.isalnum() or c in (' ', '-', '_') for c in v):
            raise ValueError('Tag name can only contain alphanumeric characters, spaces, hyphens, and underscores')
        return v.lower()


class TagSummary(BaseModel):
    """Minimal tag info for inclusion in photo responses"""
    id: int
    name: str
    
    model_config = {"from_attributes": True}


class TagResponse(BaseModel):
    """Full tag response with metadata"""
    id: int
    name: str
    photo_count: int = Field(default=0, description="Number of photos with this tag")
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    """Response for listing tags"""
    tags: List[TagResponse]
    total: int


class TagAutocompleteItem(BaseModel):
    """Autocomplete suggestion item"""
    id: int
    name: str
    photo_count: int
    
    model_config = {"from_attributes": True}


class TagAutocompleteResponse(BaseModel):
    """Response for autocomplete endpoint"""
    suggestions: List[TagAutocompleteItem]


class AddTagsRequest(BaseModel):
    """Request body for adding tags to photo"""
    tags: List[str] = Field(..., min_length=1, description="List of tag names to add")
    
    @field_validator('tags')
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        """Normalize all tag names"""
        normalized = []
        for tag in v:
            tag = tag.strip().lower()
            if tag and len(tag) <= 50:
                if all(c.isalnum() or c in (' ', '-', '_') for c in tag):
                    normalized.append(tag)
        
        if not normalized:
            raise ValueError('At least one valid tag is required')
        
        return normalized


class AddTagsResponse(BaseModel):
    """Response after adding tags to photo"""
    hothash: str
    tags: List[TagSummary]
    added: int = Field(description="Number of tags added")
    skipped: int = Field(default=0, description="Number of tags that were already applied")
    message: Optional[str] = None


class RemoveTagResponse(BaseModel):
    """Response after removing a tag from photo"""
    hothash: str
    removed_tag: str
    remaining_tags: List[TagSummary]


class DeleteTagResponse(BaseModel):
    """Response after deleting a tag completely"""
    deleted_tag: str
    photos_affected: int
    message: str


class RenameTagResponse(BaseModel):
    """Response after renaming a tag"""
    id: int
    old_name: str
    new_name: str
    photo_count: int
    updated_at: datetime
