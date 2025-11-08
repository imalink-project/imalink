"""
Access control utilities for visibility-based permissions

Phase 1: 4-level visibility
- Private: Only owner can view/edit
- Space: Space members can view (Phase 2 - treated as private in Phase 1)
- Authenticated: All logged-in users can view, only owner can edit
- Public: Everyone can view (including anonymous), only owner can edit

Future phases will add:
- Phase 2: Space infrastructure (PhotoSpaceMembership many-to-many relationships)
"""
from typing import Optional, List
from src.models.photo import Photo
from src.models.phototext_document import PhotoTextDocument
from src.models.user import User


def can_view_photo(photo: Photo, user: Optional[User], user_space_ids: Optional[List[int]] = None) -> bool:
    """
    Determine if user can view photo
    
    Phase 1 Rules:
    1. Public photos visible to everyone (including anonymous)
    2. Authenticated photos visible to all logged-in users
    3. Space photos treated as private in Phase 1 (space infrastructure not ready)
    4. Owner can always see own photos
    5. Private photos only visible to owner
    
    Phase 2 will add:
    - Space visibility: Check user_space_ids for membership
    
    Args:
        photo: Photo to check access for
        user: Current user (None if anonymous)
        user_space_ids: List of space IDs the user belongs to (for Phase 2)
        
    Returns:
        True if user can view the photo, False otherwise
    """
    # Public - anyone can see
    if photo.visibility == "public":
        return True
    
    # Authenticated - any logged-in user can see
    if photo.visibility == "authenticated":
        return user is not None
    
    # Must be authenticated for space/private
    if user is None:
        return False
    
    # Owner always sees own content
    if photo.user_id == user.id:
        return True
    
    # Phase 1: Space treated as private (no space infrastructure yet)
    # Phase 2 will check: if photo.visibility == "space" and user_space_ids...
    
    # Private - only owner
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


def can_view_document(document: PhotoTextDocument, user: Optional[User], user_space_ids: Optional[List[int]] = None) -> bool:
    """
    Determine if user can view PhotoText document
    
    Phase 1 Rules:
    1. Public documents visible to everyone (including anonymous)
    2. Authenticated documents visible to all logged-in users
    3. Space documents treated as private in Phase 1 (space infrastructure not ready)
    4. Owner can always see own documents
    5. Private documents only visible to owner
    
    Phase 2 will add:
    - Space visibility: Check user_space_ids for membership
    
    Args:
        document: PhotoTextDocument to check access for
        user: Current user (None if anonymous)
        user_space_ids: List of space IDs the user belongs to (for Phase 2)
        
    Returns:
        True if user can view the document, False otherwise
    """
    # Public - anyone can see
    if document.visibility == "public":
        return True
    
    # Authenticated - any logged-in user can see
    if document.visibility == "authenticated":
        return user is not None
    
    # Must be authenticated for space/private
    if user is None:
        return False
    
    # Owner always sees own content
    if document.user_id == user.id:
        return True
    
    # Phase 1: Space treated as private (no space infrastructure yet)
    # Phase 2 will check: if document.visibility == "space" and user_space_ids...
    
    # Private - only owner
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
