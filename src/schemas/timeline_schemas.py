"""
Timeline API schemas for hierarchical time-based photo navigation.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class DateRange(BaseModel):
    """Date range for a timeline bucket."""
    first: datetime = Field(..., description="Timestamp of earliest photo in bucket")
    last: datetime = Field(..., description="Timestamp of latest photo in bucket")


class TimelineBucket(BaseModel):
    """A time bucket with aggregated photo data."""
    year: int = Field(..., description="Year (1900-2100)")
    month: Optional[int] = Field(None, description="Month (1-12), present for month/day/hour granularity")
    day: Optional[int] = Field(None, description="Day of month (1-31), present for day/hour granularity")
    hour: Optional[int] = Field(None, description="Hour (0-23), present for hour granularity")
    count: int = Field(..., description="Number of photos in this bucket")
    preview_hothash: str = Field(..., description="HotHash of representative photo")
    preview_url: str = Field(..., description="URL to hotpreview of representative photo")
    date_range: DateRange = Field(..., description="Date range of photos in bucket")
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2024,
                "month": 6,
                "count": 45,
                "preview_hothash": "abc123def456...",
                "preview_url": "/api/v1/photos/abc123def456.../hotpreview",
                "date_range": {
                    "first": "2024-06-01T08:00:00Z",
                    "last": "2024-06-30T22:45:00Z"
                }
            }
        }


class TimelineMeta(BaseModel):
    """Metadata for timeline response."""
    total_years: Optional[int] = Field(None, description="Total years with photos")
    total_months: Optional[int] = Field(None, description="Total months with photos (when filtered by year)")
    total_days: Optional[int] = Field(None, description="Total days with photos (when filtered by month)")
    total_hours: Optional[int] = Field(None, description="Total hours with photos (when filtered by day)")
    total_photos: int = Field(..., description="Total photos in current view")
    granularity: Literal["year", "month", "day", "hour"] = Field(..., description="Time bucket granularity")
    year: Optional[int] = Field(None, description="Filtered year")
    month: Optional[int] = Field(None, description="Filtered month")
    day: Optional[int] = Field(None, description="Filtered day")


class TimelineResponse(BaseModel):
    """Timeline API response."""
    data: list[TimelineBucket] = Field(..., description="Array of timeline buckets")
    meta: TimelineMeta = Field(..., description="Timeline metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "year": 2024,
                        "count": 1247,
                        "preview_hothash": "abc123...",
                        "preview_url": "/api/v1/photos/abc123.../hotpreview",
                        "date_range": {
                            "first": "2024-01-05T08:23:12Z",
                            "last": "2024-12-28T19:45:00Z"
                        }
                    }
                ],
                "meta": {
                    "total_years": 5,
                    "total_photos": 4521,
                    "granularity": "year"
                }
            }
        }
