"""
Authentication dependencies for FastAPI endpoints
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database.connection import get_db
from services.auth_service import AuthService
from models.user import User
from utils.security import get_user_id_from_token
from core.config import config

# HTTP Bearer token scheme for extracting JWT from Authorization header
security = HTTPBearer(auto_error=False)  # auto_error=False to allow optional auth


def _get_test_user(db: Session) -> User:
    """
    Helper function to get or create a test user when DISABLE_AUTH is enabled.
    Returns the first user in the system to ensure access to existing data.
    """
    # Get the first user (usually the one with actual data)
    test_user = db.query(User).order_by(User.id).first()
    
    if not test_user:
        # Create a test user if no users exist
        auth_service = AuthService(db)
        from schemas.user import UserCreate
        user_data = UserCreate(
            username="test_user",
            email="test@example.com",
            password="test_password",
            full_name="Test User"
        )
        test_user = auth_service.register_user(user_data)
    
    return test_user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    
    When DISABLE_AUTH is enabled, returns a test user without requiring authentication.
    
    Args:
        credentials: HTTP Authorization credentials containing JWT token
        db: Database session
        
    Returns:
        Current authenticated User (or test user if auth is disabled)
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Check if authentication is disabled for testing
    if config.DISABLE_AUTH:
        # Return the first user without requiring authentication
        return _get_test_user(db)
    
    # Normal authentication flow
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Get user ID from token
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    auth_service = AuthService(db)
    user = auth_service.get_current_user(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated and active user
    
    When DISABLE_AUTH is enabled, returns a test user without requiring authentication.
    
    Args:
        credentials: Optional HTTP Authorization credentials containing JWT token
        db: Database session
        
    Returns:
        Current active User (or test user if auth is disabled)
        
    Raises:
        HTTPException: If user is inactive or authentication fails
    """
    # Check if authentication is disabled for testing
    if config.DISABLE_AUTH:
        # Return the first user without requiring authentication
        return _get_test_user(db)
    
    # Normal authentication flow        return test_user
    
    # Normal authentication flow
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Get user ID from token
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    auth_service = AuthService(db)
    current_user = auth_service.get_current_user(int(user_id))
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not getattr(current_user, 'is_active'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get current user (for endpoints that work with or without auth)
    
    Args:
        credentials: Optional HTTP Authorization credentials
        db: Database session
        
    Returns:
        Current User if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = get_user_id_from_token(token)
        if not user_id:
            return None
        
        auth_service = AuthService(db)
        return auth_service.get_current_user(int(user_id))
    except Exception:
        # If any error occurs, just return None (no authentication)
        return None