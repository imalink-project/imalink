"""
Date and time utilities
"""
from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Get current UTC time"""
    return datetime.now(timezone.utc)


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """Format datetime as string"""
    if dt is None:
        return None
    return dt.strftime(format_str)


def parse_datetime(date_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse datetime string"""
    try:
        return datetime.strptime(date_string, format_str)
    except ValueError:
        return None