"""
Import Repository - Data Access Layer for Import operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from models import Import, Image
from schemas.requests.import_requests import ImportStartRequest


class ImportRepository:
    """Repository class for Import data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # === Import CRUD Operations ===
    
    def create_import(self, request: ImportStartRequest) -> Import:
        """Create new import"""
        session = Import(
            source_path=request.source_path,
            source_description=request.source_description,
            status="in_progress",
            started_at=datetime.now()
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_import_by_id(self, session_id: int) -> Optional[Import]:
        """Get import by ID"""
        return (
            self.db.query(Import)
            .filter(Import.id == session_id)
            .first()
        )
    
    def update_import(
        self, 
        session_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[Import]:
        """Update import with progress data"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
        
        for key, value in update_data.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def complete_import(self, session_id: int) -> Optional[Import]:
        """Mark import as completed"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
        
        session.status = "completed"
        session.completed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def fail_import(self, session_id: int, error_message: str) -> Optional[Import]:
        """Mark import as failed"""
        session = self.get_import_by_id(session_id)
        if not session:
            return None
        
        session.status = "failed"
        session.error_message = error_message
        session.completed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_all_imports(self, limit: int = 50, offset: int = 0) -> List[Import]:
        """Get all imports with pagination"""
        return (
            self.db.query(Import)
            .order_by(desc(Import.started_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def count_imports(self) -> int:
        """Count total number of imports"""
        return self.db.query(Import).count()
    
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
        """Get comprehensive import statistics"""
        
        total_sessions = self.db.query(Import).count()
        
        completed_sessions = (
            self.db.query(Import)
            .filter(Import.status == "completed")
            .count()
        )
        
        failed_sessions = (
            self.db.query(Import)
            .filter(Import.status == "failed")
            .count()
        )
        
        in_progress_sessions = (
            self.db.query(Import)
            .filter(Import.status == "in_progress")
            .count()
        )
        
        # Aggregate statistics
        stats_result = (
            self.db.query(
                func.sum(Import.total_files_found).label('total_files'),
                func.sum(Import.images_imported).label('total_imported'),
                func.sum(Import.duplicates_skipped).label('total_duplicates'),
                func.sum(Import.errors_count).label('total_errors')
            )
            .filter(Import.status == "completed")
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
    
    def get_recent_imports(self, days: int = 7) -> List[Import]:
        """Get imports from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return (
            self.db.query(Import)
            .filter(Import.started_at >= cutoff_date)
            .order_by(desc(Import.started_at))
            .all()
        )
    
    # === Session Validation ===
    
    def session_exists(self, session_id: int) -> bool:
        """Check if import exists"""
        return (
            self.db.query(Import.id)
            .filter(Import.id == session_id)
            .first() is not None
        )
    
    def get_active_imports(self) -> List[Import]:
        """Get all currently active (in progress) sessions"""
        return (
            self.db.query(Import)
            .filter(Import.status == "in_progress")
            .order_by(Import.started_at)
            .all()
        )


