"""
Import Session Repository - Data Access Layer for ImportSession simple CRUD
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models import ImportSession


class ImportSessionRepository:
    """Repository class for ImportSession simple CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # === Simple CRUD Operations ===
    
    def get_import_by_id(self, session_id: int, user_id: int) -> Optional[ImportSession]:
        """Get ImportSession by ID (user-scoped)"""
        query = (
            self.db.query(ImportSession)
            .filter(ImportSession.id == session_id)
            .filter(ImportSession.user_id == user_id)
        )
        
        return query.first()
    
    def get_protected_session(self, user_id: int) -> Optional[ImportSession]:
        """
        Get user's protected ImportSession (default session for quick uploads)
        
        Used when import_session_id is not provided in PhotoCreateSchema API.
        """
        query = (
            self.db.query(ImportSession)
            .filter(ImportSession.is_protected == True)
            .filter(ImportSession.user_id == user_id)
        )
        
        return query.first()
    
    def get_all_imports(self, user_id: int, limit: int = 50, offset: int = 0) -> List[ImportSession]:
        """Get all ImportSessions with pagination (user-scoped)"""
        query = (
            self.db.query(ImportSession)
            .filter(ImportSession.user_id == user_id)
            .order_by(desc(ImportSession.imported_at))
        )
        
        return query.limit(limit).offset(offset).all()
    
    def count_imports(self, user_id: int) -> int:
        """Count total ImportSessions (user-scoped)"""
        query = self.db.query(ImportSession).filter(ImportSession.user_id == user_id)
        
        return query.count()
    
    def create_simple(
        self,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ) -> ImportSession:
        """Create a simple ImportSession (user metadata only, user-scoped)"""
        session = ImportSession(
            user_id=user_id,
            imported_at=datetime.now(),
            title=title,
            description=description,
            default_author_id=default_author_id
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def update_simple(
        self,
        session_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ) -> Optional[ImportSession]:
        """Update ImportSession metadata (user-scoped)"""
        session = self.get_import_by_id(session_id, user_id)
        if not session:
            return None
        
        if title is not None:
            setattr(session, 'title', title)
        if description is not None:
            setattr(session, 'description', description)
        if default_author_id is not None:
            setattr(session, 'default_author_id', default_author_id)
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def delete(self, session_id: int, user_id: int) -> bool:
        """Delete ImportSession (user-scoped)"""
        session = self.get_import_by_id(session_id, user_id)
        if not session:
            return False
        
        self.db.delete(session)
        self.db.commit()
        return True
