"""
Timeline Service - Business Logic Layer for Timeline operations
Orchestrates timeline aggregation with visibility filtering
"""
from typing import Optional, Literal
from fastapi import HTTPException, status

from src.repositories.timeline_repository import TimelineRepository
from src.schemas.timeline_schemas import TimelineResponse, TimelineBucket, TimelineMeta, DateRange


class TimelineService:
    """Service for timeline operations"""
    
    def __init__(self, timeline_repo: TimelineRepository):
        self.timeline_repo = timeline_repo
    
    def _validate_parameters(
        self,
        granularity: str,
        year: Optional[int],
        month: Optional[int],
        day: Optional[int]
    ):
        """Validate timeline request parameters."""
        # Validate granularity
        valid_granularities = ['year', 'month', 'day', 'hour']
        if granularity not in valid_granularities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid granularity. Must be one of: {', '.join(valid_granularities)}"
            )
        
        # Validate year
        if year is not None:
            if year < 1900 or year > 2100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid year. Must be between 1900 and 2100"
                )
        
        # Validate month
        if month is not None:
            if month < 1 or month > 12:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid month. Must be between 1 and 12"
                )
        
        # Validate day
        if day is not None:
            if day < 1 or day > 31:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid day. Must be between 1 and 31"
                )
        
        # Validate parameter requirements for each granularity
        if granularity == 'month' and year is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Year parameter required for month granularity"
            )
        
        if granularity == 'day':
            if year is None or month is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Year and month parameters required for day granularity"
                )
        
        if granularity == 'hour':
            if year is None or month is None or day is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Year, month, and day parameters required for hour granularity"
                )
    
    def _build_preview_url(self, hothash: str) -> str:
        """Build preview URL for a photo."""
        return f"/api/v1/photos/{hothash}/hotpreview"
    
    def _build_timeline_buckets(self, raw_data: list) -> list[TimelineBucket]:
        """Convert raw repository data to TimelineBucket schemas."""
        buckets = []
        
        for item in raw_data:
            bucket = TimelineBucket(
                year=item['year'],
                month=item.get('month'),
                day=item.get('day'),
                hour=item.get('hour'),
                count=item['count'],
                preview_hothash=item['preview_hothash'],
                preview_url=self._build_preview_url(item['preview_hothash']),
                date_range=DateRange(
                    first=item['first_date'],
                    last=item['last_date']
                )
            )
            buckets.append(bucket)
        
        return buckets
    
    def get_timeline(
        self,
        granularity: Literal["year", "month", "day", "hour"] = "year",
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> TimelineResponse:
        """
        Get timeline aggregation at specified granularity.
        
        Args:
            granularity: Time bucket size (year/month/day/hour)
            year: Filter to specific year
            month: Filter to specific month (requires year)
            day: Filter to specific day (requires year and month)
            user_id: User ID for visibility filtering (None for anonymous)
        
        Returns:
            TimelineResponse with buckets and metadata
        """
        # Validate parameters
        self._validate_parameters(granularity, year, month, day)
        
        # Get aggregation data based on granularity
        if granularity == 'year':
            raw_data = self.timeline_repo.get_year_aggregation(user_id=user_id)
        elif granularity == 'month':
            raw_data = self.timeline_repo.get_month_aggregation(
                year=year,
                user_id=user_id
            )
        elif granularity == 'day':
            raw_data = self.timeline_repo.get_day_aggregation(
                year=year,
                month=month,
                user_id=user_id
            )
        else:  # hour
            raw_data = self.timeline_repo.get_hour_aggregation(
                year=year,
                month=month,
                day=day,
                user_id=user_id
            )
        
        # Build timeline buckets
        buckets = self._build_timeline_buckets(raw_data)
        
        # Get total photo count
        total_photos = self.timeline_repo.count_total_photos(user_id=user_id)
        
        # Build metadata
        meta = TimelineMeta(
            granularity=granularity,
            total_photos=total_photos,
            year=year,
            month=month,
            day=day
        )
        
        # Set appropriate total count based on granularity
        if granularity == 'year':
            meta.total_years = len(buckets)
        elif granularity == 'month':
            meta.total_months = len(buckets)
        elif granularity == 'day':
            meta.total_days = len(buckets)
        else:  # hour
            meta.total_hours = len(buckets)
        
        return TimelineResponse(data=buckets, meta=meta)
