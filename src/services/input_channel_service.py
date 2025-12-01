"""
Input Channel Service - Simple CRUD for user's reference metadata

InputChannel is a metadata container for user's notes about input channels.
All file operations are handled by the client application.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.repositories.input_channel_repository import InputChannelRepository
from src.schemas.responses.input_channel_responses import (
    InputChannelResponse,
    InputChannelListResponse
)
from src.core.exceptions import NotFoundError


class InputChannelService:
    """Service class for InputChannel simple CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.channel_repo = InputChannelRepository(db)
    
    # === Simple CRUD Operations ===
    
    def create_simple_channel(
        self,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ):
        """Create a simple InputChannel (user metadata only)"""
        channel = self.channel_repo.create_simple(
            user_id=user_id,
            title=title,
            description=description,
            default_author_id=default_author_id
        )
        
        response = InputChannelResponse.model_validate(channel)
        response.images_count = 0  # No images yet
        return response
    
    def get_channel_by_id(self, channel_id: int, user_id: int):
        """Get InputChannel by ID (user-scoped)"""
        channel = self.channel_repo.get_channel_by_id(channel_id, user_id)
        if not channel:
            raise NotFoundError("Input channel", channel_id)
        
        return InputChannelResponse.model_validate(channel)
    
    def list_simple_channels(self, user_id: int, limit: int = 100, offset: int = 0):
        """List all InputChannels with pagination (user-scoped)"""
        channels = self.channel_repo.get_all_channels(limit=limit, offset=offset, user_id=user_id)
        total = self.channel_repo.count_channels(user_id=user_id)
        
        channel_responses = [InputChannelResponse.model_validate(c) for c in channels]
        
        return InputChannelListResponse(
            channels=channel_responses,
            total=total
        )
    
    def update_simple_channel(
        self,
        channel_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ):
        """
        Update InputChannel metadata
        
        All fields can be updated, even for protected channels.
        Protection only prevents deletion, not modification.
        
        Args:
            channel_id: Channel ID to update
            user_id: Owner user ID
            title: New title (allowed even for protected channels)
            description: New description
            default_author_id: New default author
            
        Returns:
            Updated InputChannelResponse
            
        Raises:
            NotFoundError: If channel not found
        """
        # Proceed with update (no restrictions)
        channel = self.channel_repo.update_simple(
            channel_id=channel_id,
            user_id=user_id,
            title=title,
            description=description,
            default_author_id=default_author_id
        )
        
        if not channel:
            raise NotFoundError("Input channel", channel_id)
        
        return InputChannelResponse.model_validate(channel)
    
    def delete_channel(self, channel_id: int, user_id: int) -> bool:
        """
        Delete InputChannel
        
        Protection: Cannot delete protected channels (is_protected=True).
        
        Args:
            channel_id: Channel ID to delete
            user_id: Owner user ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If channel not found
            ValueError: If trying to delete protected channel
        """
        # Get channel first to check if it's protected
        channel = self.channel_repo.get_channel_by_id(channel_id, user_id)
        if not channel:
            raise NotFoundError("Input channel", channel_id)
        
        # Protect system channels from deletion
        if channel.is_protected:
            raise ValueError(
                f"Cannot delete protected channel '{channel.title}'. "
                "This channel is required by the system."
            )
        
        success = self.channel_repo.delete(channel_id, user_id)
        return success
