"""
Import Session Service - Simple CRUD for user's reference metadata

ImportSession is a metadata container for user's notes about import batches.
All file operations are handled by the client application.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.repositories.import_session_repository import ImportSessionRepository
from schemas.responses.import_session_responses import (
    ImportSessionResponse,
    ImportSessionListResponse
)
from src.core.exceptions import NotFoundError


class ImportSessionService:
    """Service class for ImportSession simple CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.import_repo = ImportSessionRepository(db)
    
    # === Simple CRUD Operations ===
    
    def create_simple_session(
        self,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ):
        """Create a simple ImportSession (user metadata only)"""
        session = self.import_repo.create_simple(
            user_id=user_id,
            title=title,
            description=description,
            default_author_id=default_author_id
        )
        
        response = ImportSessionResponse.model_validate(session)
        response.images_count = 0  # No images yet
        return response
    
    def get_session_by_id(self, session_id: int, user_id: int):
        """Get ImportSession by ID (user-scoped)"""
        session = self.import_repo.get_import_by_id(session_id, user_id)
        if not session:
            raise NotFoundError("Import session", session_id)
        
        return ImportSessionResponse.model_validate(session)
    
    def list_simple_sessions(self, user_id: int, limit: int = 100, offset: int = 0):
        """List all ImportSessions with pagination (user-scoped)"""
        sessions = self.import_repo.get_all_imports(limit=limit, offset=offset, user_id=user_id)
        total = self.import_repo.count_imports(user_id=user_id)
        
        session_responses = [ImportSessionResponse.model_validate(s) for s in sessions]
        
        return ImportSessionListResponse(
            sessions=session_responses,
            total=total
        )
    
    def update_simple_session(
        self,
        session_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ):
        """Update ImportSession metadata"""
        session = self.import_repo.update_simple(
            session_id=session_id,
            user_id=user_id,
            title=title,
            description=description,
            default_author_id=default_author_id
        )
        
        if not session:
            raise NotFoundError("Import session", session_id)
        
        return ImportSessionResponse.model_validate(session)
    
    def delete_session(self, session_id: int, user_id: int) -> bool:
        """Delete ImportSession"""
        success = self.import_repo.delete(session_id, user_id)
        if not success:
            raise NotFoundError("Import session", session_id)
        return success
