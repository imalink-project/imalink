"""
Schemas package for API data models and validation
"""
# Import commonly used schemas for convenience
from .responses.author_responses import AuthorResponse, AuthorListResponse
from .requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest
from .common import PaginatedResponse, SingleResponse

__all__ = [
    "AuthorResponse", 
    "AuthorListResponse",
    "AuthorCreateRequest", 
    "AuthorUpdateRequest",
    "PaginatedResponse",
    "SingleResponse"
]