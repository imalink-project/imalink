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

# HTTP Bearer token scheme for extracting JWT from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials containing JWT token
        db: Database session
        
    Returns:
        Current authenticated User
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
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
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current authenticated and active user
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current active User
        
    Raises:
        HTTPException: If user is inactive
    """
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