"""
Import-related Pydantic schemas for API requests and responses
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ImportRequestCreate(BaseModel):
    """Request model for starting import operations"""
    source_path: str = Field(..., min_length=1, description="Path to source directory")
    source_description: str = Field("Manual import", description="Description of the import source")


class ImportResponse(BaseModel):
    """Response model for import data"""
    id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = Field(..., description="Import status")
    source_path: str
    source_description: str
    total_files_found: int = 0
    images_imported: int = 0
    duplicates_skipped: int = 0
    raw_files_skipped: int = 0
    single_raw_skipped: int = 0
    errors_count: int = 0
    
    class Config:
        from_attributes = True


class ImportStatusResponse(BaseModel):
    """Response model for import status queries"""
    import_id: int
    status: str
    total_files_found: int
    images_imported: int
    duplicates_skipped: int
    raw_files_skipped: int
    single_raw_skipped: int
    errors_count: int
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")


class ImportStartResponse(BaseModel):
    """Response model for starting an import"""
    message: str
    import_id: int
    status: str


class ImportListResponse(BaseModel):
    """Response model for listing imports"""
    imports: List[ImportResponse] = Field(..., description="Array of imports")
    total: int = Field(..., description="Total number of imports")
    
    class Config:
        from_attributes = True


class SingleFileTestRequest(BaseModel):
    """Request model for testing single file import"""
    file_path: str = Field(..., min_length=1, description="Path to single file to test")


class SingleFileTestResponse(BaseModel):
    """Response model for single file test results"""
    file_path: str
    is_valid: bool
    file_size: int
    file_type: Optional[str] = None
    dimensions: Optional[str] = None
    exif_data: Optional[dict] = None
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Any warnings")