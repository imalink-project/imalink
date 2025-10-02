"""
Import request schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class ImportStartRequest(BaseModel):
    """Request to start import process"""
    source_directory: str = Field(..., description="Path to directory containing images")
    source_description: str = Field("Manual import", description="Description of import source")
    default_author_id: Optional[int] = Field(default=None, description="Default author ID for imported images")
    
    @property
    def source_path(self) -> str:
        """Alias for backward compatibility"""
        return self.source_directory


class ImportTestRequest(BaseModel):
    """Request to test single file import"""
    file_path: str = Field(..., description="Path to single image file")
    source_description: str = Field("Test import", description="Description of import source")
    author_id: Optional[int] = Field(None, description="Author ID for the image")