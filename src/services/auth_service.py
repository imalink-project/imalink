"""
Authentication service for user login/registration
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.utils.security import verify_password, create_access_token
from src.schemas.user import UserCreate, UserResponse


class AuthService:
    """Service for user authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/password
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        # Try to find user by username first, then by email
        user = self.user_repo.get_by_username(username)
        if not user:
            user = self.user_repo.get_by_email(username)
        
        if not user:
            return None
        
        # Check if user is active
        if not getattr(user, 'is_active'):
            return None
        
        # Verify password
        if not verify_password(password, getattr(user, 'password_hash')):
            return None
        
        return user
    
    def login(self, username: str, password: str) -> Optional[Tuple[str, User]]:
        """
        Login user and return access token
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            Tuple of (access_token, user) if successful, None otherwise
        """
        user = self.authenticate_user(username, password)
        if not user:
            return None
        
        # Create JWT token with user ID as subject
        access_token = create_access_token(data={"sub": str(user.id)})
        return access_token, user
    
    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user
        
        Args:
            user_data: User registration data
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If username or email already exists
        """
        return self.user_repo.create(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )
    
    def get_current_user(self, user_id: int) -> Optional[User]:
        """
        Get current user by ID (from JWT token)
        
        Args:
            user_id: User ID from JWT token
            
        Returns:
            User instance if found and active, None otherwise
        """
        user = self.user_repo.get_by_id(user_id)
        if user and getattr(user, 'is_active'):
            return user
        return None