"""
Dependency injection setup for ImaLink services
Provides clean dependency management for controllers
"""
from sqlalchemy.orm import Session
from fastapi import Depends

# Database dependency (reuse existing)
from database.connection import get_db

# Service imports
from services.image_service_new import ImageService
from services.author_service import AuthorService
from services.import_service import ImportService


# Image Service Dependencies
def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    """Get ImageService instance with database dependency"""
    return ImageService(db)


# Note: Selections functionality was considered but not implemented
# Focus remains on core image, author, and import functionality


# Author Service Dependencies
def get_author_service(db: Session = Depends(get_db)) -> AuthorService:
    """Get AuthorService instance with database dependency"""
    return AuthorService(db)


# Import Service Dependencies
def get_import_service(db: Session = Depends(get_db)) -> ImportService:
    """Get ImportService instance with database dependency"""
    return ImportService(db)


# Utility dependencies
def get_current_user():
    """Get current authenticated user (placeholder for future auth)"""
    # TODO: Implement when authentication is added
    return {"id": 1, "name": "Anonymous User"}


def get_pagination_params(
    offset: int = 0,
    limit: int = 100
) -> dict:
    """Standard pagination parameters"""
    return {
        "offset": max(0, offset),
        "limit": min(max(1, limit), 1000)  # Cap at 1000 items
    }