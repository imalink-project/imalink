"""
FileStorage model - Represents physical storage locations for image files
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
import re

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .import_session import ImportSession


class FileStorage(Base, TimestampMixin):
    """
    Represents a physical storage location where image files are stored.
    
    FileStorage manages:
    - Storage location on filesystem (external disks, network drives, etc.)
    - Unique directory naming for global identification
    - Storage accessibility and status tracking
    - Relationship to ImportSessions that use this storage
    
    Directory naming pattern: "imalink_YYYYMMDD_HHMMSS_uuid8"
    Example: "imalink_20241018_143052_a1b2c3d4"
    """
    __tablename__ = "file_storages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Storage identification
    storage_uuid = Column(String(36), unique=True, nullable=False, index=True)
    directory_name = Column(String(255), unique=True, nullable=False, index=True)
    
    # Storage location
    base_path = Column(Text, nullable=False)  # e.g., "/media/external-disk", "D:\PhotoStorage"
    
    # Storage metadata
    display_name = Column(String(255), nullable=True)  # User-friendly name
    description = Column(Text, nullable=True)
    
    # Relationships
    import_sessions = relationship("ImportSession", back_populates="file_storage")
    
    def __init__(self, base_path: str, display_name: Optional[str] = None, description: Optional[str] = None):
        """
        Initialize FileStorage with auto-generated directory name
        """
        super().__init__()
        self.storage_uuid = str(uuid.uuid4())
        self.base_path = base_path
        self.directory_name = self._generate_directory_name()
        self.display_name = display_name
        self.description = description
    
    def _generate_directory_name(self) -> str:
        """
        Generate unique directory name with imalink prefix, timestamp, and UUID
        
        Format: imalink_YYYYMMDD_HHMMSS_uuid8
        Example: imalink_20241018_143052_a1b2c3d4
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use the first 8 characters of the storage_uuid
        uuid_short = str(self.storage_uuid)[:8]
        return f"imalink_{timestamp}_{uuid_short}"
    
    @property
    def full_path(self) -> str:
        """Get full filesystem path (computed from base_path + directory_name)"""
        return f"{self.base_path.rstrip('/')}/{self.directory_name}"
    

    
    @classmethod
    def create_storage(cls, base_path: str, display_name: Optional[str] = None, 
                      description: Optional[str] = None) -> 'FileStorage':
        """
        Factory method to create new FileStorage with validated directory name
        """
        return cls(base_path=base_path, display_name=display_name, description=description)
    

    
    @property
    def master_index_path(self) -> str:
        """Path to master index.json file"""
        return f"{self.full_path}/index.json"
    
    @property
    def imports_index_dir(self) -> str:
        """Directory containing per-session index files"""
        return f"{self.full_path}/imports"
    
    def get_session_index_path(self, session_id: int) -> str:
        """Get path to specific import session index file"""
        return f"{self.imports_index_dir}/session_{session_id}.json"
    
    def generate_master_index_data(self) -> dict:
        """Generate master index.json data with overview of all import sessions"""
        from datetime import datetime
        
        master_data = {
            "storage_info": {
                "uuid": str(self.storage_uuid),
                "directory_name": str(self.directory_name),
                "base_path": str(self.base_path),
                "display_name": self.display_name,
                "description": self.description,
                "created_at": self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
                "last_scan": datetime.utcnow().isoformat()
            },
            "import_sessions": [],
            "imalink_version": "2.0"
        }
        
        # Add import session summaries
        if hasattr(self, 'import_sessions') and self.import_sessions:
            for session in self.import_sessions:
                session_summary = {
                    "id": int(session.id),
                    "title": str(session.title) if session.title else "Untitled",
                    "imported_at": session.imported_at.isoformat() if session.imported_at else None,
                    "file_count": session.images_count,
                    "index_file": f"imports/session_{session.id}.json"
                }
                master_data["import_sessions"].append(session_summary)
        
        return master_data
    
    def __repr__(self):
        return f"<FileStorage(id={self.id}, name='{str(self.directory_name)}')>"