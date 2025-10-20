"""
Request schemas package
"""

from .photo_stack_requests import (
    PhotoStackCreateRequest,
    PhotoStackUpdateRequest,
    PhotoStackAddPhotoRequest
)

__all__ = [
    "PhotoStackCreateRequest",
    "PhotoStackUpdateRequest", 
    "PhotoStackAddPhotoRequest"
]