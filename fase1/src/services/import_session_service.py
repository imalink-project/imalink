"""
Import Session Service - Business Logic Layer for Import operations
"""
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from repositories.import_session_repository import ImportSessionRepository
from schemas.requests.import_session_requests import ImportStartRequest, ImportTestRequest
from schemas.responses.import_session_responses import (
    ImportResponse, ImportStartResponse, ImportListResponse,
    ImportTestResponse, ImportProgressResponse, ImportCancelResponse
)
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, ValidationError


class ImportSessionService:
    """Service class for ImportSession business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.import_repo = ImportSessionRepository(db)
    
    def start_import(self, request: ImportStartRequest) -> ImportStartResponse:
        """Start a new import session"""
        # Logging handled by proper logger if needed
        
        # Business Logic: Validate source path
        source_path = Path(request.source_path)
        
        if not source_path.exists():
            raise ValidationError(f"Source path does not exist: {request.source_path}")
        
        if not source_path.is_dir():
            raise ValidationError(f"Source path must be a directory: {request.source_path}")
        
        # Business Logic: Check if path is accessible
        try:
            # Try to list directory to check permissions
            list(source_path.iterdir())
        except PermissionError:
            raise ValidationError(f"Permission denied accessing: {request.source_path}")
        except OSError as e:
            raise ValidationError(f"Cannot access path: {str(e)}")
        
        # Create import session
        session = self.import_repo.create_import(request)
        
        return ImportStartResponse(
            message="Import started successfully",
            import_id=session.id,
            status=session.status
        )
    
    def get_import_status(self, import_id: int) -> ImportResponse:
        """Get status of an import session"""
        
        session = self.import_repo.get_import_by_id(import_id)
        if not session:
            raise NotFoundError("Import session", import_id)
        
        # Business Logic: Calculate progress percentage
        progress = 0.0
        total = getattr(session, 'total_files_found', 0) or 0
        if total > 0:
            processed = (
                getattr(session, 'images_imported', 0) or 0 +
                getattr(session, 'duplicates_skipped', 0) or 0 +
                getattr(session, 'raw_files_skipped', 0) or 0 +
                getattr(session, 'single_raw_skipped', 0) or 0 +
                getattr(session, 'errors_count', 0) or 0
            )
            progress = (processed / total) * 100.0
            # Cap at 100%
            progress = min(progress, 100.0)
        
        # Use from_attributes=True for Pydantic conversion
        response = ImportResponse.model_validate(session)
        response.progress_percentage = round(progress, 2)
        return response
    
    def list_imports(
        self,
        limit: int = 50
    ) -> ImportListResponse:
        """Get list of import imports"""
        
        imports = self.import_repo.get_all_imports(limit=limit, offset=0)
        total = self.import_repo.count_imports()
        
        # Convert to response models
        session_responses = []
        for session in imports:
            session_response = ImportResponse.model_validate(session) 
            session_responses.append(session_response)
        
        return ImportListResponse(
            imports=session_responses,
            total=total
        )
    
    def get_import_by_id(self, import_id: int) -> ImportResponse:
        """Get specific import session by ID"""
        
        session = self.import_repo.get_import_by_id(import_id)
        if not session:
            raise NotFoundError("Import session", import_id)
        
        return self._convert_to_response(session)
    
    def test_single_file(self, request: ImportTestRequest) -> ImportTestResponse:
        """Test if a single file can be imported"""
        
        file_path = Path(request.file_path)
        errors = []
        warnings = []
        
        # Business Logic: File validation
        if not file_path.exists():
            return ImportTestResponse(
                message="File does not exist",
                success=False
            )
        
        if not file_path.is_file():
            return ImportTestResponse(
                message="Path is not a file",
                success=False
            )
        
        try:
            # Get file info
            file_size = file_path.stat().st_size
            file_type = file_path.suffix.lower()
            
            # Business Logic: Check file type
            supported_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
            raw_extensions = {'.cr2', '.cr3', '.nef', '.arw', '.orf', '.dng', '.raf', '.rw2'}
            
            if file_type not in supported_extensions and file_type not in raw_extensions:
                warnings.append(f"Unsupported file type: {file_type}")
            
            # Business Logic: Check file size
            if file_size == 0:
                errors.append("File is empty")
            elif file_size < 1024:  # Less than 1KB
                warnings.append("File is very small, may not be a valid image")
            elif file_size > 100 * 1024 * 1024:  # More than 100MB
                warnings.append("File is very large, import may be slow")
            
            # Try to get basic image info
            dimensions = None
            exif_data = None
            
            try:
                from PIL import Image as PILImage
                with PILImage.open(file_path) as img:
                    dimensions = f"{img.width}x{img.height}"
                    
                    # Get basic EXIF if available
                    try:
                        exif = img.getexif()
                        if exif:
                            exif_data = {"exif_keys": len(exif)}
                    except:
                        exif_data = None
                    
            except Exception as e:
                if file_type in raw_extensions:
                    warnings.append(f"RAW file detected: {file_type}")
                else:
                    errors.append(f"Cannot read image: {str(e)}")
            
            is_valid = len(errors) == 0
            
            return ImportTestResponse(
                message="File validation successful" if is_valid else "File validation failed",
                success=is_valid,
                filename=file_path.name
            )
            
        except Exception as e:
            errors.append(f"Error accessing file: {str(e)}")
            return ImportTestResponse(
                message=f"Error accessing file: {str(e)}",
                success=False
            )
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """Get comprehensive import statistics"""
        return self.import_repo.get_import_statistics()
    
    def get_active_imports(self) -> List[ImportResponse]:
        """Get all currently active import imports"""
        
        active_imports = self.import_repo.get_active_imports()
        
        session_responses = []
        for session in active_imports:
            session_response = self._convert_to_response(session)
            session_responses.append(session_response)
        
        return session_responses
    
    # Progress tracking methods (for background tasks)
    
    def update_session_progress(self, import_id: int, update_data: Dict[str, Any]) -> bool:
        """Update import session progress"""
        session = self.import_repo.update_session(import_id, update_data)
        return session is not None
    
    def complete_session(self, import_id: int) -> bool:
        """Mark import session as completed"""
        session = self.import_repo.complete_session(import_id)
        return session is not None
    
    def fail_session(self, import_id: int, error_message: str) -> bool:
        """Mark import session as failed"""
        session = self.import_repo.fail_session(import_id, error_message)
        return session is not None
    
    # Counter methods for background import tasks
    
    def increment_files_found(self, import_id: int, count: int = 1) -> bool:
        """Increment files found counter"""
        return self.import_repo.increment_files_found(import_id, count)
    
    def increment_images_imported(self, import_id: int, count: int = 1) -> bool:
        """Increment images imported counter"""
        return self.import_repo.increment_images_imported(import_id, count)
    
    def increment_duplicates_skipped(self, import_id: int, count: int = 1) -> bool:
        """Increment duplicates skipped counter"""
        return self.import_repo.increment_duplicates_skipped(import_id, count)
    
    def increment_raw_files_skipped(self, import_id: int, count: int = 1) -> bool:
        """Increment raw files skipped counter"""
        return self.import_repo.increment_raw_files_skipped(import_id, count)
    
    def increment_single_raw_skipped(self, import_id: int, count: int = 1) -> bool:
        """Increment single raw skipped counter"""
        return self.import_repo.increment_single_raw_skipped(import_id, count)
    
    def increment_errors(self, import_id: int, count: int = 1) -> bool:
        """Increment errors counter"""
        return self.import_repo.increment_errors(import_id, count)
    
    # Private helper methods
    
    def _convert_to_response(self, session) -> ImportResponse:
        """Convert database model to response model"""
        
        return ImportResponse(
            id=getattr(session, 'id'),
            started_at=getattr(session, 'started_at', None),
            completed_at=getattr(session, 'completed_at', None),
            status=getattr(session, 'status', 'unknown'),
            source_path=getattr(session, 'source_path', ''),
            source_description=getattr(session, 'source_description', ''),
            total_files_found=getattr(session, 'total_files_found', 0) or 0,
            images_imported=getattr(session, 'images_imported', 0) or 0,
            duplicates_skipped=getattr(session, 'duplicates_skipped', 0) or 0,
            raw_files_skipped=getattr(session, 'raw_files_skipped', 0) or 0,
            single_raw_skipped=getattr(session, 'single_raw_skipped', 0) or 0,
            errors_count=getattr(session, 'errors_count', 0) or 0,
            
            # Progress tracking
            progress_percentage=getattr(session, 'progress_percentage', 0.0) or 0.0,
            files_processed=getattr(session, 'files_processed', 0) or 0,
            current_file=getattr(session, 'current_file', None),
            is_cancelled=getattr(session, 'is_cancelled', False) or False,
            
            # Import result classification and user feedback
            import_result_type=getattr(session, 'import_result_type', None),
            user_feedback_message=getattr(session, 'user_feedback_message', None),
            
            # Storage information
            storage_name=getattr(session, 'storage_name', None),
            archive_base_path=getattr(session, 'archive_base_path', None),
            files_copied=getattr(session, 'files_copied', 0) or 0,
            files_copy_skipped=getattr(session, 'files_copy_skipped', 0) or 0,
            storage_errors=[]  # This might need proper handling if it's stored as JSON
        )
    
    def get_import_progress(self, import_id: int) -> ImportProgressResponse:
        """Get real-time progress of import session"""
        session = self.import_repo.get_import_by_id(import_id)
        if not session:
            raise NotFoundError("Import session", import_id)
        
        return ImportProgressResponse(
            import_id=getattr(session, 'id'),
            status=getattr(session, 'status', 'unknown'),
            progress_percentage=getattr(session, 'progress_percentage', 0.0) or 0.0,
            files_processed=getattr(session, 'files_processed', 0) or 0,
            total_files_found=getattr(session, 'total_files_found', 0) or 0,
            current_file=getattr(session, 'current_file', None),
            is_cancelled=getattr(session, 'is_cancelled', False) or False,
            
            # Quick stats
            images_imported=getattr(session, 'images_imported', 0) or 0,
            duplicates_skipped=getattr(session, 'duplicates_skipped', 0) or 0,
            errors_count=getattr(session, 'errors_count', 0) or 0
        )
    
    def cancel_import(self, import_id: int) -> ImportCancelResponse:
        """Cancel running import session"""
        session = self.import_repo.get_import_by_id(import_id)
        if not session:
            raise NotFoundError("Import session", import_id)
        
        # Use repository method to cancel
        cancelled_session = self.import_repo.cancel_import(import_id)
        
        success = cancelled_session is not None
        final_status = getattr(cancelled_session, 'status', 'unknown') if success else 'error'
        
        message = "Import cancelled successfully" if success else "Failed to cancel import"
        
        return ImportCancelResponse(
            message=message,
            import_id=import_id,
            success=success,
            status=final_status
        )
    
    def copy_to_storage(self, import_id: int, storage_path: str) -> Dict[str, Any]:
        """
        Copy files from temp directory to user-specified storage location
        """
        import shutil
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get import session
        import_session = self.import_repo.get_import_by_id(import_id)
        if not import_session:
            raise NotFoundError("Import session", import_id)
        
        source_dir = Path(str(import_session.source_path))
        storage_dir = Path(storage_path)
        
        # Validate storage path
        if not storage_dir.parent.exists():
            raise ValidationError(f"Storage parent directory does not exist: {storage_dir.parent}")
        
        # Create storage directory if it doesn't exist
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy all files from source to storage, preserving structure
            files_copied = 0
            for item in source_dir.rglob("*"):
                if item.is_file():
                    # Calculate relative path
                    rel_path = item.relative_to(source_dir)
                    dest_path = storage_dir / rel_path
                    
                    # Create parent directories if needed
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(item, dest_path)
                    files_copied += 1
                    
                    logger.debug(f"Copied {item} -> {dest_path}")
            
            # Update import session with storage path
            self.import_repo.update_import(import_id, {
                "archive_base_path": str(storage_dir),
                "storage_name": storage_dir.name
            })
            
            logger.info(f"Successfully copied {files_copied} files to {storage_dir}")
            
            return {
                "storage_path": str(storage_dir),
                "files_copied": files_copied,
                "message": f"Successfully copied {files_copied} files to storage"
            }
            
        except Exception as e:
            logger.error(f"Failed to copy files to storage: {str(e)}")
            raise ValidationError(f"Failed to copy files to storage: {str(e)}")
    
    # === Simple CRUD Operations (for basic API endpoints) ===
    
    def create_simple_session(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        storage_location: Optional[str] = None,
        default_author_id: Optional[int] = None
    ):
        """Create a simple ImportSession (user metadata only)"""
        from schemas.responses.import_session_responses import ImportSessionResponse
        
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
        from schemas.responses.import_session_responses import ImportSessionResponse
        
        session = self.import_repo.get_import_by_id(session_id)
        if not session:
            raise NotFoundError("Import session", session_id)
        
        return ImportSessionResponse.model_validate(session)
    
    def list_simple_sessions(self, limit: int = 100, offset: int = 0):
        """List all ImportSessions with pagination"""
        from schemas.responses.import_session_responses import ImportSessionResponse, ImportSessionListResponse
        
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
        from schemas.responses.import_session_responses import ImportSessionResponse
        
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