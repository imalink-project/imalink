"""
Timeline API endpoints for hierarchical time-based photo navigation.

Provides year/month/day/hour aggregation with visibility-aware filtering
and representative preview selection.
"""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query
import logging

from src.services.timeline_service import TimelineService
from src.repositories.timeline_repository import TimelineRepository
from src.schemas.timeline_schemas import TimelineResponse
from src.database.connection import get_db
from src.api.dependencies import get_optional_current_user
from src.models.user import User
from sqlalchemy.orm import Session


router = APIRouter()
logger = logging.getLogger(__name__)


def get_timeline_service(db: Session = Depends(get_db)) -> TimelineService:
    """Dependency to get timeline service."""
    timeline_repo = TimelineRepository(db)
    return TimelineService(timeline_repo)


@router.get("/", response_model=TimelineResponse)
async def get_timeline(
    granularity: Literal["year", "month", "day", "hour"] = Query(
        "year",
        description="Time bucket granularity (year/month/day/hour)"
    ),
    year: Optional[int] = Query(
        None,
        ge=1900,
        le=2100,
        description="Filter to specific year (required for month/day/hour)"
    ),
    month: Optional[int] = Query(
        None,
        ge=1,
        le=12,
        description="Filter to specific month (required for day/hour, requires year)"
    ),
    day: Optional[int] = Query(
        None,
        ge=1,
        le=31,
        description="Filter to specific day (required for hour, requires year and month)"
    ),
    current_user: Optional[User] = Depends(get_optional_current_user),
    timeline_service: TimelineService = Depends(get_timeline_service)
) -> TimelineResponse:
    """
    Get hierarchical timeline aggregation of photos.
    
    Navigate photos by time with automatic aggregation into buckets.
    Each bucket includes photo count, representative preview, and date range.
    
    **Granularity Levels:**
    - `year`: Aggregate by year (no parameters required)
    - `month`: Aggregate by month within a year (requires `year`)
    - `day`: Aggregate by day within a month (requires `year` and `month`)
    - `hour`: Aggregate by hour within a day (requires `year`, `month`, and `day`)
    
    **Preview Selection:**
    1. Highest rated photo (rating 4-5)
    2. Temporally centered photo (middle of period)
    3. First photo in period
    
    **Visibility Filtering:**
    - Anonymous users: Only `public` photos
    - Authenticated users: Own photos + `authenticated` + `public` photos
    - Empty buckets (no accessible photos) are excluded
    
    **Examples:**
    - `GET /timeline?granularity=year` - All years with photos
    - `GET /timeline?granularity=month&year=2024` - Months in 2024
    - `GET /timeline?granularity=day&year=2024&month=6` - Days in June 2024
    - `GET /timeline?granularity=hour&year=2024&month=6&day=15` - Hours on June 15, 2024
    
    Returns:
        TimelineResponse with array of time buckets and metadata
    """
    user_id = current_user.id if current_user else None
    
    logger.info(
        f"Timeline request: granularity={granularity}, year={year}, month={month}, "
        f"day={day}, user_id={user_id}"
    )
    
    timeline = timeline_service.get_timeline(
        granularity=granularity,
        year=year,
        month=month,
        day=day,
        user_id=user_id
    )
    
    logger.info(
        f"Timeline response: {len(timeline.data)} buckets, "
        f"{timeline.meta.total_photos} total photos"
    )
    
    return timeline
