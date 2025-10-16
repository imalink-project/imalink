"""
Common model mixins for shared functionality
"""
from datetime import datetime
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """Add created_at and updated_at timestamps to models"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)