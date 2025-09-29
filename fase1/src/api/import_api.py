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

from ..database.connection import get_db
from ..database.models import Image, ImportSession
from ..services.image_service import create_image_record, ImageProcessor

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
        processed = session.images_imported + session.duplicates_skipped + session.errors_count
        progress = (processed / session.total_files_found) * 100
    
    return ImportStatus(
        session_id=session.id,
        status=session.status,
        total_files_found=session.total_files_found,
        images_imported=session.images_imported,
        duplicates_skipped=session.duplicates_skipped,
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
            "errors_count": session.errors_count
        })
    
    return result


def import_directory_background(session_id: int, source_path: str, source_description: str):
    """
    Background task to import all images from a directory
    """
    from ..database.connection import get_db_sync
    
    db = get_db_sync()
    
    try:
        # Get the import session
        session = db.query(ImportSession).filter(ImportSession.id == session_id).first()
        if not session:
            return
        
        source_path_obj = Path(source_path)
        
        # Find all image files
        image_files = []
        for ext in ImageProcessor.SUPPORTED_FORMATS:
            pattern = f"**/*{ext}"
            image_files.extend(source_path_obj.rglob(pattern))
            # Also search uppercase extensions
            pattern = f"**/*{ext.upper()}"
            image_files.extend(source_path_obj.rglob(pattern))
        
        # Update session with total files found
        session.total_files_found = len(image_files)
        db.commit()
        
        # Process each file
        imported_count = 0
        duplicates_count = 0
        errors_count = 0
        errors_log = []
        
        for file_path in image_files:
            try:
                image_record = create_image_record(
                    str(file_path),
                    source_description,
                    db
                )
                
                if image_record is None:
                    # This could be a duplicate or unsupported file
                    duplicates_count += 1
                else:
                    db.add(image_record)
                    db.commit()
                    imported_count += 1
                
            except Exception as e:
                errors_count += 1
                error_msg = f"{file_path}: {str(e)}"
                errors_log.append(error_msg)
                print(f"Error importing {file_path}: {e}")
            
            # Update session progress periodically
            if (imported_count + duplicates_count + errors_count) % 10 == 0:
                session.images_imported = imported_count
                session.duplicates_skipped = duplicates_count
                session.errors_count = errors_count
                db.commit()
        
        # Final update
        session.images_imported = imported_count
        session.duplicates_skipped = duplicates_count
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
    
    if not ImageProcessor.is_supported_image(file_path):
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