"""
Timeline API endpoints for navigating photos by time intervals

This API provides structured access to photos organized by year, month, and day.
It supports search and filtering while maintaining efficient database access patterns.
"""
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, desc, or_

from core.dependencies import get_db
from models.photo import Photo
from models.author import Author

router = APIRouter()


@router.get("/years")
async def get_timeline_years(
    q: Optional[str] = Query(None, description="Search query"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    has_gps: Optional[bool] = Query(None, description="Filter by GPS availability"),
    db: Session = Depends(get_db)
):
    """Get all years that contain photos, with counts and pilot images"""
    try:
        # Base query - search in Photo table
        query = db.query(
            extract('year', Photo.taken_at).label('year'),
            func.count(Photo.hothash).label('photo_count'),
            func.count(func.distinct(extract('month', Photo.taken_at))).label('month_count'),
            func.min(Photo.taken_at).label('first_photo'),
            func.max(Photo.taken_at).label('last_photo'),
            # Get pilot photo (highest rated, or first chronologically)
            func.first_value(Photo.hothash).over(
                partition_by=extract('year', Photo.taken_at),
                order_by=[desc(Photo.rating), Photo.taken_at]
            ).label('pilot_photo_hothash')
        ).filter(Photo.taken_at.isnot(None))
        
        # Apply filters
        if q:
            query = query.filter(
                or_(
                    Photo.title.ilike(f"%{q}%"),
                    Photo.description.ilike(f"%{q}%")
                )
            )
        
        if author_id:
            query = query.filter(Photo.author_id == author_id)
            
        if has_gps is not None:
            if has_gps:
                query = query.filter(and_(Photo.latitude.isnot(None), Photo.longitude.isnot(None)))
            else:
                query = query.filter(or_(Photo.latitude.is_(None), Photo.longitude.is_(None)))
        
        # Group by year and order by year descending
        results = query.group_by(extract('year', Photo.taken_at)).order_by(desc('year')).all()
        
        # Format response
        years = []
        for result in results:
            # Get pilot photo details
            pilot_photo = db.query(Photo).filter(Photo.hothash == result.pilot_photo_hothash).first()
            
            year_data = {
                "year": int(result.year),
                "photo_count": result.photo_count,
                "month_count": result.month_count,
                "pilot_image": {
                    "id": pilot_photo.hothash,
                    "thumbnail_url": f"/api/photos/{pilot_photo.hothash}/hotpreview",
                    "title": pilot_photo.title or f"Photo {pilot_photo.hothash[:8]}"
                } if pilot_photo else None,
                "date_range": {
                    "first": result.first_photo.isoformat() if result.first_photo else None,
                    "last": result.last_photo.isoformat() if result.last_photo else None
                }
            }
            years.append(year_data)
        
        return {"years": years}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline years: {str(e)}")


@router.get("/years/{year}/months")
async def get_timeline_months(
    year: int,
    q: Optional[str] = Query(None, description="Search query"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    has_gps: Optional[bool] = Query(None, description="Filter by GPS availability"),
    db: Session = Depends(get_db)
):
    """Get all months in a year that contain photos"""
    try:
        # Month names in Norwegian
        month_names = {
            1: "Januar", 2: "Februar", 3: "Mars", 4: "April",
            5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
            9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }
        
        # Base query for specific year
        query = db.query(
            extract('month', Photo.taken_at).label('month'),
            func.count(Photo.hothash).label('photo_count'),
            func.count(func.distinct(extract('day', Photo.taken_at))).label('day_count'),
            func.min(Photo.taken_at).label('first_photo'),
            func.max(Photo.taken_at).label('last_photo'),
            # Get pilot photo
            func.first_value(Photo.hothash).over(
                partition_by=extract('month', Photo.taken_at),
                order_by=[desc(Photo.rating), Photo.taken_at]
            ).label('pilot_photo_hothash')
        ).filter(
            and_(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year
            )
        )
        
        # Apply filters (same as years endpoint)
        if q:
            query = query.filter(
                or_(
                    Photo.title.ilike(f"%{q}%"),
                    Photo.description.ilike(f"%{q}%")
                )
            )
        
        if author_id:
            query = query.filter(Photo.author_id == author_id)
            
        if has_gps is not None:
            if has_gps:
                query = query.filter(and_(Photo.latitude.isnot(None), Photo.longitude.isnot(None)))
            else:
                query = query.filter(or_(Photo.latitude.is_(None), Photo.longitude.is_(None)))
        
        # Group by month and order by month descending
        results = query.group_by(extract('month', Photo.taken_at)).order_by(desc('month')).all()
        
        # Format response
        months = []
        for result in results:
            pilot_photo = db.query(Photo).filter(Photo.hothash == result.pilot_photo_hothash).first()
            
            month_data = {
                "month": int(result.month),
                "name": month_names.get(int(result.month), f"Måned {result.month}"),
                "photo_count": result.photo_count,
                "day_count": result.day_count,
                "pilot_image": {
                    "id": pilot_photo.hothash,
                    "thumbnail_url": f"/api/photos/{pilot_photo.hothash}/hotpreview",
                    "title": pilot_photo.title or f"Photo {pilot_photo.hothash[:8]}"
                } if pilot_photo else None,
                "date_range": {
                    "first": result.first_photo.isoformat() if result.first_photo else None,
                    "last": result.last_photo.isoformat() if result.last_photo else None
                }
            }
            months.append(month_data)
        
        return {"year": year, "months": months}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline months: {str(e)}")


@router.get("/years/{year}/months/{month}/days")
async def get_timeline_days(
    year: int,
    month: int,
    q: Optional[str] = Query(None, description="Search query"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    has_gps: Optional[bool] = Query(None, description="Filter by GPS availability"),
    db: Session = Depends(get_db)
):
    """Get all days in a month that contain photos"""
    try:
        # Base query for specific year and month
        query = db.query(
            extract('day', Photo.taken_at).label('day'),
            func.count(Photo.hothash).label('photo_count'),
            func.min(Photo.taken_at).label('first_photo'),
            func.max(Photo.taken_at).label('last_photo'),
            # Get pilot photo
            func.first_value(Photo.hothash).over(
                partition_by=extract('day', Photo.taken_at),
                order_by=[desc(Photo.rating), Photo.taken_at]
            ).label('pilot_photo_hothash')
        ).filter(
            and_(
                Photo.taken_at.isnot(None),
                extract('year', Photo.taken_at) == year,
                extract('month', Photo.taken_at) == month
            )
        )
        
        # Apply filters
        if q:
            query = query.filter(
                or_(
                    Photo.title.ilike(f"%{q}%"),
                    Photo.description.ilike(f"%{q}%")
                )
            )
        
        if author_id:
            query = query.filter(Photo.author_id == author_id)
            
        if has_gps is not None:
            if has_gps:
                query = query.filter(and_(Photo.latitude.isnot(None), Photo.longitude.isnot(None)))
            else:
                query = query.filter(or_(Photo.latitude.is_(None), Photo.longitude.is_(None)))
        
        # Group by day and order by day descending
        results = query.group_by(extract('day', Photo.taken_at)).order_by(desc('day')).all()
        
        # Format response
        days = []
        for result in results:
            pilot_photo = db.query(Photo).filter(Photo.hothash == result.pilot_photo_hothash).first()
            
            day_data = {
                "day": int(result.day),
                "photo_count": result.photo_count,
                "pilot_image": {
                    "id": pilot_photo.hothash,
                    "thumbnail_url": f"/api/photos/{pilot_photo.hothash}/hotpreview",
                    "title": pilot_photo.title or f"Photo {pilot_photo.hothash[:8]}"
                } if pilot_photo else None,
                "time_range": {
                    "first": result.first_photo.isoformat() if result.first_photo else None,
                    "last": result.last_photo.isoformat() if result.last_photo else None
                }
            }
            days.append(day_data)
        
        return {"year": year, "month": month, "days": days}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline days: {str(e)}")


@router.get("/years/{year}/months/{month}/days/{day}/photos")
async def get_day_photos(
    year: int,
    month: int,
    day: int,
    offset: int = Query(0, ge=0, description="Number of photos to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of photos to return"),
    sort_by: str = Query("taken_at", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """Get all photos for a specific day"""
    try:
        # Create date filter for specific day
        target_date = date(year, month, day)
        next_date = date(year, month, day + 1) if day < 31 else date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        
        # Base query
        query = db.query(Photo).filter(
            and_(
                Photo.taken_at >= target_date,
                Photo.taken_at < next_date
            )
        )
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Photo, sort_by, Photo.taken_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        photos = query.offset(offset).limit(limit).all()
        
        # Format response
        photo_list = []
        for photo in photos:
            photo_data = {
                "id": photo.hothash,
                "title": photo.title or f"Photo {photo.hothash[:8]}",
                "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                "thumbnail_url": f"/api/photos/{photo.hothash}/hotpreview",
                "full_url": f"/api/photos/{photo.hothash}/view",
                "author": {
                    "id": photo.author.id,
                    "name": photo.author.name
                } if photo.author else None,
                "location": f"{photo.location_name}" if photo.location_name else None,
                "rating": photo.rating
            }
            photo_list.append(photo_data)
        
        return {
            "date": target_date.isoformat(),
            "total": total,
            "offset": offset,
            "limit": limit,
            "photos": photo_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get day photos: {str(e)}")