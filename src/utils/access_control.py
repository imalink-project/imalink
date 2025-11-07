"""
Access control utilities for visibility-based permissions

Phase 1: Private vs Public
- Private: Only owner can view/edit
- Public: Everyone can view (including anonymous), only owner can edit

Future phases will add:
- Collaborators: Invited users with view or edit permissions
- Space: All members of a shared workspace
"""
from typing import Optional
from src.models.photo import Photo
from src.models.phototext_document import PhotoTextDocument
from src.models.user import User


def can_view_photo(photo: Photo, user: Optional[User]) -> bool:
    """
    Determine if user can view photo
    
    Phase 1 Rules:
    1. Public photos visible to everyone (including anonymous)
    2. Owner can always see own photos
    3. Private photos only visible to owner
    
    Args:
        photo: Photo to check access for
        user: Current user (None if anonymous)
        
    Returns:
        True if user can view the photo, False otherwise
    """
    # Public - anyone can see
    if photo.visibility == "public":
        return True
    
    # Must be authenticated for non-public
    if user is None:
        return False
    
    # Owner always sees own content
    if photo.user_id == user.id:
        return True
    
    # Phase 1: Only public or owner access
    return False


def can_edit_photo(photo: Photo, user: Optional[User]) -> bool:
    """
    Determine if user can edit photo
    
    Phase 1 Rules:
    1. Only owner can edit
    
    Args:
        photo: Photo to check access for
        user: Current user (None if anonymous)
        
    Returns:
        True if user can edit the photo, False otherwise
    """
    # Must be authenticated
    if user is None:
        return False
    
    # Only owner can edit
    return photo.user_id == user.id


def can_view_document(document: PhotoTextDocument, user: Optional[User]) -> bool:
    """
    Determine if user can view PhotoText document
    
    Phase 1 Rules:
    1. Public documents visible to everyone (including anonymous)
    2. Owner can always see own documents
    3. Private documents only visible to owner
    
    Args:
        document: PhotoTextDocument to check access for
        user: Current user (None if anonymous)
        
    Returns:
        True if user can view the document, False otherwise
    """
    # Public - anyone can see
    if document.visibility == "public":
        return True
    
    # Must be authenticated for non-public
    if user is None:
        return False
    
    # Owner always sees own content
    if document.user_id == user.id:
        return True
    
    # Phase 1: Only public or owner access
    return False


def can_edit_document(document: PhotoTextDocument, user: Optional[User]) -> bool:
    """
    Determine if user can edit PhotoText document
    
    Phase 1 Rules:
    1. Only owner can edit
    
    Args:
        document: PhotoTextDocument to check access for
        user: Current user (None if anonymous)
        
    Returns:
        True if user can edit the document, False otherwise
    """
    # Must be authenticated
    if user is None:
        return False
    
    # Only owner can edit
    return document.user_id == user.id
