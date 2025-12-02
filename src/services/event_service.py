"""
Service layer for Event business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from src.repositories.event_repository import EventRepository
from src.models.event import Event
from src.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventTreeNode, 
    EventTreeResponse, EventWithPhotos
)
from src.core.exceptions import NotFoundError, ValidationError, AuthorizationError


class EventService:
    """Service for Event operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = EventRepository(db)
    
    def create_event(self, user_id: int, event_data: EventCreate) -> EventResponse:
        """Create a new event"""
        try:
            event = self.repo.create(
                user_id=user_id,
                name=event_data.name,
                description=event_data.description,
                parent_event_id=event_data.parent_event_id,
                start_date=event_data.start_date,
                end_date=event_data.end_date,
                location_name=event_data.location_name,
                gps_latitude=event_data.gps_latitude,
                gps_longitude=event_data.gps_longitude,
                sort_order=event_data.sort_order
            )
            return EventResponse.model_validate(event)
        except ValueError as e:
            raise ValidationError(str(e))
    
    def get_event(self, event_id: int, user_id: int) -> EventResponse:
        """Get event by ID"""
        event = self.repo.get_by_id(event_id, user_id)
        if not event:
            raise NotFoundError("Event", event_id)
        return EventResponse.model_validate(event)
    
    def list_events(self, user_id: int, parent_id: Optional[int] = None) -> List[EventWithPhotos]:
        """
        List events for user
        
        Args:
            user_id: User ID
            parent_id: Filter by parent (None = root events only)
        """
        events = self.repo.list_by_user(user_id, parent_id)
        
        # Add photo counts
        result = []
        for event in events:
            photo_count = self.repo.get_photo_count(event.id, include_descendants=False)
            event_dict = EventResponse.model_validate(event).model_dump()
            event_dict['photo_count'] = photo_count
            result.append(EventWithPhotos(**event_dict))
        
        return result
    
    def get_event_tree(self, user_id: int, root_event_id: Optional[int] = None) -> EventTreeResponse:
        """
        Get hierarchical event tree
        
        Args:
            user_id: User ID
            root_event_id: Start from specific event (None = all roots)
        """
        events = self.repo.get_event_tree(user_id, root_event_id)
        
        def build_tree_node(event: Event) -> EventTreeNode:
            """Recursively build EventTreeNode with photo counts"""
            photo_count = self.repo.get_photo_count(event.id, include_descendants=False)
            
            node_dict = EventResponse.model_validate(event).model_dump()
            node_dict['photo_count'] = photo_count
            node_dict['children'] = [build_tree_node(child) for child in event.children]
            
            return EventTreeNode(**node_dict)
        
        tree_nodes = [build_tree_node(event) for event in events]
        
        # Count total events recursively
        def count_events(node: EventTreeNode) -> int:
            return 1 + sum(count_events(child) for child in node.children)
        
        total_events = sum(count_events(node) for node in tree_nodes)
        
        return EventTreeResponse(events=tree_nodes, total_events=total_events)
    
    def update_event(self, event_id: int, user_id: int, event_data: EventUpdate) -> EventResponse:
        """Update event"""
        # Check event exists
        existing = self.repo.get_by_id(event_id, user_id)
        if not existing:
            raise NotFoundError("Event", event_id)
        
        # Build update dict (exclude None values)
        update_data = event_data.model_dump(exclude_unset=True)
        
        try:
            # Handle parent change via move_event
            if 'parent_event_id' in update_data:
                new_parent_id = update_data.pop('parent_event_id')
                self.repo.move_event(event_id, new_parent_id, user_id)
            
            # Update other fields
            if update_data:
                event = self.repo.update(event_id, user_id, **update_data)
            else:
                event = self.repo.get_by_id(event_id, user_id)
            
            return EventResponse.model_validate(event)
        except ValueError as e:
            raise ValidationError(str(e))
    
    def move_event(self, event_id: int, new_parent_id: Optional[int], user_id: int) -> EventResponse:
        """Move event to new parent"""
        try:
            event = self.repo.move_event(event_id, new_parent_id, user_id)
            return EventResponse.model_validate(event)
        except ValueError as e:
            if "not found" in str(e):
                raise NotFoundError("Event", event_id if "Event" in str(e) else new_parent_id)
            raise ValidationError(str(e))
    
    def delete_event(self, event_id: int, user_id: int) -> None:
        """Delete event"""
        if not self.repo.delete(event_id, user_id):
            raise NotFoundError("Event", event_id)
    
    # Photo operations
    
    def add_photos_to_event(self, event_id: int, hothashes: List[str], user_id: int) -> int:
        """
        Add photos to event
        
        Returns:
            Number of photos added
        """
        try:
            return self.repo.add_photos_to_event(event_id, hothashes, user_id)
        except ValueError as e:
            if "not found" in str(e).lower():
                raise NotFoundError("Event or Photos", event_id)
            raise ValidationError(str(e))
    
    def remove_photos_from_event(self, event_id: int, hothashes: List[str], user_id: int) -> int:
        """
        Remove photos from event
        
        Returns:
            Number of photos removed
        """
        try:
            return self.repo.remove_photos_from_event(event_id, hothashes, user_id)
        except ValueError as e:
            raise NotFoundError("Event", event_id)
    
    def get_event_photos(self, event_id: int, user_id: int, include_descendants: bool = False):
        """Get photos in event (optionally recursive)"""
        try:
            return self.repo.get_photos_in_event(event_id, user_id, include_descendants)
        except ValueError as e:
            raise NotFoundError("Event", event_id)
