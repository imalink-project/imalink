"""
Event model for hierarchical photo organization

Events represent contextual groupings of photos (trips, occasions, projects).
Unlike Collections (curated, many-to-many), Events are hierarchical one-to-many.
Each photo belongs to at most ONE event.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin


class Event(Base, TimestampMixin):
    """
    Hierarchical event for organizing photos by context
    
    Examples:
    - "London Trip 2025" (parent)
      - "Tower of London" (child)
      - "British Museum" (child)
    
    Each photo belongs to at most ONE event (one-to-many).
    Collections and Tags provide many-to-many functionality.
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_event_id = Column(Integer, ForeignKey('events.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Core fields
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Optional temporal bounds
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Optional location
    location_name = Column(String(200), nullable=True)
    gps_latitude = Column(Numeric(precision=10, scale=8), nullable=True)
    gps_longitude = Column(Numeric(precision=11, scale=8), nullable=True)
    
    # Ordering within siblings
    sort_order = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    modified_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="events")
    parent = relationship("Event", remote_side=[id], backref="children")
    photos = relationship("Photo", back_populates="event")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('parent_event_id != id', name='valid_parent_event'),
    )
    
    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', user_id={self.user_id}, parent_id={self.parent_event_id})>"
    
    @property
    def depth(self) -> int:
        """Calculate depth in tree (0 = root)"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth
    
    @property
    def path(self) -> List[str]:
        """Get full path from root to this event"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return path
    
    def is_ancestor_of(self, other: 'Event') -> bool:
        """Check if this event is an ancestor of another"""
        current = other.parent
        while current:
            if current.id == self.id:
                return True
            current = current.parent
        return False
