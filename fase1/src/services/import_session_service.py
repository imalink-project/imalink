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
    ImportTestResponse
)
from schemas.common import PaginatedResponse, create_paginated_response
from core.exceptions import NotFoundError, ValidationError


class ImportSessionService:
    """Service class for ImportSession business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.import_repo = ImportSessionRepository(db)
    
    async def start_import(self, request: ImportStartRequest) -> ImportStartResponse:
        """Start a new import session"""
        # Logging handled by proper logger if needed
        
        # Business Logic: Validate source path
        source_path = Path(request.source_directory)
        
        if not source_path.exists():
            raise ValidationError(f"Source path does not exist: {request.source_directory}")
        
        if not source_path.is_dir():
            raise ValidationError(f"Source path must be a directory: {request.source_directory}")
        
        # Business Logic: Check if path is accessible
        try:
            # Try to list directory to check permissions
            list(source_path.iterdir())
        except PermissionError:
            raise ValidationError(f"Permission denied accessing: {request.source_directory}")
        except OSError as e:
            raise ValidationError(f"Cannot access path: {str(e)}")
        
        # Create import session
        session = self.import_repo.create_import(request)
        
        return ImportStartResponse(
            message="Import started successfully",
            import_id=session.id,
            status=session.status
        )
    
    async def get_import_status(self, import_id: int) -> ImportResponse:
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
    
    async def list_imports(
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
    
    async def get_import_by_id(self, import_id: int) -> ImportResponse:
        """Get specific import session by ID"""
        
        session = self.import_repo.get_import_by_id(import_id)
        if not session:
            raise NotFoundError("Import session", import_id)
        
        return self._convert_to_response(session)
    
    async def test_single_file(self, request: ImportTestRequest) -> ImportTestResponse:
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
    
    async def get_import_statistics(self) -> Dict[str, Any]:
        """Get comprehensive import statistics"""
        return self.import_repo.get_import_statistics()
    
    async def get_active_imports(self) -> List[ImportResponse]:
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
            
            # Import result classification and user feedback
            import_result_type=getattr(session, 'import_result_type', None),
            user_feedback_message=getattr(session, 'user_feedback_message', None)
        )