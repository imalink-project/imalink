"""
Import Session API - Simple CRUD for user's reference metadata

ImportSession is NOT a file processor - it's a metadata container for:
- User's notes about an import batch
- When the import happened  
- Who took the photos
- Where the client stored the files

All file operations are handled by the client application.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models.import_session import ImportSession
from schemas.requests.import_session_requests import (
    ImportSessionCreateRequest, 
    ImportSessionUpdateRequest
)
from schemas.responses.import_session_responses import (
    ImportSessionResponse,
    ImportSessionListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ImportSessionResponse, status_code=201)
async def create_import_session(
    request: ImportSessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new import session (user's reference metadata).
    
    Client has already imported the images - this just records metadata.
    """
    try:
        # Create new import session
        import_session = ImportSession(
            title=request.title,
            description=request.description,
            storage_location=request.storage_location,
            default_author_id=request.default_author_id
        )
        
        db.add(import_session)
        db.commit()
        db.refresh(import_session)
        
        logger.info(f"Created import session {import_session.id}: {import_session.title}")
        
        # Use model_validate to convert SQLAlchemy model to Pydantic
        response = ImportSessionResponse.model_validate(import_session)
        response.images_count = 0  # No images yet
        return response
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating import session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create import session: {str(e)}")


@router.get("/{import_id}", response_model=ImportSessionResponse)
async def get_import_session(
    import_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific import session by ID"""
    import_session = db.query(ImportSession).filter(ImportSession.id == import_id).first()
    
    if not import_session:
        raise HTTPException(status_code=404, detail=f"Import session {import_id} not found")
    
    return ImportSessionResponse.model_validate(import_session)


@router.get("/", response_model=ImportSessionListResponse)
async def list_import_sessions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all import sessions with pagination"""
    total = db.query(ImportSession).count()
    
    sessions = (
        db.query(ImportSession)
        .order_by(ImportSession.imported_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Convert to response format using model_validate
    session_responses = [ImportSessionResponse.model_validate(s) for s in sessions]
    
    return ImportSessionListResponse(
        sessions=session_responses,
        total=total
    )


@router.patch("/{import_id}", response_model=ImportSessionResponse)
async def update_import_session(
    import_id: int,
    request: ImportSessionUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update import session metadata"""
    import_session = db.query(ImportSession).filter(ImportSession.id == import_id).first()
    
    if not import_session:
        raise HTTPException(status_code=404, detail=f"Import session {import_id} not found")
    
    try:
        # Update fields using setattr to avoid type errors
        if request.title is not None:
            setattr(import_session, 'title', request.title)
        if request.description is not None:
            setattr(import_session, 'description', request.description)
        if request.storage_location is not None:
            setattr(import_session, 'storage_location', request.storage_location)
        if request.default_author_id is not None:
            setattr(import_session, 'default_author_id', request.default_author_id)
        
        db.commit()
        db.refresh(import_session)
        
        logger.info(f"Updated import session {import_id}")
        
        return ImportSessionResponse.model_validate(import_session)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating import session {import_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update import session: {str(e)}")


@router.delete("/{import_id}", status_code=204)
async def delete_import_session(
    import_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an import session.
    
    WARNING: This will also delete all images associated with this import session
    due to cascade delete. Use with caution.
    """
    import_session = db.query(ImportSession).filter(ImportSession.id == import_id).first()
    
    if not import_session:
        raise HTTPException(status_code=404, detail=f"Import session {import_id} not found")
    
    try:
        db.delete(import_session)
        db.commit()
        
        logger.info(f"Deleted import session {import_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting import session {import_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete import session: {str(e)}")
