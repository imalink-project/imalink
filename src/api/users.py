"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserResponse, UserUpdate, UserChangePassword
from src.api.dependencies import get_current_active_user
from src.models.user import User
from src.utils.security import verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user's profile information with statistics
    """
    # Add statistics to response
    user_response = UserResponse.from_orm(current_user)
    user_response.photos_count = current_user.photos_count
    user_response.import_sessions_count = current_user.import_sessions_count
    user_response.authors_count = current_user.authors_count
    # Note: image_files_count removed - ImageFile has no user_id, access via Photo
    
    return user_response


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information
    
    Args:
        user_update: Updated user information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If update fails (e.g., email already exists)
    """
    user_repo = UserRepository(db)
    
    # Extract non-None values from update request
    update_data = user_update.dict(exclude_unset=True)
    
    if not update_data:
        # No fields to update, return current user
        return UserResponse.from_orm(current_user)
    
    try:
        updated_user = user_repo.update(getattr(current_user, 'id'), **update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/me/change-password")
async def change_my_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password
    
    Args:
        password_data: Current and new password
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(password_data.current_password, getattr(current_user, 'password_hash')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user_repo = UserRepository(db)
    success = user_repo.change_password(getattr(current_user, 'id'), password_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return {"message": "Password changed successfully"}


@router.delete("/me")
async def deactivate_my_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user's account
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    user_repo = UserRepository(db)
    success = user_repo.deactivate(getattr(current_user, 'id'))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )
    
    return {"message": "Account deactivated successfully"}