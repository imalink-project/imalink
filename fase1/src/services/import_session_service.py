"""
Import Session Service - Simple CRUD for user's reference metadata

ImportSession is a metadata container for user's notes about import batches.
All file operations are handled by the client application.
"""
from typing import Optional
from sqlalchemy.orm import Session

from repositories.import_session_repository import ImportSessionRepository
from schemas.responses.import_session_responses import (
    ImportSessionResponse,
    ImportSessionListResponse
)
from core.exceptions import NotFoundError


class ImportSessionService:
    """Service class for ImportSession simple CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.import_repo = ImportSessionRepository(db)
    
    # === Simple CRUD Operations ===
    
    def create_simple_session(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        storage_location: Optional[str] = None,
        default_author_id: Optional[int] = None
    ):
        """Create a simple ImportSession (user metadata only)"""
        session = self.import_repo.create_simple(
            title=title,
            description=description,
            storage_location=storage_location,
            default_author_id=default_author_id
        )
        
        response = ImportSessionResponse.model_validate(session)
        response.images_count = 0  # No images yet
        return response
    
    def get_session_by_id(self, session_id: int):
        """Get ImportSession by ID"""
        session = self.import_repo.get_import_by_id(session_id)
        if not session:
            raise NotFoundError("Import session", session_id)
        
        return ImportSessionResponse.model_validate(session)
    
    def list_simple_sessions(self, limit: int = 100, offset: int = 0):
        """List all ImportSessions with pagination"""
        sessions = self.import_repo.get_all_imports(limit=limit, offset=offset)
        total = self.import_repo.count_imports()
        
        session_responses = [ImportSessionResponse.model_validate(s) for s in sessions]
        
        return ImportSessionListResponse(
            sessions=session_responses,
            total=total
        )
    
    def update_simple_session(
        self,
        session_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        storage_location: Optional[str] = None,
        default_author_id: Optional[int] = None
    ):
        """Update ImportSession metadata"""
        session = self.import_repo.update_simple(
            session_id=session_id,
            title=title,
            description=description,
            storage_location=storage_location,
            default_author_id=default_author_id
        )
        
        if not session:
            raise NotFoundError("Import session", session_id)
        
        return ImportSessionResponse.model_validate(session)
    
    def delete_session(self, session_id: int) -> bool:
        """Delete ImportSession"""
        success = self.import_repo.delete(session_id)
        if not success:
            raise NotFoundError("Import session", session_id)
        return success
