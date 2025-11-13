"""
Authentication service for user login/registration
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.import_session import ImportSession
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
        Register a new user and create default Author + ImportSession
        
        Automatically creates:
        1. Default Author (self-author) representing the user as photographer
        2. 'Quick Add' ImportSession for immediate photo uploads
        
        The self-author:
        - Has same name as user's display_name (or username if no display_name)
        - Marked with is_self=True
        - Set as user's default_author_id
        - Used automatically when author_id not specified in photo imports
        
        The default session:
        - Cannot be deleted (is_protected=True)
        - Allows users to upload photos immediately without setup
        
        Args:
            user_data: User registration data
            
        Returns:
            Created User instance (with relationships loaded)
            
        Raises:
            ValueError: If username or email already exists
        """
        from datetime import datetime
        from src.models.author import Author
        
        # Create the user
        user = self.user_repo.create(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )
        
        # Create default self-author (represents user as photographer)
        author_name = user_data.display_name or user_data.username
        self_author = Author(
            name=author_name,
            email=user_data.email,  # Use user's email
            bio=None,
            is_self=True  # Mark as self-author
        )
        self.db.add(self_author)
        self.db.flush()  # Get self_author.id
        
        # Set user's default_author_id
        user.default_author_id = self_author.id
        
        # Create default ImportSession for quick uploads
        # is_protected=True prevents deletion (user can edit title/description)
        default_session = ImportSession(
            user_id=user.id,
            title="Quick Add",
            description="Default session for quick photo uploads.",
            imported_at=datetime.utcnow(),
            is_protected=True  # Cannot be deleted by user
        )
        
        self.db.add(default_session)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
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