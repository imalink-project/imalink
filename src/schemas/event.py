"""
Pydantic schemas for Event API requests and responses
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class EventBase(BaseModel):
    """Base schema with common event fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Event name")
    description: Optional[str] = Field(None, max_length=2000, description="Event description")
    parent_event_id: Optional[int] = Field(None, description="Parent event ID for hierarchy")
    
    # Temporal context (optional - events may span time or be instant)
    start_date: Optional[datetime] = Field(None, description="Event start date/time")
    end_date: Optional[datetime] = Field(None, description="Event end date/time")
    
    # Spatial context (optional - events may have location)
    location_name: Optional[str] = Field(None, max_length=200, description="Location name (e.g., 'Tower of London')")
    gps_latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    
    # UI ordering
    sort_order: int = Field(default=0, description="Sort order among siblings (lower = earlier)")


class EventCreate(EventBase):
    """Schema for creating a new event"""
    pass


class EventUpdate(BaseModel):
    """Schema for updating an event (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    parent_event_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location_name: Optional[str] = Field(None, max_length=200)
    gps_latitude: Optional[float] = Field(None, ge=-90, le=90)
    gps_longitude: Optional[float] = Field(None, ge=-180, le=180)
    sort_order: Optional[int] = None


class EventResponse(EventBase):
    """Schema for event responses (includes database fields)"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EventWithPhotos(EventResponse):
    """Event with photo count"""
    photo_count: int = Field(..., description="Number of photos directly in this event")


class EventTreeNode(EventResponse):
    """Event node in hierarchy tree with children"""
    children: List['EventTreeNode'] = Field(default_factory=list, description="Child events")
    photo_count: int = Field(0, description="Number of photos directly in this event (not recursive)")
    
    model_config = ConfigDict(from_attributes=True)


class EventTreeResponse(BaseModel):
    """Response containing event tree structure"""
    events: List[EventTreeNode] = Field(..., description="Root events with nested children")
    total_events: int = Field(..., description="Total number of events in tree")


class EventMoveRequest(BaseModel):
    """Request to move event to new parent"""
    new_parent_id: Optional[int] = Field(None, description="New parent event ID (null for root level)")


# Allow forward references for recursive EventTreeNode
EventTreeNode.model_rebuild()
