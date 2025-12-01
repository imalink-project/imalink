"""
Input Channel Repository - Data Access Layer for InputChannel simple CRUD
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models import InputChannel


class InputChannelRepository:
    """Repository class for InputChannel simple CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # === Simple CRUD Operations ===
    
    def get_channel_by_id(self, channel_id: int, user_id: int) -> Optional[InputChannel]:
        """Get InputChannel by ID (user-scoped)"""
        query = (
            self.db.query(InputChannel)
            .filter(InputChannel.id == channel_id)
            .filter(InputChannel.user_id == user_id)
        )
        
        return query.first()
    
    def get_protected_channel(self, user_id: int) -> Optional[InputChannel]:
        """
        Get user's protected InputChannel (default channel for quick uploads)
        
        Used when input_channel_id is not provided in PhotoCreateSchema API.
        """
        query = (
            self.db.query(InputChannel)
            .filter(InputChannel.is_protected == True)
            .filter(InputChannel.user_id == user_id)
        )
        
        return query.first()
    
    def get_all_channels(self, user_id: int, limit: int = 50, offset: int = 0) -> List[InputChannel]:
        """Get all InputChannels with pagination (user-scoped)"""
        query = (
            self.db.query(InputChannel)
            .filter(InputChannel.user_id == user_id)
            .order_by(desc(InputChannel.imported_at))
        )
        
        return query.limit(limit).offset(offset).all()
    
    def count_channels(self, user_id: int) -> int:
        """Count total InputChannels (user-scoped)"""
        query = self.db.query(InputChannel).filter(InputChannel.user_id == user_id)
        
        return query.count()
    
    def create_simple(
        self,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ) -> InputChannel:
        """Create a simple InputChannel (user metadata only, user-scoped)"""
        channel = InputChannel(
            user_id=user_id,
            imported_at=datetime.now(),
            title=title,
            description=description,
            default_author_id=default_author_id
        )
        
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel
    
    def update_simple(
        self,
        channel_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ) -> Optional[InputChannel]:
        """Update InputChannel metadata (user-scoped)"""
        channel = self.get_channel_by_id(channel_id, user_id)
        if not channel:
            return None
        
        if title is not None:
            setattr(channel, 'title', title)
        if description is not None:
            setattr(channel, 'description', description)
        if default_author_id is not None:
            setattr(channel, 'default_author_id', default_author_id)
        
        self.db.commit()
        self.db.refresh(channel)
        return channel
    
    def delete(self, channel_id: int, user_id: int) -> bool:
        """Delete InputChannel (user-scoped)"""
        channel = self.get_channel_by_id(channel_id, user_id)
        if not channel:
            return False
        
        self.db.delete(channel)
        self.db.commit()
        return True
