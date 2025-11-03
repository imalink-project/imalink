"""
Repository for User model operations
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.user import User
from utils.security import hash_password


class UserRepository:
    """Repository for User database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, username: str, email: str, password: str, display_name: Optional[str] = None) -> User:
        """
        Create a new user
        
        Args:
            username: Unique username
            email: User's email address
            password: Plain text password (will be hashed)
            display_name: Optional display name
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check if username already exists
        if self.get_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        
        # Check if email already exists
        if self.get_by_email(email):
            raise ValueError(f"Email '{email}' already exists")
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            is_active=True
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Failed to create user: {str(e)}")
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Update user fields
        
        Args:
            user_id: ID of user to update
            **kwargs: Fields to update (email, display_name, is_active)
            
        Returns:
            Updated User instance or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Update allowed fields
        allowed_fields = {"email", "display_name", "is_active"}
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Failed to update user (email may already exist)")
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """
        Change user's password
        
        Args:
            user_id: ID of user
            new_password: New plain text password
            
        Returns:
            True if successful, False if user not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        # Update password hash
        setattr(user, 'password_hash', hash_password(new_password))
        self.db.commit()
        return True
    
    def deactivate(self, user_id: int) -> bool:
        """
        Deactivate user account
        
        Args:
            user_id: ID of user to deactivate
            
        Returns:
            True if successful, False if user not found
        """
        return self.update(user_id, is_active=False) is not None
    
    def get_all_active(self) -> list[User]:
        """Get all active users"""
        return self.db.query(User).filter(User.is_active == True).all()