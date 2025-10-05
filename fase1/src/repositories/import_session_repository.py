"""
Import Session Repository - Data Access Layer for ImportSession operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from models import ImportSession, Image
from schemas.requests.import_session_requests import ImportStartRequest


class ImportSessionRepository:
    """Repository class for ImportSession data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # === ImportSession CRUD Operations ===
    
    def create_import(self, request: ImportStartRequest) -> ImportSession:
        """Create new ImportSession"""
        session = ImportSession(
            source_path=request.source_path,
            source_description=request.source_description,
            status="in_progress",
            started_at=datetime.now(),
            archive_base_path=request.archive_base_path,
            copy_files=request.copy_files
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_import_by_id(self, session_id: int) -> Optional[ImportSession]:
        """Get ImportSession by ID"""
        return (
            self.db.query(ImportSession)
            .filter(ImportSession.id == session_id)
            .first()
        )
    
    def update_import(
        self, 
        session_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[ImportSession]:
        """Update ImportSession with progress data"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
        
        for key, value in update_data.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def complete_import(self, session_id: int) -> Optional[ImportSession]:
        """Mark ImportSession as completed"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
        
        session.status = "completed"
        session.completed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def fail_import(self, session_id: int, error_message: str) -> Optional[ImportSession]:
        """Mark ImportSession as failed"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
        
        session.status = "failed"
        session.error_message = error_message
        session.completed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def update_feedback(self, session_id: int, result_type: str, user_message: str) -> Optional[ImportSession]:
        """Update ImportSession with feedback information"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
            
        # Type ignore for SQLAlchemy column assignments (Pylance limitation)
        session.import_result_type = result_type  # type: ignore
        session.user_feedback_message = user_message  # type: ignore
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_all_imports(self, limit: int = 50, offset: int = 0) -> List[ImportSession]:
        """Get all imports with pagination"""
        return (
            self.db.query(ImportSession)
            .order_by(desc(ImportSession.started_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def count_imports(self) -> int:
        """Count total number of imports"""
        return self.db.query(ImportSession).count()
    
    # === Progress Tracking ===
    
    def increment_files_found(self, session_id: int, count: int = 1) -> bool:
        """Increment total files found counter"""
        return self._increment_counter(session_id, "total_files_found", count)
    
    def increment_images_imported(self, session_id: int, count: int = 1) -> bool:
        """Increment images imported counter"""
        return self._increment_counter(session_id, "images_imported", count)
    
    def increment_duplicates_skipped(self, session_id: int, count: int = 1) -> bool:
        """Increment duplicates skipped counter"""
        return self._increment_counter(session_id, "duplicates_skipped", count)
    
    def increment_raw_files_skipped(self, session_id: int, count: int = 1) -> bool:
        """Increment raw files skipped counter"""
        return self._increment_counter(session_id, "raw_files_skipped", count)
    
    def increment_single_raw_skipped(self, session_id: int, count: int = 1) -> bool:
        """Increment single raw skipped counter"""
        return self._increment_counter(session_id, "single_raw_skipped", count)
    
    def increment_errors(self, session_id: int, count: int = 1) -> bool:
        """Increment errors counter"""
        return self._increment_counter(session_id, "errors_count", count)
    
    def _increment_counter(self, session_id: int, field_name: str, count: int) -> bool:
        """Generic method to increment any counter field"""
        session = self.get_import_by_id(session_id)
        if not session:
            return False
        
        current_value = getattr(session, field_name, 0) or 0
        setattr(session, field_name, current_value + count)
        
        self.db.commit()
        return True
    
    # === Statistics and Reporting ===
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ImportSession statistics"""
        
        total_sessions = self.db.query(ImportSession).count()
        
        completed_sessions = (
            self.db.query(ImportSession)
            .filter(ImportSession.status == "completed")
            .count()
        )
        
        failed_sessions = (
            self.db.query(ImportSession)
            .filter(ImportSession.status == "failed")
            .count()
        )
        
        in_progress_sessions = (
            self.db.query(ImportSession)
            .filter(ImportSession.status == "in_progress")
            .count()
        )
        
        # Aggregate statistics
        stats_result = (
            self.db.query(
                func.sum(ImportSession.total_files_found).label('total_files'),
                func.sum(ImportSession.images_imported).label('total_imported'),
                func.sum(ImportSession.duplicates_skipped).label('total_duplicates'),
                func.sum(ImportSession.errors_count).label('total_errors')
            )
            .filter(ImportSession.status == "completed")
            .first()
        )
        
        total_files = getattr(stats_result, 'total_files', 0) or 0
        total_imported = getattr(stats_result, 'total_imported', 0) or 0
        total_duplicates = getattr(stats_result, 'total_duplicates', 0) or 0
        total_errors = getattr(stats_result, 'total_errors', 0) or 0
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "failed_sessions": failed_sessions,
            "in_progress_sessions": in_progress_sessions,
            "success_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            "total_files_processed": total_files,
            "total_images_imported": total_imported,
            "total_duplicates_skipped": total_duplicates,
            "total_errors": total_errors
        }
    
    def get_recent_imports(self, days: int = 7) -> List[ImportSession]:
        """Get imports from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return (
            self.db.query(ImportSession)
            .filter(ImportSession.started_at >= cutoff_date)
            .order_by(desc(ImportSession.started_at))
            .all()
        )
    
    # === Session Validation ===
    
    def session_exists(self, session_id: int) -> bool:
        """Check if ImportSession exists"""
        return (
            self.db.query(ImportSession.id)
            .filter(ImportSession.id == session_id)
            .first() is not None
        )
    
    def get_active_imports(self) -> List[ImportSession]:
        """Get all currently active (in progress) sessions"""
        return (
            self.db.query(ImportSession)
            .filter(ImportSession.status == "in_progress")
            .order_by(ImportSession.started_at)
            .all()
        )