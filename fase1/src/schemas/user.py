"""
Pydantic schemas for User model API operations
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base User schema with common fields"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User's email address")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name for the user")
    is_active: bool = Field(True, description="Whether the user account is active")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User's password (will be hashed)")


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = Field(None, description="New email address")
    display_name: Optional[str] = Field(None, max_length=100, description="New display name")
    is_active: Optional[bool] = Field(None, description="Update active status")


class UserChangePassword(BaseModel):
    """Schema for changing user password"""
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password")


class UserResponse(UserBase):
    """Schema for User API responses"""
    id: int = Field(..., description="User's unique ID")
    created_at: datetime = Field(..., description="When the user account was created")
    updated_at: datetime = Field(..., description="When the user account was last updated")
    
    # Statistics (populated by service layer)
    photos_count: int = Field(0, description="Number of photos owned by this user")
    import_sessions_count: int = Field(0, description="Number of import sessions created by this user")
    authors_count: int = Field(0, description="Number of authors created by this user")
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User's password")


class UserToken(BaseModel):
    """Schema for authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")