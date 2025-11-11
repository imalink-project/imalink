"""
Timeline Repository - Data Access Layer for Timeline aggregations
Handles hierarchical time-based photo aggregation queries
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, extract
from datetime import datetime

from src.models import Photo


class TimelineRepository:
    """Repository for timeline aggregation operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _build_visibility_filter(self, user_id: Optional[int]):
        """
        Build visibility filter based on user authentication.
        
        Access rules:
        - Anonymous (user_id=None): Only public photos
        - Authenticated: Own photos + authenticated photos + public photos
        """
        if user_id is None:
            # Anonymous: only public
            return Photo.visibility == 'public'
        else:
            # Authenticated: own + authenticated + public
            return or_(
                Photo.user_id == user_id,
                Photo.visibility == 'authenticated',
                Photo.visibility == 'public'
            )
    
    def _get_preview_selection_case(self):
        """
        Build SQL CASE statement for preview photo selection.
        
        Priority:
        1. Highest rated (4-5 stars)
        2. Temporally centered photo
        3. First photo
        
        Returns a sort key where lower is better.
        """
        return case(
            # Priority 1: Rating 4-5 (sort by rating DESC, then by temporal position)
            (Photo.rating >= 4, 0),
            # Priority 2: No rating or rating < 4 (sort by temporal position)
            else_=1
        )
    
    def get_year_aggregation(
        self,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate photos by year.
        
        Returns list of dicts with:
        - year: int
        - count: int
        - preview_hothash: str
        - first_date: datetime
        - last_date: datetime
        """
        visibility_filter = self._build_visibility_filter(user_id)
        
        # Subquery to find preview photo for each year
        preview_subquery = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                Photo.hothash,
                Photo.rating,
                Photo.taken_at,
                func.row_number().over(
                    partition_by=extract('year', Photo.taken_at),
                    order_by=[
                        self._get_preview_selection_case(),
                        Photo.rating.desc().nullslast(),
                        Photo.taken_at
                    ]
                ).label('rn')
            )
            .filter(
                Photo.taken_at.isnot(None),
                visibility_filter
            )
            .subquery()
        )
        
        # Main aggregation query
        query = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                func.count(Photo.id).label('count'),
                func.min(Photo.taken_at).label('first_date'),
                func.max(Photo.taken_at).label('last_date')
            )
            .filter(
                Photo.taken_at.isnot(None),
                visibility_filter
            )
            .group_by(extract('year', Photo.taken_at))
            .order_by(extract('year', Photo.taken_at).desc())
        )
        
        results = query.all()
        
        # Get preview hashes
        year_previews = {}
        preview_results = (
            self.db.query(
                preview_subquery.c.year,
                preview_subquery.c.hothash
            )
            .filter(preview_subquery.c.rn == 1)
            .all()
        )
        
        for year, hothash in preview_results:
            year_previews[int(year)] = hothash
        
        # Combine results
        timeline = []
        for year, count, first_date, last_date in results:
            year_int = int(year)
            timeline.append({
                'year': year_int,
                'count': count,
                'preview_hothash': year_previews.get(year_int, ''),
                'first_date': first_date,
                'last_date': last_date
            })
        
        return timeline
    
    def get_month_aggregation(
        self,
        year: int,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate photos by month for a specific year.
        
        Returns list of dicts with:
        - year: int
        - month: int
        - count: int
        - preview_hothash: str
        - first_date: datetime
        - last_date: datetime
        """
        visibility_filter = self._build_visibility_filter(user_id)
        
        # Subquery for preview selection
        preview_subquery = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                extract('month', Photo.taken_at).label('month'),
                Photo.hothash,
                Photo.rating,
                Photo.taken_at,
                func.row_number().over(
                    partition_by=[
                        extract('year', Photo.taken_at),
                        extract('month', Photo.taken_at)
                    ],
                    order_by=[
                        self._get_preview_selection_case(),
                        Photo.rating.desc().nullslast(),
                        Photo.taken_at
                    ]
                ).label('rn')
            )
            .filter(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year,
                visibility_filter
            )
            .subquery()
        )
        
        # Main aggregation
        query = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                extract('month', Photo.taken_at).label('month'),
                func.count(Photo.id).label('count'),
                func.min(Photo.taken_at).label('first_date'),
                func.max(Photo.taken_at).label('last_date')
            )
            .filter(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year,
                visibility_filter
            )
            .group_by(
                extract('year', Photo.taken_at),
                extract('month', Photo.taken_at)
            )
            .order_by(extract('month', Photo.taken_at).desc())
        )
        
        results = query.all()
        
        # Get preview hashes
        month_previews = {}
        preview_results = (
            self.db.query(
                preview_subquery.c.month,
                preview_subquery.c.hothash
            )
            .filter(preview_subquery.c.rn == 1)
            .all()
        )
        
        for month, hothash in preview_results:
            month_previews[int(month)] = hothash
        
        # Combine results
        timeline = []
        for year_val, month, count, first_date, last_date in results:
            month_int = int(month)
            timeline.append({
                'year': int(year_val),
                'month': month_int,
                'count': count,
                'preview_hothash': month_previews.get(month_int, ''),
                'first_date': first_date,
                'last_date': last_date
            })
        
        return timeline
    
    def get_day_aggregation(
        self,
        year: int,
        month: int,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate photos by day for a specific month.
        
        Returns list of dicts with:
        - year: int
        - month: int
        - day: int
        - count: int
        - preview_hothash: str
        - first_date: datetime
        - last_date: datetime
        """
        visibility_filter = self._build_visibility_filter(user_id)
        
        # Subquery for preview selection
        preview_subquery = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                extract('month', Photo.taken_at).label('month'),
                extract('day', Photo.taken_at).label('day'),
                Photo.hothash,
                Photo.rating,
                Photo.taken_at,
                func.row_number().over(
                    partition_by=[
                        extract('year', Photo.taken_at),
                        extract('month', Photo.taken_at),
                        extract('day', Photo.taken_at)
                    ],
                    order_by=[
                        self._get_preview_selection_case(),
                        Photo.rating.desc().nullslast(),
                        Photo.taken_at
                    ]
                ).label('rn')
            )
            .filter(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year,
                extract('month', Photo.taken_at) == month,
                visibility_filter
            )
            .subquery()
        )
        
        # Main aggregation
        query = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                extract('month', Photo.taken_at).label('month'),
                extract('day', Photo.taken_at).label('day'),
                func.count(Photo.id).label('count'),
                func.min(Photo.taken_at).label('first_date'),
                func.max(Photo.taken_at).label('last_date')
            )
            .filter(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year,
                extract('month', Photo.taken_at) == month,
                visibility_filter
            )
            .group_by(
                extract('year', Photo.taken_at),
                extract('month', Photo.taken_at),
                extract('day', Photo.taken_at)
            )
            .order_by(extract('day', Photo.taken_at).desc())
        )
        
        results = query.all()
        
        # Get preview hashes
        day_previews = {}
        preview_results = (
            self.db.query(
                preview_subquery.c.day,
                preview_subquery.c.hothash
            )
            .filter(preview_subquery.c.rn == 1)
            .all()
        )
        
        for day, hothash in preview_results:
            day_previews[int(day)] = hothash
        
        # Combine results
        timeline = []
        for year_val, month_val, day, count, first_date, last_date in results:
            day_int = int(day)
            timeline.append({
                'year': int(year_val),
                'month': int(month_val),
                'day': day_int,
                'count': count,
                'preview_hothash': day_previews.get(day_int, ''),
                'first_date': first_date,
                'last_date': last_date
            })
        
        return timeline
    
    def get_hour_aggregation(
        self,
        year: int,
        month: int,
        day: int,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate photos by hour for a specific day.
        
        Returns list of dicts with:
        - year: int
        - month: int
        - day: int
        - hour: int
        - count: int
        - preview_hothash: str
        - first_date: datetime
        - last_date: datetime
        """
        visibility_filter = self._build_visibility_filter(user_id)
        
        # Subquery for preview selection
        preview_subquery = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                extract('month', Photo.taken_at).label('month'),
                extract('day', Photo.taken_at).label('day'),
                extract('hour', Photo.taken_at).label('hour'),
                Photo.hothash,
                Photo.rating,
                Photo.taken_at,
                func.row_number().over(
                    partition_by=[
                        extract('year', Photo.taken_at),
                        extract('month', Photo.taken_at),
                        extract('day', Photo.taken_at),
                        extract('hour', Photo.taken_at)
                    ],
                    order_by=[
                        self._get_preview_selection_case(),
                        Photo.rating.desc().nullslast(),
                        Photo.taken_at
                    ]
                ).label('rn')
            )
            .filter(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year,
                extract('month', Photo.taken_at) == month,
                extract('day', Photo.taken_at) == day,
                visibility_filter
            )
            .subquery()
        )
        
        # Main aggregation
        query = (
            self.db.query(
                extract('year', Photo.taken_at).label('year'),
                extract('month', Photo.taken_at).label('month'),
                extract('day', Photo.taken_at).label('day'),
                extract('hour', Photo.taken_at).label('hour'),
                func.count(Photo.id).label('count'),
                func.min(Photo.taken_at).label('first_date'),
                func.max(Photo.taken_at).label('last_date')
            )
            .filter(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year,
                extract('month', Photo.taken_at) == month,
                extract('day', Photo.taken_at) == day,
                visibility_filter
            )
            .group_by(
                extract('year', Photo.taken_at),
                extract('month', Photo.taken_at),
                extract('day', Photo.taken_at),
                extract('hour', Photo.taken_at)
            )
            .order_by(extract('hour', Photo.taken_at).desc())
        )
        
        results = query.all()
        
        # Get preview hashes
        hour_previews = {}
        preview_results = (
            self.db.query(
                preview_subquery.c.hour,
                preview_subquery.c.hothash
            )
            .filter(preview_subquery.c.rn == 1)
            .all()
        )
        
        for hour, hothash in preview_results:
            hour_previews[int(hour)] = hothash
        
        # Combine results
        timeline = []
        for year_val, month_val, day_val, hour, count, first_date, last_date in results:
            hour_int = int(hour)
            timeline.append({
                'year': int(year_val),
                'month': int(month_val),
                'day': int(day_val),
                'hour': hour_int,
                'count': count,
                'preview_hothash': hour_previews.get(hour_int, ''),
                'first_date': first_date,
                'last_date': last_date
            })
        
        return timeline
    
    def count_total_photos(self, user_id: Optional[int] = None) -> int:
        """Count total accessible photos."""
        visibility_filter = self._build_visibility_filter(user_id)
        
        return (
            self.db.query(func.count(Photo.id))
            .filter(
                Photo.taken_at.isnot(None),
                visibility_filter
            )
            .scalar()
        )
