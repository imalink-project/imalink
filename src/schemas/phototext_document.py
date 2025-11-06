"""
PhotoTextDocument-related Pydantic schemas for API requests and responses
Provides type-safe data models for PhotoText operations
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class DocumentType(str, Enum):
    """PhotoText document types"""
    GENERAL = "general"      # Full-featured (headings, paragraphs, lists, images)
    ALBUM = "album"          # Image-focused (only images/collages)
    SLIDESHOW = "slideshow"  # Presentation-style (single images per block)


class CoverImage(BaseModel):
    """Cover image reference"""
    hash: str = Field(..., min_length=71, max_length=71, description="SHA256 hash (sha256_ + 64 hex chars)")
    alt: str = Field(..., min_length=1, max_length=500, description="Alt text for cover image")
    
    @field_validator('hash')
    @classmethod
    def validate_hash_format(cls, v):
        """Validate hash format: sha256_ + 64 hex chars"""
        if not v.startswith('sha256_'):
            raise ValueError('Hash must start with sha256_')
        hex_part = v[7:]
        if len(hex_part) != 64:
            raise ValueError('Hash must have 64 hexadecimal characters after sha256_')
        try:
            int(hex_part, 16)
        except ValueError:
            raise ValueError('Hash must contain only hexadecimal characters after sha256_')
        return v


class PhotoTextDocumentCreate(BaseModel):
    """Schema for creating a PhotoText document"""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    document_type: DocumentType = Field(..., description="Document type (general/album/slideshow)")
    content: dict = Field(..., description="Complete PhotoText JSON document structure")
    abstract: Optional[str] = Field(None, max_length=5000, description="Short description/summary")
    cover_image: Optional[CoverImage] = Field(None, description="Cover image reference")
    is_published: bool = Field(default=False, description="Publication status")
    
    @field_validator('content')
    @classmethod
    def validate_content_structure(cls, v):
        """Validate that content has required PhotoText fields"""
        if not isinstance(v, dict):
            raise ValueError('Content must be a JSON object')
        
        # Required fields in PhotoText document
        required_fields = ['version', 'documentType', 'title', 'blocks']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Content missing required field: {field}')
        
        # Validate blocks is an array
        if not isinstance(v.get('blocks'), list):
            raise ValueError('Content blocks must be an array')
        
        return v


class PhotoTextDocumentUpdate(BaseModel):
    """Schema for updating a PhotoText document"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Document title")
    content: Optional[dict] = Field(None, description="Complete PhotoText JSON document structure")
    abstract: Optional[str] = Field(None, max_length=5000, description="Short description/summary")
    cover_image: Optional[CoverImage] = Field(None, description="Cover image reference")
    is_published: Optional[bool] = Field(None, description="Publication status")
    
    @field_validator('content')
    @classmethod
    def validate_content_structure(cls, v):
        """Validate that content has required PhotoText fields"""
        if v is None:
            return v
            
        if not isinstance(v, dict):
            raise ValueError('Content must be a JSON object')
        
        # Required fields in PhotoText document
        required_fields = ['version', 'documentType', 'title', 'blocks']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Content missing required field: {field}')
        
        # Validate blocks is an array
        if not isinstance(v.get('blocks'), list):
            raise ValueError('Content blocks must be an array')
        
        return v


class PhotoTextDocumentResponse(BaseModel):
    """Schema for PhotoText document responses"""
    id: int = Field(..., description="Document ID")
    user_id: int = Field(..., description="Owner user ID")
    title: str = Field(..., description="Document title")
    document_type: str = Field(..., description="Document type")
    content: dict = Field(..., description="Complete PhotoText JSON document")
    abstract: Optional[str] = Field(None, description="Short description")
    cover_image_hash: Optional[str] = Field(None, description="Cover image hash")
    cover_image_alt: Optional[str] = Field(None, description="Cover image alt text")
    is_published: bool = Field(..., description="Publication status")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    version: str = Field(..., description="Document version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PhotoTextDocumentSummary(BaseModel):
    """Lightweight document info for list views"""
    id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    document_type: str = Field(..., description="Document type")
    abstract: Optional[str] = Field(None, description="Short description")
    cover_image_hash: Optional[str] = Field(None, description="Cover image hash")
    cover_image_alt: Optional[str] = Field(None, description="Cover image alt text")
    is_published: bool = Field(..., description="Publication status")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PhotoTextDocumentListResponse(BaseModel):
    """Schema for paginated document list responses"""
    documents: List[PhotoTextDocumentSummary] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents matching filters")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
