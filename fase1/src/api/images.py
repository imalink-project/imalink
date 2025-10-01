"""
API endpoints for image operations
"""
import os
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Image

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
        # Compute RAW companion info dynamically
        from services.image_service import ImageProcessor
        raw_companion = ImageProcessor.find_raw_companion(img.file_path) if img.file_path else None
        
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
            "has_gps": img.gps_latitude is not None and img.gps_longitude is not None,
            "user_rotation": img.user_rotation or 0,  # Include rotation info
            "has_raw_companion": raw_companion is not None,
            "raw_file_format": Path(raw_companion).suffix.lower().lstrip('.') if raw_companion else None
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
    
    # Compute RAW companion info dynamically
    from services.image_service import ImageProcessor
    raw_companion = ImageProcessor.find_raw_companion(str(image.file_path)) if image.file_path else None
    raw_file_size = None
    raw_file_format = None
    
    if raw_companion and os.path.exists(raw_companion):
        raw_stat = os.stat(raw_companion)
        raw_file_size = raw_stat.st_size
        raw_file_format = Path(raw_companion).suffix.lower().lstrip('.')
    
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
        "import_source": image.import_source,
        "has_raw_companion": raw_companion is not None,
        "raw_file_path": raw_companion,
        "raw_file_size": raw_file_size,
        "raw_file_format": raw_file_format
    }


@router.get("/{image_id}/thumbnail")
async def get_thumbnail(image_id: int, db: Session = Depends(get_db)):
    """
    Get thumbnail image data with EXIF rotation applied retroactively
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image or image.thumbnail is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    try:
        # Modern thumbnails (created after EXIF fix) are already correctly oriented
        # Return thumbnail as-is without additional rotation
        return Response(
            content=image.thumbnail,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except Exception as e:
        print(f"Error processing thumbnail for image {image_id}: {e}")
        # Fallback to original thumbnail
        return Response(
            content=image.thumbnail,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=3600"}
        )


@router.get("/{image_id}/pool/{size}")
async def get_pool_image(
    image_id: int,
    size: str,
    db: Session = Depends(get_db)
):
    """
    Get optimized image version from pool
    
    Available sizes:
    - small: 400x400 max (for gallery grid view)
    - medium: 800x800 max (for standard viewing)
    - large: 1200x1200 max (for detailed viewing)
    
    Pool images have EXIF rotation baked in and no EXIF data.
    They are optimized JPEG files for fast web delivery.
    """
    from fastapi.responses import FileResponse
    from services.image_pool import ImagePoolService
    from config import config
    
    # Validate size parameter
    valid_sizes = ["small", "medium", "large"]
    if size not in valid_sizes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid size '{size}'. Valid sizes: {valid_sizes}"
        )
    
    # Get image from database
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if original file exists
    file_path_str = str(image.file_path) if image.file_path is not None else None
    if not file_path_str or not Path(file_path_str).exists():
        raise HTTPException(status_code=404, detail="Original image file not found")
    
    try:
        # Initialize pool service
        pool_service = ImagePoolService(config.IMAGE_POOL_DIRECTORY)
        
        # Get or create pool version
        pool_path = pool_service.get_or_create(
            original_path=Path(file_path_str),
            image_hash=str(image.image_hash),
            size=size,
            quality=config.POOL_QUALITY
        )
        
        # Return optimized image with aggressive caching
        return FileResponse(
            pool_path,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=31536000",  # 1 year cache
                "ETag": f'"{str(image.image_hash)}_{size}"',
                "X-Pool-Size": size,
                "X-Image-Hash": str(image.image_hash)
            }
        )
        
    except Exception as e:
        print(f"Error serving pool image {image_id}/{size}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate or serve pool image"
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
        try:
            from datetime import datetime
            after_date = datetime.fromisoformat(taken_after)
            query = query.filter(Image.taken_at >= after_date)
        except ValueError:
            pass
    if taken_before:
        try:
            from datetime import datetime
            before_date = datetime.fromisoformat(taken_before)
            query = query.filter(Image.taken_at <= before_date)
        except ValueError:
            pass
    
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


@router.post("/{image_id}/rotate")
async def rotate_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Rotate image thumbnail 90 degrees clockwise
    Updates ONLY thumbnail and user_rotation field - original file unchanged
    """
    try:
        from services.image_service import ImageProcessor
        
        # Check if image exists first
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail=f"Image with id {image_id} not found")
        
        # Rotate thumbnail and update user_rotation
        updated_image = ImageProcessor.rotate_thumbnail_in_db(db, image_id)
        
        if not updated_image:
            raise HTTPException(status_code=500, detail="Failed to rotate image - check server logs")
        
        return {
            "success": True,
            "image_id": image_id,
            "user_rotation": updated_image.user_rotation,
            "message": f"Image rotated to {updated_image.user_rotation * 90} degrees"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in rotate_image: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")