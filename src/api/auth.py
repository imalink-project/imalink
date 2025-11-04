"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.services.auth_service import AuthService
from src.schemas.user import UserCreate, UserResponse, UserLogin, UserToken
from src.api.dependencies import get_current_active_user
from src.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account
    
    Args:
        user_data: User registration information
        db: Database session
        
    Returns:
        Created user information (without password)
        
    Raises:
        HTTPException: If username or email already exists
    """
    auth_service = AuthService(db)
    
    try:
        user = auth_service.register_user(user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=UserToken)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user and return access token
    
    Args:
        login_data: User login credentials
        db: Database session
        
    Returns:
        Access token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    
    result = auth_service.login(login_data.username, login_data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token, user = result
    return UserToken(
        access_token=access_token,
        token_type="bearer",
        expires_in=24 * 60 * 60,  # 24 hours in seconds
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user's profile information
    """
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout():
    """
    Logout user (placeholder endpoint)
    
    Note: With JWT tokens, logout is typically handled client-side
    by removing the token. For server-side token blacklisting,
    additional implementation would be needed.
    
    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}