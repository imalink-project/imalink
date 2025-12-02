"""
Event API endpoints - Hierarchical photo organization
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.dependencies import get_db, get_current_user
from src.models.user import User
from src.services.event_service import EventService
from src.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventTreeResponse,
    EventWithPhotos, EventMoveRequest
)
from src.schemas.photo_schemas import PhotoResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=201)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new event
    
    Events organize photos by hierarchical context (e.g., "London 2025" > "Tower of London").
    
    - **name**: Event name (required)
    - **description**: Optional description
    - **parent_event_id**: Parent event for hierarchy (null = root level)
    - **start_date/end_date**: Optional temporal context
    - **location_name/gps_***: Optional spatial context
    - **sort_order**: Order among siblings (default 0)
    """
    service = EventService(db)
    return service.create_event(current_user.id, event_data)


@router.get("/", response_model=List[EventWithPhotos])
def list_events(
    parent_id: Optional[int] = Query(None, description="Filter by parent event ID (null = root events)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List events for current user
    
    By default, returns root events only. Use parent_id to list children of specific event.
    Each event includes photo count (direct photos, not recursive).
    """
    service = EventService(db)
    return service.list_events(current_user.id, parent_id)


@router.get("/tree", response_model=EventTreeResponse)
def get_event_tree(
    root_id: Optional[int] = Query(None, description="Root event ID (null = all roots)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get hierarchical event tree
    
    Returns complete tree structure with nested children.
    Use root_id to get subtree starting from specific event.
    
    **Performance**: Uses recursive SQL for efficiency.
    """
    service = EventService(db)
    return service.get_event_tree(current_user.id, root_id)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get event by ID"""
    service = EventService(db)
    return service.get_event(event_id, current_user.id)


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update event
    
    All fields optional. Only provided fields will be updated.
    To move event, update parent_event_id (validated to prevent cycles).
    """
    service = EventService(db)
    return service.update_event(event_id, current_user.id, event_data)


@router.post("/{event_id}/move", response_model=EventResponse)
def move_event(
    event_id: int,
    move_request: EventMoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Move event to new parent
    
    Validates that move won't create cycle (can't move to own descendant).
    Use new_parent_id=null to move to root level.
    """
    service = EventService(db)
    return service.move_event(event_id, move_request.new_parent_id, current_user.id)


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete event
    
    Child events will become root events (parent_event_id set to NULL).
    Photos remain but lose association with this event.
    """
    service = EventService(db)
    service.delete_event(event_id, current_user.id)


# Photo-Event associations

@router.get("/{event_id}/photos", response_model=List[PhotoResponse])
def get_event_photos(
    event_id: int,
    include_descendants: bool = Query(False, description="Include photos from child events"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get photos in event
    
    - **include_descendants=false**: Only direct photos in this event
    - **include_descendants=true**: Photos in this event + all child events (recursive)
    
    Note: To set/change a photo's event, use PUT /photos/{hothash}/event
    """
    service = EventService(db)
    photos = service.get_event_photos(event_id, current_user.id, include_descendants)
    return [PhotoResponse.model_validate(photo) for photo in photos]
