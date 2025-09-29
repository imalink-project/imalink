"""
API endpoints for image operations
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import Image

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_images(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get a list of images with basic metadata
    """
    images = (
        db.query(Image)
        .order_by(Image.taken_at.desc(), Image.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Convert to simple dict format
    result = []
    for img in images:
        result.append({
            "id": img.id,
            "hash": img.image_hash,
            "filename": img.original_filename,
            "taken_at": img.taken_at.isoformat() if img.taken_at is not None else None,
            "created_at": img.created_at.isoformat() if img.created_at is not None else None,
            "width": img.width,
            "height": img.height,
            "file_size": img.file_size,
            "format": img.file_format,
            "has_gps": img.gps_latitude is not None and img.gps_longitude is not None
        })
    
    return result


@router.get("/{image_id}")
async def get_image_details(image_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific image
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {
        "id": image.id,
        "hash": image.image_hash,
        "filename": image.original_filename,
        "file_path": image.file_path,
        "file_size": image.file_size,
        "format": image.file_format,
        "taken_at": image.taken_at.isoformat() if image.taken_at is not None else None,
        "created_at": image.created_at.isoformat() if image.created_at is not None else None,
        "width": image.width,
        "height": image.height,
        "gps_latitude": image.gps_latitude,
        "gps_longitude": image.gps_longitude,
        "title": image.title,
        "description": image.description,
        "tags": image.tags,
        "rating": image.rating,
        "import_source": image.import_source
    }


@router.get("/{image_id}/thumbnail")
async def get_thumbnail(image_id: int, db: Session = Depends(get_db)):
    """
    Get thumbnail image data
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image or image.thumbnail is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return Response(
        content=image.thumbnail,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/search")
async def search_images(
    q: Optional[str] = None,
    taken_after: Optional[str] = None,
    taken_before: Optional[str] = None,
    has_gps: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Search images with various filters
    """
    query = db.query(Image)
    
    # Text search in filename
    if q:
        query = query.filter(Image.original_filename.contains(q))
    
    # Date range filters
    if taken_after:
        query = query.filter(Image.taken_at >= taken_after)
    if taken_before:
        query = query.filter(Image.taken_at <= taken_before)
    
    # GPS filter
    if has_gps is not None:
        if has_gps:
            query = query.filter(
                Image.gps_latitude.isnot(None),
                Image.gps_longitude.isnot(None)
            )
        else:
            query = query.filter(
                (Image.gps_latitude.is_(None)) |
                (Image.gps_longitude.is_(None))
            )
    
    # Apply pagination and ordering
    images = (
        query
        .order_by(Image.taken_at.desc(), Image.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Convert to response format
    result = []
    for img in images:
        result.append({
            "id": img.id,
            "hash": img.image_hash,
            "filename": img.original_filename,
            "taken_at": img.taken_at.isoformat() if img.taken_at is not None else None,
            "width": img.width,
            "height": img.height,
            "has_gps": img.gps_latitude is not None and img.gps_longitude is not None
        })
    
    return {
        "images": result,
        "total": len(result),
        "offset": offset,
        "limit": limit
    }