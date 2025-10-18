"""
FileStorage Service - Business Logic Layer for Physical File Storage Management

This service manages the business logic for physical file storage locations,
including directory creation, accessibility checking, and storage statistics.
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from repositories.file_storage_repository import FileStorageRepository
from models import FileStorage
from core.exceptions import ValidationError, NotFoundError


class FileStorageService:
    """Service for FileStorage business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = FileStorageRepository(db)
    
    def create_storage(
        self, 
        base_path: str, 
        display_name: Optional[str] = None, 
        description: Optional[str] = None,
        create_directory: bool = True
    ) -> FileStorage:
        """
        Create a new FileStorage location
        
        Args:
            base_path: Base path for storage (e.g., "/media/external-disk")
            display_name: User-friendly name
            description: Optional description
            create_directory: Whether to create the physical directory
            
        Returns:
            Created FileStorage instance
            
        Raises:
            ValidationError: If base_path is invalid or directory creation fails
        """
        # Validate base path
        if not base_path or not base_path.strip():
            raise ValidationError("Base path cannot be empty")
            
        base_path = base_path.strip()
        
        # Check if base path is accessible
        if not os.path.exists(base_path):
            raise ValidationError(f"Base path does not exist: {base_path}")
            
        if not os.path.isdir(base_path):
            raise ValidationError(f"Base path is not a directory: {base_path}")
        
        # Check for duplicate base path
        existing = self.repository.get_by_base_path(base_path)
        if existing:
            raise ValidationError(f"Storage with base path '{base_path}' already exists")
        
        # Create FileStorage instance
        storage = FileStorage(
            base_path=base_path,
            display_name=display_name,
            description=description
        )
        
        # Create physical directory if requested
        if create_directory:
            try:
                full_path = Path(storage.full_path)
                full_path.mkdir(parents=True, exist_ok=True)
                storage.is_accessible = True
                storage.last_accessed = datetime.utcnow()
            except (OSError, PermissionError) as e:
                raise ValidationError(f"Failed to create directory '{storage.full_path}': {str(e)}")
        
        # Save to database
        created_storage = self.repository.create(storage)
        self.db.commit()
        
        return created_storage
    
    def get_storage_by_uuid(self, storage_uuid: str) -> Optional[FileStorage]:
        """Get storage by UUID"""
        return self.repository.get_by_uuid(storage_uuid)
    
    def get_storage_by_directory_name(self, directory_name: str) -> Optional[FileStorage]:
        """Get storage by directory name"""
        return self.repository.get_by_directory_name(directory_name)
    
    def list_storages(
        self, 
        active_only: bool = False, 
        accessible_only: bool = False,
        skip: int = 0, 
        limit: int = 100
    ) -> List[FileStorage]:
        """List storages with filtering options"""
        return self.repository.get_all(
            active_only=active_only,
            accessible_only=accessible_only,
            skip=skip,
            limit=limit
        )
    
    def check_accessibility(self, storage_uuid: str) -> Dict[str, Any]:
        """
        Check if storage is accessible and update status
        
        Returns:
            Dictionary with accessibility information
        """
        storage = self.repository.get_by_uuid(storage_uuid)
        if not storage:
            raise NotFoundError("FileStorage", storage_uuid)
        
        # Check directory accessibility
        full_path = Path(storage.full_path)
        is_accessible = full_path.exists() and full_path.is_dir()
        
        # Check permissions
        can_read = False
        can_write = False
        if is_accessible:
            try:
                # Test read access
                list(full_path.iterdir())
                can_read = True
                
                # Test write access by creating a temporary file
                test_file = full_path / f".imalink_test_{uuid.uuid4().hex[:8]}"
                test_file.touch()
                test_file.unlink()
                can_write = True
            except (OSError, PermissionError):
                pass
        
        # Update storage status
        was_accessible = storage.is_accessible
        storage.is_accessible = is_accessible and can_read and can_write
        
        if storage.is_accessible:
            storage.last_accessed = datetime.utcnow()
        
        self.repository.update(storage)
        self.db.commit()
        
        return {
            'storage_uuid': storage_uuid,
            'directory_name': storage.directory_name,
            'full_path': storage.full_path,
            'is_accessible': storage.is_accessible,
            'can_read': can_read,
            'can_write': can_write,
            'exists': full_path.exists(),
            'is_directory': full_path.is_dir() if full_path.exists() else False,
            'status_changed': was_accessible != storage.is_accessible,
            'last_accessed': storage.last_accessed.isoformat() if storage.last_accessed else None
        }
    
    def update_storage_statistics(self, storage_uuid: str) -> Dict[str, Any]:
        """
        Update storage statistics by scanning the directory
        
        Returns:
            Updated statistics
        """
        storage = self.repository.get_by_uuid(storage_uuid)
        if not storage:
            raise NotFoundError(f"Storage not found: {storage_uuid}")
        
        if not storage.is_accessible:
            # Try to check accessibility first
            accessibility = self.check_accessibility(storage_uuid)
            if not accessibility['is_accessible']:
                raise ValidationError(f"Storage is not accessible: {storage.full_path}")
        
        # Scan directory for statistics
        full_path = Path(storage.full_path)
        total_files = 0
        total_size = 0
        
        try:
            for item in full_path.rglob('*'):
                if item.is_file():
                    total_files += 1
                    total_size += item.stat().st_size
        except (OSError, PermissionError) as e:
            raise ValidationError(f"Failed to scan directory '{storage.full_path}': {str(e)}")
        
        # Update storage
        storage.total_files = total_files
        storage.total_size_bytes = total_size
        storage.last_accessed = datetime.utcnow()
        
        self.repository.update(storage)
        self.db.commit()
        
        return {
            'storage_uuid': storage_uuid,
            'directory_name': storage.directory_name,
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size else 0.0,
            'last_updated': storage.last_accessed.isoformat()
        }
    
    def deactivate_storage(self, storage_uuid: str) -> FileStorage:
        """Deactivate storage (soft delete)"""
        storage = self.repository.get_by_uuid(storage_uuid)
        if not storage:
            raise NotFoundError(f"Storage not found: {storage_uuid}")
        
        if not storage.is_active:
            raise ValidationError(f"Storage is already deactivated: {storage_uuid}")
        
        storage.is_active = False
        updated_storage = self.repository.update(storage)
        self.db.commit()
        
        return updated_storage
    
    def reactivate_storage(self, storage_uuid: str) -> FileStorage:
        """Reactivate storage"""
        storage = self.repository.get_by_uuid(storage_uuid)
        if not storage:
            raise NotFoundError(f"Storage not found: {storage_uuid}")
        
        if storage.is_active:
            raise ValidationError(f"Storage is already active: {storage_uuid}")
        
        storage.is_active = True
        updated_storage = self.repository.update(storage)
        self.db.commit()
        
        return updated_storage
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get overall storage statistics"""
        return self.repository.get_statistics()
    
    def update_display_info(
        self, 
        storage_uuid: str, 
        display_name: Optional[str] = None, 
        description: Optional[str] = None
    ) -> FileStorage:
        """Update storage display information"""
        storage = self.repository.get_by_uuid(storage_uuid)
        if not storage:
            raise NotFoundError(f"Storage not found: {storage_uuid}")
        
        if display_name is not None:
            storage.display_name = display_name.strip() if display_name.strip() else None
            
        if description is not None:
            storage.description = description.strip() if description.strip() else None
        
        updated_storage = self.repository.update(storage)
        self.db.commit()
        
        return updated_storage