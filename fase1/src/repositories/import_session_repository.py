"""
Import Session Repository - Data Access Layer for ImportSession simple CRUD
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import ImportSession


class ImportSessionRepository:
    """Repository class for ImportSession simple CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # === Simple CRUD Operations ===
    
    def get_import_by_id(self, session_id: int) -> Optional[ImportSession]:
        """Get ImportSession by ID"""
        return (
            self.db.query(ImportSession)
            .filter(ImportSession.id == session_id)
            .first()
        )
    
    def get_all_imports(self, limit: int = 50, offset: int = 0) -> List[ImportSession]:
        """Get all ImportSessions with pagination"""
        return (
            self.db.query(ImportSession)
            .order_by(desc(ImportSession.imported_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def count_imports(self) -> int:
        """Count total ImportSessions"""
        return self.db.query(ImportSession).count()
    
    def create_simple(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ) -> ImportSession:
        """Create a simple ImportSession (user metadata only)"""
        session = ImportSession(
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
        title: Optional[str] = None,
        description: Optional[str] = None,
        default_author_id: Optional[int] = None
    ) -> Optional[ImportSession]:
        """Update ImportSession metadata"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
        
        if title is not None:
            session.title = title
        if description is not None:
            session.description = description
        if default_author_id is not None:
            session.default_author_id = default_author_id
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def delete(self, session_id: int) -> bool:
        """Delete ImportSession"""
        session = self.get_import_by_id(session_id)
        if not session:
            return False
        
        self.db.delete(session)
        self.db.commit()
        return True
