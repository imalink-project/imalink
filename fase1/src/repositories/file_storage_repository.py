"""
FileStorage Repository - Data Access Layer for FileStorage operations
"""
from typing import List, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func

from models import FileStorage


class FileStorageRepository:
    """Repository class for FileStorage CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # === Basic CRUD Operations ===
    
    def get_by_id(self, storage_id: int) -> Optional[FileStorage]:
        """Get FileStorage by ID"""
        return self.db.query(FileStorage).filter(FileStorage.id == storage_id).first()
    
    def get_by_uuid(self, storage_uuid: str) -> Optional[FileStorage]:
        """Get FileStorage by UUID"""
        return self.db.query(FileStorage).filter(FileStorage.storage_uuid == storage_uuid).first()
    
    def get_by_directory_name(self, directory_name: str) -> Optional[FileStorage]:
        """Get FileStorage by directory name"""
        return self.db.query(FileStorage).filter(FileStorage.directory_name == directory_name).first()
    
    def get_by_base_path(self, base_path: str) -> Optional[FileStorage]:
        """Get FileStorage by base path"""
        return self.db.query(FileStorage).filter(FileStorage.base_path == base_path).first()
    
    def get_all(self, limit: int = 100, offset: int = 0, 
                skip: int = 0) -> List[FileStorage]:
        """Get all FileStorages with filtering and pagination"""
        query = self.db.query(FileStorage)
        
        # Use skip if provided, otherwise use offset
        actual_offset = skip if skip > 0 else offset
        
        return (query
                .order_by(desc(FileStorage.created_at))
                .limit(limit)
                .offset(actual_offset)
                .all())
    
    def count(self) -> int:
        """Count total FileStorages"""
        query = self.db.query(FileStorage)
        return query.count()
    
    def create(self, base_path: str, display_name: Optional[str] = None, 
              description: Optional[str] = None) -> FileStorage:
        """Create new FileStorage"""
        storage = FileStorage.create_storage(
            base_path=base_path,
            display_name=display_name,
            description=description
        )
        
        self.db.add(storage)
        self.db.commit()
        self.db.refresh(storage)
        return storage
    
    def update(self, storage_id: int, **kwargs) -> Optional[FileStorage]:
        """Update FileStorage with provided fields"""
        storage = self.get_by_id(storage_id)
        if not storage:
            return None
        
        # Allowed update fields
        allowed_fields = [
            'display_name', 'description'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(storage, field, value)
        
        self.db.commit()
        self.db.refresh(storage)
        return storage
    
    def delete(self, storage_id: int) -> bool:
        """Delete FileStorage permanently"""
        storage = self.get_by_id(storage_id)
        if not storage:
            return False
        
        self.db.delete(storage)
        self.db.commit()
        return True
        self.db.commit()
        return True
    
    def hard_delete(self, storage_id: int) -> bool:
        """Permanently delete FileStorage (use with caution)"""
        storage = self.get_by_id(storage_id)
        if not storage:
            return False
        
        self.db.delete(storage)
        self.db.commit()
        return True
    
    # === Storage-specific Operations ===
    
    def get_storages_by_base_path(self, base_path: str) -> List[FileStorage]:
        """Get all FileStorages in a specific base path"""
        return (self.db.query(FileStorage)
                .filter(FileStorage.base_path == base_path)
                .order_by(desc(FileStorage.created_at))
                .all())
    
    def get_storage_statistics(self) -> dict:
        """Get overall storage statistics"""
        total_storages = self.count()
        
        return {
            'total_storages': total_storages
        }
    
    def get_statistics(self) -> dict:
        """Alias for get_storage_statistics for service compatibility"""
        return self.get_storage_statistics()