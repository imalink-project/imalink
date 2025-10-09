"""
Import session request schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class ImportStartRequest(BaseModel):
    """Request to start import session process"""
    source_path: str = Field(..., description="Path to directory containing images")
    source_description: str = Field("Manual import", description="Description of import source")
    default_author_id: Optional[int] = Field(default=None, description="Default author ID for imported images")
    archive_base_path: Optional[str] = Field(None, description="Base path for permanent storage (optional - will auto-generate if not provided)")
    storage_subfolder: Optional[str] = Field(None, description="Subfolder in storage (auto-generated if not provided)")
    copy_files: bool = Field(True, description="Whether to copy files to storage after database import")
    
    @property
    def source_directory(self) -> str:
        """Alias for backward compatibility"""
        return self.source_path


class ImportTestRequest(BaseModel):
    """Test request schema"""
    test_parameter: str = Field("test", description="Test parameter for endpoint verification")


class SetStorageNameRequest(BaseModel):
    """Request to set storage name for import session"""
    storage_name: str = Field(..., description="Storage name (directory name without path) with UUID suffix")