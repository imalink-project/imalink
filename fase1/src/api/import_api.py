"""
API endpoints for importing images
"""
import os
from typing import List
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.models import Image, ImportSession
from services.image_service import create_image_record, ImageProcessor

router = APIRouter()


class ImportRequest(BaseModel):
    source_path: str
    source_description: str = "Manual import"


class ImportStatus(BaseModel):
    session_id: int
    status: str
    total_files_found: int
    images_imported: int
    duplicates_skipped: int
    raw_files_skipped: int
    single_raw_skipped: int
    errors_count: int
    progress_percentage: float


@router.post("/start")
async def start_import(
    import_request: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start an import process for a directory
    """
    source_path = Path(import_request.source_path)
    
    if not source_path.exists():
        raise HTTPException(status_code=400, detail="Source path does not exist")
    
    if not source_path.is_dir():
        raise HTTPException(status_code=400, detail="Source path must be a directory")
    
    # Create import session
    import_session = ImportSession(
        source_path=str(source_path),
        source_description=import_request.source_description,
        status="in_progress"
    )
    
    db.add(import_session)
    db.commit()
    db.refresh(import_session)
    
    # Start background import
    background_tasks.add_task(
        import_directory_background,
        import_session.id,
        str(source_path),
        import_request.source_description
    )
    
    return {
        "message": "Import started",
        "session_id": import_session.id,
        "status": "in_progress"
    }


@router.get("/status/{session_id}")
async def get_import_status(session_id: int, db: Session = Depends(get_db)):
    """
    Get status of an import session
    """
    session = db.query(ImportSession).filter(ImportSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Import session not found")
    
    progress = 0.0
    if session.total_files_found > 0:
        processed = session.images_imported + session.duplicates_skipped + session.raw_files_skipped + session.single_raw_skipped + session.errors_count
        progress = (processed / session.total_files_found) * 100
    
    return ImportStatus(
        session_id=session.id,
        status=session.status,
        total_files_found=session.total_files_found,
        images_imported=session.images_imported,
        duplicates_skipped=session.duplicates_skipped,
        raw_files_skipped=session.raw_files_skipped or 0,
        single_raw_skipped=session.single_raw_skipped or 0,
        errors_count=session.errors_count,
        progress_percentage=progress
    )


@router.get("/sessions")
async def list_import_sessions(db: Session = Depends(get_db)):
    """
    List all import sessions
    """
    sessions = (
        db.query(ImportSession)
        .order_by(ImportSession.started_at.desc())
        .limit(50)
        .all()
    )
    
    result = []
    for session in sessions:
        result.append({
            "id": session.id,
            "started_at": session.started_at.isoformat() if session.started_at is not None else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at is not None else None,
            "status": session.status,
            "source_path": session.source_path,
            "source_description": session.source_description,
            "total_files_found": session.total_files_found,
            "images_imported": session.images_imported,
            "duplicates_skipped": session.duplicates_skipped,
            "raw_files_skipped": session.raw_files_skipped or 0,
            "single_raw_skipped": session.single_raw_skipped or 0,
            "errors_count": session.errors_count
        })
    
    return result


def import_directory_background(session_id: int, source_path: str, source_description: str):
    """
    Background task to import all images from a directory
    """
    from database.connection import get_db_sync
    
    db = get_db_sync()
    
    try:
        # Get the import session
        session = db.query(ImportSession).filter(ImportSession.id == session_id).first()
        if not session:
            return
        
        source_path_obj = Path(source_path)
        
        # Find all image files (including RAW formats)
        image_files = []
        for ext in ImageProcessor.ALL_FORMATS:
            pattern = f"**/*{ext}"
            image_files.extend(source_path_obj.rglob(pattern))
            # Also search uppercase extensions
            pattern = f"**/*{ext.upper()}"
            image_files.extend(source_path_obj.rglob(pattern))
        
        # WORKAROUND: Remove duplicates caused by case-insensitive filesystems
        # On Windows, a file named "image.jpg" will be found by both "**/*.jpg" 
        # and "**/*.JPG" patterns, causing each file to be counted twice.
        # This deduplication ensures accurate file counts during import.
        image_files = list(set(image_files))
        
        # Update session with total files found
        session.total_files_found = len(image_files)
        db.commit()
        
        # Process each file with proper categorization
        imported_count = 0
        duplicates_count = 0
        raw_files_count = 0        # RAW files with JPEG companions
        single_raw_count = 0       # Single RAW files (no JPEG companion)
        errors_count = 0
        errors_log = []
        
        for file_path in image_files:
            try:
                # Check if this is a RAW file
                if ImageProcessor.is_raw_format(str(file_path)):
                    jpeg_companion = ImageProcessor.find_jpeg_companion(str(file_path))
                    if jpeg_companion:
                        raw_files_count += 1
                        print(f"Skipping RAW file {file_path} - JPEG companion found: {jpeg_companion}")
                        continue
                    else:
                        single_raw_count += 1
                        print(f"Skipping single RAW file {file_path} - no JPEG companion (will add RAW processing later)")
                        continue
                
                # Try to import the file
                image_record = create_image_record(
                    str(file_path),
                    source_description,
                    db
                )
                
                if image_record is None:
                    # This is a true duplicate (same hash)
                    duplicates_count += 1
                else:
                    db.add(image_record)
                    db.commit()
                    imported_count += 1
                    
                    # Generate pool versions in background (non-blocking)
                    try:
                        from services.image_pool import ImagePoolService
                        from config import config
                        
                        pool_service = ImagePoolService(config.IMAGE_POOL_DIRECTORY)
                        
                        # Generate all pool sizes optimized
                        created_paths = pool_service.create_all_sizes_optimized(
                            original_path=file_path,
                            image_hash=str(image_record.image_hash),
                            quality=config.POOL_QUALITY
                        )
                        
                        print(f"Created pool versions for {image_record.original_filename}: {list(created_paths.keys())}")
                        
                    except Exception as pool_error:
                        # Pool generation is non-critical - don't fail the import
                        print(f"Warning: Failed to create pool versions for {file_path}: {pool_error}")
                        # Continue with import process
                
            except Exception as e:
                errors_count += 1
                error_msg = f"{file_path}: {str(e)}"
                errors_log.append(error_msg)
                print(f"Error importing {file_path}: {e}")
            
            # Update session progress periodically
            if (imported_count + duplicates_count + raw_files_count + single_raw_count + errors_count) % 10 == 0:
                session.images_imported = imported_count
                session.duplicates_skipped = duplicates_count
                session.raw_files_skipped = raw_files_count
                session.single_raw_skipped = single_raw_count
                session.errors_count = errors_count
                db.commit()
        
        # Final update with correct statistics
        session.images_imported = imported_count
        session.duplicates_skipped = duplicates_count
        session.raw_files_skipped = raw_files_count
        session.single_raw_skipped = single_raw_count
        session.errors_count = errors_count
        session.completed_at = datetime.utcnow()
        session.status = "completed"
        
        if errors_log:
            session.error_log = "\\n".join(errors_log[:100])  # Limit error log size
        
        db.commit()
        
        print(f"Import completed: {imported_count} imported, {duplicates_count} duplicates, {errors_count} errors")
        
    except Exception as e:
        # Mark session as failed
        session.status = "failed"
        session.error_log = str(e)
        session.completed_at = datetime.utcnow()
        db.commit()
        print(f"Import failed: {e}")
        
    finally:
        db.close()


@router.post("/test-single")
async def test_single_image(file_path: str, db: Session = Depends(get_db)):
    """
    Test importing a single image file (for development/testing)
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File does not exist")
    
    if not ImageProcessor.is_any_supported_format(file_path):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    try:
        image_record = create_image_record(file_path, "test_import", db)
        
        if image_record is None:
            return {"message": "File skipped (duplicate or error)", "success": False}
        
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
        
        return {
            "message": "Image imported successfully",
            "success": True,
            "image_id": image_record.id,
            "hash": image_record.image_hash,
            "filename": image_record.original_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")