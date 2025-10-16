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

from core.dependencies import get_import_session_service
from services.import_session_service import ImportSessionService
from schemas.requests.import_session_requests import (
    ImportSessionCreateRequest, 
    ImportSessionUpdateRequest
)
from schemas.responses.import_session_responses import (
    ImportSessionResponse,
    ImportSessionListResponse
)
from core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ImportSessionResponse, status_code=201)
def create_import_session(
    request: ImportSessionCreateRequest,
    service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Create a new import session (user's reference metadata).
    
    Client has already imported the images - this just records metadata.
    """
    try:
        response = service.create_simple_session(
            title=request.title,
            description=request.description,
            storage_location=request.storage_location,
            default_author_id=request.default_author_id
        )
        
        logger.info(f"Created import session: {request.title}")
        return response
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating import session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create import session: {str(e)}")


@router.get("/{import_id}", response_model=ImportSessionResponse)
def get_import_session(
    import_id: int,
    service: ImportSessionService = Depends(get_import_session_service)
):
    """Get a specific import session by ID"""
    try:
        return service.get_session_by_id(import_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving import session {import_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve import session: {str(e)}")


@router.get("/", response_model=ImportSessionListResponse)
def list_import_sessions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: ImportSessionService = Depends(get_import_session_service)
):
    """List all import sessions with pagination"""
    try:
        return service.list_simple_sessions(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Error listing import sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list import sessions: {str(e)}")


@router.patch("/{import_id}", response_model=ImportSessionResponse)
def update_import_session(
    import_id: int,
    request: ImportSessionUpdateRequest,
    service: ImportSessionService = Depends(get_import_session_service)
):
    """Update import session metadata"""
    try:
        response = service.update_simple_session(
            session_id=import_id,
            title=request.title,
            description=request.description,
            storage_location=request.storage_location,
            default_author_id=request.default_author_id
        )
        
        logger.info(f"Updated import session {import_id}")
        return response
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating import session {import_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update import session: {str(e)}")


@router.delete("/{import_id}", status_code=204)
def delete_import_session(
    import_id: int,
    service: ImportSessionService = Depends(get_import_session_service)
):
    """
    Delete an import session.
    
    WARNING: This will also delete all images associated with this import session
    due to cascade delete. Use with caution.
    """
    try:
        service.delete_session(import_id)
        logger.info(f"Deleted import session {import_id}")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting import session {import_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete import session: {str(e)}")
