"""
Schemas package for API data models and validation
"""
# Import commonly used schemas for convenience
from .user import UserCreate, UserUpdate, UserResponse, UserLogin, UserToken, UserChangePassword
from .responses.author_responses import AuthorResponse, AuthorListResponse
from .requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest
from .image_file_upload_schemas import ImageFileNewPhotoRequest, ImageFileAddToPhotoRequest, ImageFileUploadResponse
from .common import PaginatedResponse, SingleResponse
from .phototext_document import (
    DocumentType,
    CoverImage,
    PhotoTextDocumentCreate,
    PhotoTextDocumentUpdate,
    PhotoTextDocumentResponse,
    PhotoTextDocumentSummary,
    PhotoTextDocumentListResponse
)

__all__ = [
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserLogin",
    "UserToken",
    "UserChangePassword",
    "AuthorResponse", 
    "AuthorListResponse",
    "AuthorCreateRequest", 
    "AuthorUpdateRequest",
    "ImageFileNewPhotoRequest",
    "ImageFileAddToPhotoRequest", 
    "ImageFileUploadResponse",
    "PaginatedResponse",
    "SingleResponse",
    "DocumentType",
    "CoverImage",
    "PhotoTextDocumentCreate",
    "PhotoTextDocumentUpdate",
    "PhotoTextDocumentResponse",
    "PhotoTextDocumentSummary",
    "PhotoTextDocumentListResponse"
]