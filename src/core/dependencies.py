"""
Dependency injection setup for ImaLink services
Provides clean dependency management for controllers
"""
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

# Database dependency (reuse existing)
from src.database.connection import get_db

# Service imports
from src.services.image_file_service import ImageFileService
from src.services.author_service import AuthorService
from src.services.import_session_service import ImportSessionService
from src.services.photo_service import PhotoService
from src.services.photo_stack_service import PhotoStackService


# ImageFile Service Dependencies
def get_image_file_service(db: Session = Depends(get_db)) -> ImageFileService:
    """Get ImageFileService instance with database dependency"""
    return ImageFileService(db)


# Note: Selections functionality was considered but not implemented
# Focus remains on core image, author, and import functionality


# Author Service Dependencies
def get_author_service(db: Session = Depends(get_db)) -> AuthorService:
    """Get AuthorService instance with database dependency"""
    return AuthorService(db)


# Import Service Dependencies
def get_import_session_service(db: Session = Depends(get_db)) -> ImportSessionService:
    """Get ImportSessionService instance with database dependency"""
    return ImportSessionService(db)


# Photo Service Dependencies
def get_photo_service(db: Session = Depends(get_db)) -> PhotoService:
    """Get PhotoService instance with database dependency"""
    return PhotoService(db)


# PhotoStack Service Dependencies
def get_photo_stack_service(db: Session = Depends(get_db)) -> PhotoStackService:
    """Get PhotoStackService instance with database dependency"""
    return PhotoStackService(db)


# Import Once functionality has been integrated into ImportSessionService


# Utility dependencies
def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login")),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from JWT token"""
    from src.utils.security import get_user_id_from_token
    from src.repositories.user_repository import UserRepository
    from src.core.exceptions import AuthenticationError
    
    # Extract user ID from token
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise AuthenticationError("Invalid or expired token")
    
    # Fetch user from database
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")
    
    return user


def get_pagination_params(
    offset: int = 0,
    limit: int = 100
) -> dict:
    """Standard pagination parameters"""
    return {
        "offset": max(0, offset),
        "limit": min(max(1, limit), 1000)  # Cap at 1000 items
    }