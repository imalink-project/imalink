"""
Import session request schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class ImportSessionCreateRequest(BaseModel):
    """Request to create an import session (user's reference metadata)"""
    title: Optional[str] = Field(None, max_length=255, description="User's title for this import (e.g., 'Italy Summer 2024')")
    description: Optional[str] = Field(None, description="User's notes or comments about this import")
    storage_location: Optional[str] = Field(None, description="Where client stored the files (e.g., 'D:/photos/2024/italy')")
    default_author_id: Optional[int] = Field(None, description="Default photographer for this batch of photos")


class ImportSessionUpdateRequest(BaseModel):
    """Request to update import session metadata"""
    title: Optional[str] = Field(None, max_length=255, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    storage_location: Optional[str] = Field(None, description="Updated storage location")
    default_author_id: Optional[int] = Field(None, description="Updated default author")


# Backward compatibility - deprecated
class ImportStartRequest(ImportSessionCreateRequest):
    """DEPRECATED: Use ImportSessionCreateRequest instead"""
    source_path: Optional[str] = Field(None, description="DEPRECATED: Use storage_location")
    source_description: Optional[str] = Field(None, description="DEPRECATED: Use description")
    
    @property
    def source_directory(self) -> str:
        """DEPRECATED: Alias for backward compatibility"""
        return self.source_path or ""


class ImportTestRequest(BaseModel):
    """Test request schema"""
    test_parameter: str = Field("test", description="Test parameter for endpoint verification")


class SetStorageNameRequest(BaseModel):
    """DEPRECATED: Use ImportSessionUpdateRequest instead"""
    storage_name: str = Field(..., description="Storage name (directory name without path)")