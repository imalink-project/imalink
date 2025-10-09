"""
Storage service for managing permanent file archiving in ImportSession system
"""
import os
import shutil
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models.import_session import ImportSession
from ..models.image import Image
from ..core.config import config


@dataclass
class StorageResult:
    """Result of storage operation"""
    success: bool
    message: str
    files_copied: int = 0
    files_skipped: int = 0
    total_size_mb: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class StorageProgress:
    """Current progress of storage operation"""
    session_id: int
    status: str  # not_started, in_progress, completed, failed
    files_processed: int = 0
    total_files: int = 0
    current_file: Optional[str] = None
    files_copied: int = 0
    files_skipped: int = 0
    total_size_mb: int = 0
    errors: List[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.files_processed / self.total_files) * 100.0


class StorageService:
    """Service for handling permanent storage of ImportSession files"""
    
    def __init__(self, db: Session, base_storage_path: Optional[str] = None):
        self.db = db
        self.base_storage_path = base_storage_path or config.STORAGE_ROOT
        self._active_operations: Dict[int, StorageProgress] = {}
    
    def generate_storage_uuid(self) -> str:
        """Generate unique UUID for storage directory"""
        return str(uuid.uuid4())
    
    def generate_storage_directory_name(self, import_session: 'ImportSession', session_description: Optional[str] = None) -> str:
        """Generate storage directory name with date prefix and UUID suffix"""
        from datetime import datetime
        import re
        
        import_date = (import_session.started_at or datetime.utcnow()).strftime("%Y%m%d")
        uuid_suffix = import_session.storage_uuid[:8] if import_session.storage_uuid is not None else "unknown"
        
        if session_description:
            # Clean session description for filename safety
            safe_description = re.sub(r'[^\w\-_]', '_', session_description)[:50]
            return f"{import_date}_import_{safe_description}_{uuid_suffix}"
        else:
            return f"{import_date}_import_session_{uuid_suffix}"
    
    def find_storage_directory_path(self, directory_name: str) -> Optional[str]:
        """Find full path to storage directory by searching in storage_root"""
        base_path = Path(self.base_storage_path)
        
        # Search for directory in storage root
        for item in base_path.iterdir():
            if item.is_dir() and item.name == directory_name:
                return str(item)
        
        return None
    
    def get_storage_full_path(self, directory_name: str) -> str:
        """Get full path for storage directory (create if not exists)"""
        base_path = Path(self.base_storage_path)
        return str(base_path / directory_name)
    
    def validate_storage_directory(self, directory_name: str) -> Tuple[bool, str]:
        """Validate that storage directory name is valid and path is accessible"""
        try:
            # Get full path from directory name
            storage_path = self.get_storage_full_path(directory_name)
            path = Path(storage_path)
            
            # Check if parent directory exists or can be created
            parent = path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return False, f"Cannot create parent directory: {e}"
            
            # Check if we can create the directory
            if not path.exists():
                try:
                    path.mkdir(exist_ok=True)
                    # Test write permissions
                    test_file = path / ".write_test"
                    test_file.write_text("test")
                    test_file.unlink()
                except Exception as e:
                    return False, f"Cannot create or write to storage directory: {e}"
            
            return True, "Storage path is valid"
            
        except Exception as e:
            return False, f"Invalid storage path: {e}"
    
    def get_import_session_files(self, import_session: ImportSession) -> List[Dict[str, Any]]:
        """Get list of all files that need to be copied for an import session"""
        files = []
        
        # NOTE: This method is now deprecated since Image doesn't store file_path
        # Files should be found using ImportSession's original source_path
        # This is a placeholder that returns empty list to prevent errors
        
        # TODO: Implement proper file discovery from ImportSession.source_path
        # when copy operation is needed
        
        return files
    
    def calculate_total_size(self, files: List[Dict[str, Any]]) -> int:
        """Calculate total size in MB for list of files"""
        total_bytes = sum(f['size_bytes'] for f in files)
        return int(total_bytes / (1024 * 1024))  # Convert to MB
    
    async def prepare_storage(self, import_session_id: int, session_name: Optional[str] = None) -> StorageResult:
        """Prepare storage directory and update ImportSession with storage info"""
        import_session = self.db.query(ImportSession).filter(ImportSession.id == import_session_id).first()
        if not import_session:
            return StorageResult(success=False, message="ImportSession not found")
        
        # Check if already has storage configured
        if import_session.storage_uuid:
            return StorageResult(
                success=False, 
                message="ImportSession already has storage configured",
                files_copied=import_session.files_copied or 0,
                total_size_mb=import_session.storage_size_mb or 0
            )
        
        try:
            # Generate UUID and directory name
            storage_uuid = self.generate_storage_uuid()
            directory_name = self.generate_storage_directory_name(import_session, session_name)
            
            # Validate storage directory
            is_valid, validation_msg = self.validate_storage_directory(directory_name)
            if not is_valid:
                return StorageResult(success=False, message=f"Storage directory validation failed: {validation_msg}")
            
            # Get files to copy
            files = self.get_import_session_files(import_session)
            total_size_mb = self.calculate_total_size(files)
            
            # Update ImportSession with storage info
            import_session.storage_uuid = storage_uuid
            import_session.storage_directory_name = directory_name
            import_session.copy_status = "not_started"
            import_session.storage_size_mb = total_size_mb
            
            self.db.commit()
            
            return StorageResult(
                success=True,
                message=f"Storage prepared: {len(files)} files, {total_size_mb}MB",
                total_size_mb=total_size_mb
            )
            
        except Exception as e:
            self.db.rollback()
            return StorageResult(success=False, message=f"Failed to prepare storage: {e}")
    
    async def copy_files_to_storage(self, import_session_id: int) -> StorageResult:
        """Copy all files from ImportSession to permanent storage"""
        import_session = self.db.query(ImportSession).filter(ImportSession.id == import_session_id).first()
        if not import_session:
            return StorageResult(success=False, message="ImportSession not found")
        
        if not import_session.storage_uuid or not import_session.storage_directory_name:
            return StorageResult(success=False, message="Storage not prepared. Call prepare_storage first.")
        
        if import_session.copy_status == "completed":
            return StorageResult(
                success=True,
                message="Storage copy already completed",
                files_copied=import_session.files_copied or 0,
                total_size_mb=import_session.storage_size_mb or 0
            )
        
        # Initialize progress tracking
        files = self.get_import_session_files(import_session)
        progress = StorageProgress(
            session_id=import_session_id,
            status="in_progress",
            total_files=len(files),
            started_at=datetime.utcnow()
        )
        self._active_operations[import_session_id] = progress
        
        try:
            # Update ImportSession status
            import_session.copy_status = "in_progress"
            import_session.storage_started_at = progress.started_at
            self.db.commit()
            
            storage_path = Path(self.get_storage_full_path(import_session.storage_directory_name))
            storage_path.mkdir(parents=True, exist_ok=True)
            
            files_copied = 0
            files_skipped = 0
            total_size_bytes = 0
            errors = []
            
            for i, file_info in enumerate(files):
                try:
                    progress.current_file = file_info['filename']
                    progress.files_processed = i + 1
                    
                    source_path = Path(file_info['source_path'])
                    dest_path = storage_path / file_info['filename']
                    
                    # Skip if file already exists and is same size
                    if dest_path.exists() and dest_path.stat().st_size == file_info['size_bytes']:
                        files_skipped += 1
                        progress.files_skipped += 1
                    else:
                        # Copy file
                        shutil.copy2(source_path, dest_path)
                        files_copied += 1
                        progress.files_copied += 1
                        total_size_bytes += file_info['size_bytes']
                    
                    # Small delay to prevent overwhelming the system
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    error_msg = f"Failed to copy {file_info['filename']}: {e}"
                    errors.append(error_msg)
                    progress.errors.append(error_msg)
            
            # Update final status
            total_size_mb = int(total_size_bytes / (1024 * 1024))
            completed_at = datetime.utcnow()
            
            import_session.copy_status = "completed" if not errors else "failed"
            import_session.files_copied = files_copied
            import_session.files_copy_skipped = files_skipped
            import_session.storage_errors_count = len(errors)
            import_session.storage_size_mb = total_size_mb
            import_session.storage_completed_at = completed_at
            
            progress.status = import_session.copy_status
            progress.completed_at = completed_at
            progress.total_size_mb = total_size_mb
            
            self.db.commit()
            
            return StorageResult(
                success=len(errors) == 0,
                message=f"Storage copy {'completed' if not errors else 'completed with errors'}: {files_copied} copied, {files_skipped} skipped",
                files_copied=files_copied,
                files_skipped=files_skipped,
                total_size_mb=total_size_mb,
                errors=errors
            )
            
        except Exception as e:
            # Update error status
            import_session.copy_status = "failed"
            import_session.storage_completed_at = datetime.utcnow()
            progress.status = "failed"
            progress.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            return StorageResult(success=False, message=f"Storage copy failed: {e}", errors=[str(e)])
        
        finally:
            # Clean up progress tracking
            if import_session_id in self._active_operations:
                del self._active_operations[import_session_id]
    
    def get_storage_status(self, import_session_id: int) -> Optional[StorageProgress]:
        """Get current storage operation progress"""
        # Check if operation is active
        if import_session_id in self._active_operations:
            return self._active_operations[import_session_id]
        
        # Get status from database
        import_session = self.db.query(ImportSession).filter(ImportSession.id == import_session_id).first()
        if not import_session:
            return None
        
        return StorageProgress(
            session_id=import_session_id,
            status=import_session.copy_status or "not_started",
            files_processed=import_session.files_copied or 0,
            total_files=import_session.total_files_found or 0,
            files_copied=import_session.files_copied or 0,
            files_skipped=import_session.files_copy_skipped or 0,
            total_size_mb=import_session.storage_size_mb or 0,
            started_at=import_session.storage_started_at,
            completed_at=import_session.storage_completed_at
        )
    
    def verify_storage_integrity(self, import_session_id: int) -> StorageResult:
        """Verify that all files were copied correctly to storage"""
        import_session = self.db.query(ImportSession).filter(ImportSession.id == import_session_id).first()
        if not import_session:
            return StorageResult(success=False, message="ImportSession not found")
        
        if not import_session.storage_path:
            return StorageResult(success=False, message="No storage path configured")
        
        try:
            storage_path = Path(import_session.storage_path)
            if not storage_path.exists():
                return StorageResult(success=False, message="Storage directory does not exist")
            
            files = self.get_import_session_files(import_session)
            errors = []
            verified_count = 0
            
            for file_info in files:
                dest_path = storage_path / file_info['filename']
                
                if not dest_path.exists():
                    errors.append(f"Missing file: {file_info['filename']}")
                elif dest_path.stat().st_size != file_info['size_bytes']:
                    errors.append(f"Size mismatch: {file_info['filename']}")
                else:
                    verified_count += 1
            
            return StorageResult(
                success=len(errors) == 0,
                message=f"Verification {'passed' if not errors else 'failed'}: {verified_count}/{len(files)} files OK",
                files_copied=verified_count,
                errors=errors
            )
            
        except Exception as e:
            return StorageResult(success=False, message=f"Verification failed: {e}")