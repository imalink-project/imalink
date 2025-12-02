"""
Repository for Event database operations
"""
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from src.models.event import Event
from src.models.photo import Photo


class EventRepository:
    """Repository for Event operations with hierarchy support"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_id: int, **kwargs) -> Event:
        """Create a new event"""
        # Ensure user_id is set
        kwargs['user_id'] = user_id
        
        # Validate parent event exists and belongs to same user
        if 'parent_event_id' in kwargs and kwargs['parent_event_id']:
            parent = self.get_by_id(kwargs['parent_event_id'])
            if not parent:
                raise ValueError(f"Parent event {kwargs['parent_event_id']} not found")
            if parent.user_id != user_id:
                raise ValueError("Cannot set parent from different user")
        
        event = Event(**kwargs)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def get_by_id(self, event_id: int, user_id: Optional[int] = None) -> Optional[Event]:
        """Get event by ID, optionally filtered by user"""
        query = self.db.query(Event).filter(Event.id == event_id)
        if user_id is not None:
            query = query.filter(Event.user_id == user_id)
        return query.first()
    
    def list_by_user(self, user_id: int, parent_id: Optional[int] = None) -> List[Event]:
        """
        List events for a user
        
        Args:
            user_id: User ID
            parent_id: Filter by parent event ID (None = root events only)
        """
        query = self.db.query(Event).filter(Event.user_id == user_id)
        
        if parent_id is None:
            # Root events only
            query = query.filter(Event.parent_event_id.is_(None))
        else:
            # Children of specific parent
            query = query.filter(Event.parent_event_id == parent_id)
        
        return query.order_by(Event.sort_order, Event.name).all()
    
    def get_event_tree(self, user_id: int, root_event_id: Optional[int] = None) -> List[Event]:
        """
        Get hierarchical event tree using recursive SQL
        
        Args:
            user_id: User ID
            root_event_id: Start from specific event (None = all roots)
        
        Returns:
            List of Event objects with children populated
        """
        # Build recursive CTE query
        if root_event_id is None:
            # Get all root events and their descendants
            cte_query = text("""
                WITH RECURSIVE event_tree AS (
                    -- Base case: root events
                    SELECT id, user_id, parent_event_id, name, description,
                           start_date, end_date, location_name, 
                           gps_latitude, gps_longitude, sort_order,
                           created_at, updated_at,
                           0 as depth
                    FROM events
                    WHERE user_id = :user_id AND parent_event_id IS NULL
                    
                    UNION ALL
                    
                    -- Recursive case: children
                    SELECT e.id, e.user_id, e.parent_event_id, e.name, e.description,
                           e.start_date, e.end_date, e.location_name,
                           e.gps_latitude, e.gps_longitude, e.sort_order,
                           e.created_at, e.updated_at,
                           et.depth + 1
                    FROM events e
                    INNER JOIN event_tree et ON e.parent_event_id = et.id
                )
                SELECT * FROM event_tree ORDER BY depth, sort_order, name
            """)
            params = {"user_id": user_id}
        else:
            # Get specific event and its descendants
            cte_query = text("""
                WITH RECURSIVE event_tree AS (
                    -- Base case: specified event
                    SELECT id, user_id, parent_event_id, name, description,
                           start_date, end_date, location_name,
                           gps_latitude, gps_longitude, sort_order,
                           created_at, updated_at,
                           0 as depth
                    FROM events
                    WHERE id = :root_id AND user_id = :user_id
                    
                    UNION ALL
                    
                    -- Recursive case: children
                    SELECT e.id, e.user_id, e.parent_event_id, e.name, e.description,
                           e.start_date, e.end_date, e.location_name,
                           e.gps_latitude, e.gps_longitude, e.sort_order,
                           e.created_at, e.updated_at,
                           et.depth + 1
                    FROM events e
                    INNER JOIN event_tree et ON e.parent_event_id = et.id
                )
                SELECT * FROM event_tree ORDER BY depth, sort_order, name
            """)
            params = {"user_id": user_id, "root_id": root_event_id}
        
        # Execute query and convert to Event objects
        result = self.db.execute(cte_query, params)
        rows = result.fetchall()
        
        # Convert rows to Event objects and build tree structure
        events_by_id = {}
        root_events = []
        
        for row in rows:
            event = Event(
                id=row.id,
                user_id=row.user_id,
                parent_event_id=row.parent_event_id,
                name=row.name,
                description=row.description,
                start_date=row.start_date,
                end_date=row.end_date,
                location_name=row.location_name,
                gps_latitude=row.gps_latitude,
                gps_longitude=row.gps_longitude,
                sort_order=row.sort_order,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            # Initialize children list
            event.children = []
            events_by_id[event.id] = event
            
            if event.parent_event_id is None:
                root_events.append(event)
        
        # Build parent-child relationships
        for event in events_by_id.values():
            if event.parent_event_id and event.parent_event_id in events_by_id:
                parent = events_by_id[event.parent_event_id]
                parent.children.append(event)
        
        return root_events if root_event_id is None else [events_by_id.get(root_event_id)] if root_event_id in events_by_id else []
    
    def get_descendant_ids(self, event_id: int, user_id: int) -> List[int]:
        """
        Get all descendant event IDs (recursive)
        
        Args:
            event_id: Root event ID
            user_id: User ID for security
        
        Returns:
            List of event IDs including root
        """
        cte_query = text("""
            WITH RECURSIVE event_descendants AS (
                -- Base case: specified event
                SELECT id, parent_event_id
                FROM events
                WHERE id = :event_id AND user_id = :user_id
                
                UNION ALL
                
                -- Recursive case: children
                SELECT e.id, e.parent_event_id
                FROM events e
                INNER JOIN event_descendants ed ON e.parent_event_id = ed.id
            )
            SELECT id FROM event_descendants
        """)
        
        result = self.db.execute(cte_query, {"event_id": event_id, "user_id": user_id})
        return [row.id for row in result.fetchall()]
    
    def move_event(self, event_id: int, new_parent_id: Optional[int], user_id: int) -> Event:
        """
        Move event to new parent
        
        Args:
            event_id: Event to move
            new_parent_id: New parent (None = root level)
            user_id: User ID for security
        
        Raises:
            ValueError: If move would create cycle or cross user boundaries
        """
        event = self.get_by_id(event_id, user_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        # Prevent moving to itself
        if new_parent_id == event_id:
            raise ValueError("Cannot move event to itself")
        
        # If moving to new parent, validate
        if new_parent_id is not None:
            new_parent = self.get_by_id(new_parent_id, user_id)
            if not new_parent:
                raise ValueError(f"Parent event {new_parent_id} not found")
            
            # Prevent creating cycle (new parent can't be descendant)
            descendant_ids = self.get_descendant_ids(event_id, user_id)
            if new_parent_id in descendant_ids:
                raise ValueError("Cannot move event to its own descendant (would create cycle)")
        
        # Update parent
        event.parent_event_id = new_parent_id
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def update(self, event_id: int, user_id: int, **kwargs) -> Optional[Event]:
        """Update event fields"""
        event = self.get_by_id(event_id, user_id)
        if not event:
            return None
        
        # Handle parent_event_id change separately (via move_event)
        if 'parent_event_id' in kwargs:
            kwargs.pop('parent_event_id')
        
        # Update allowed fields
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def delete(self, event_id: int, user_id: int) -> bool:
        """
        Delete event
        
        Child events will have parent_event_id set to NULL (via CASCADE SET NULL)
        Photos remain but lose event association (via CASCADE DELETE on photo_events)
        """
        event = self.get_by_id(event_id, user_id)
        if not event:
            return False
        
        self.db.delete(event)
        self.db.commit()
        return True
    
    # Photo-Event associations (one-to-many: photo.event_id)
    
    def get_photos_in_event(self, event_id: int, user_id: int, include_descendants: bool = False) -> List[Photo]:
        """
        Get photos in event
        
        Args:
            event_id: Event ID
            user_id: User ID for security
            include_descendants: Include photos from child events
        """
        event = self.get_by_id(event_id, user_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        if include_descendants:
            # Get all descendant event IDs
            event_ids = self.get_descendant_ids(event_id, user_id)
        else:
            event_ids = [event_id]
        
        # Query photos directly via event_id column
        photos = self.db.query(Photo).filter(
            Photo.event_id.in_(event_ids),
            Photo.user_id == user_id
        ).all()
        
        return photos
    
    def get_photo_count(self, event_id: int, include_descendants: bool = False) -> int:
        """Get number of photos in event (optionally recursive)"""
        if include_descendants:
            # Recursive count using CTE
            cte_query = text("""
                WITH RECURSIVE event_tree AS (
                    SELECT id FROM events WHERE id = :event_id
                    UNION ALL
                    SELECT e.id FROM events e
                    INNER JOIN event_tree et ON e.parent_event_id = et.id
                )
                SELECT COUNT(p.id)
                FROM photos p
                INNER JOIN event_tree et ON p.event_id = et.id
            """)
            result = self.db.execute(cte_query, {"event_id": event_id})
            return result.scalar() or 0
        else:
            # Direct count
            count = self.db.query(Photo).filter(Photo.event_id == event_id).count()
            return count
