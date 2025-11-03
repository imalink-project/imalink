"""
Common response schemas and base models
Provides consistent API response structure across all endpoints
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Generic type variable for response data
T = TypeVar('T')


class PaginationMeta(BaseModel):
    """Metadata for paginated responses"""
    total: int = Field(..., description="Total number of items")
    offset: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    page: int = Field(..., description="Current page number (1-based)")
    pages: int = Field(..., description="Total number of pages")


class PaginationLinks(BaseModel):
    """Navigation links for paginated responses (HATEOAS)"""
    self: Optional[str] = Field(None, description="Current page URL")
    first: Optional[str] = Field(None, description="First page URL")
    prev: Optional[str] = Field(None, description="Previous page URL") 
    next: Optional[str] = Field(None, description="Next page URL")
    last: Optional[str] = Field(None, description="Last page URL")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    data: List[T] = Field(..., description="Array of response items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    links: Optional[PaginationLinks] = Field(None, description="Navigation links")


class SingleResponse(BaseModel, Generic[T]):
    """Generic single item response wrapper"""
    data: T = Field(..., description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name for validation errors")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: ErrorDetail = Field(..., description="Error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class SuccessResponse(BaseModel):
    """Generic success response for operations without data"""
    success: bool = Field(True, description="Operation success indicator")
    message: str = Field(..., description="Success message")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field("1.0.0", description="API version")
    uptime: Optional[str] = Field(None, description="Service uptime")


# Helper functions for creating responses
def create_paginated_response(
    data: List[T], 
    total: int, 
    offset: int = 0, 
    limit: int = 100,
    base_url: Optional[str] = None
) -> PaginatedResponse[T]:
    """Helper to create paginated response with calculated metadata"""
    page = (offset // limit) + 1
    pages = (total + limit - 1) // limit if limit > 0 else 1
    
    meta = PaginationMeta(
        total=total,
        offset=offset,
        limit=limit,
        page=page,
        pages=pages
    )
    
    links = None
    if base_url:
        links = PaginationLinks(
            self=f"{base_url}?offset={offset}&limit={limit}",
            first=f"{base_url}?offset=0&limit={limit}",
            prev=f"{base_url}?offset={max(0, offset-limit)}&limit={limit}" if offset > 0 else None,
            next=f"{base_url}?offset={offset+limit}&limit={limit}" if offset + limit < total else None,
            last=f"{base_url}?offset={max(0, (pages-1)*limit)}&limit={limit}" if pages > 1 else None
        )
    
    return PaginatedResponse(data=data, meta=meta, links=links)


def create_success_response(message: str, **meta) -> SuccessResponse:
    """Helper to create success response"""
    return SuccessResponse(
        success=True,
        message=message,
        meta=meta if meta else None
    )


def create_error_response(
    code: str, 
    message: str, 
    field: Optional[str] = None,
    request_id: Optional[str] = None,
    **details
) -> ErrorResponse:
    """Helper to create error response"""
    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            field=field,
            details=details if details else None
        ),
        request_id=request_id
    )