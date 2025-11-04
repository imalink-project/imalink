"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database.connection import get_db
from src.services.auth_service import AuthService
from src.schemas.user import UserCreate, UserResponse, UserLogin, UserToken
from src.api.dependencies import get_current_active_user
from src.models.user import User
from src.utils.audit_logger import log_audit_event, log_security_event, AuditAction

router = APIRouter(prefix="/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # Limit registrations to prevent abuse
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account
    
    Rate limit: 5 registrations per hour per IP
    
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
        
        # Log successful registration
        log_audit_event(
            action=AuditAction.USER_REGISTER,
            user_id=user.id,
            username=user.username,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            details={"email": user.email}
        )
        
        return UserResponse.from_orm(user)
    except ValueError as e:
        # Log failed registration attempt
        log_security_event(
            event_type="REGISTRATION_FAILED",
            message=str(e),
            username=user_data.username,
            ip_address=request.client.host if request.client else None,
            details={"email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=UserToken)
@limiter.limit("10/minute")  # Protect against brute force attacks
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user and return access token
    
    Rate limit: 10 login attempts per minute per IP
    
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
        # Log failed login attempt
        log_security_event(
            event_type="LOGIN_FAILED",
            message="Invalid credentials",
            username=login_data.username,
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token, user = result
    
    # Log successful login
    log_audit_event(
        action=AuditAction.USER_LOGIN,
        user_id=user.id,
        username=user.username,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None
    )
    
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