"""
Import response schemas
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ImportResponse(BaseModel):
    """Import response model"""
    id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = Field(..., description="Import status: in_progress, completed, failed")
    source_path: str
    source_description: Optional[str] = None
    total_files_found: int = 0
    images_imported: int = 0
    duplicates_skipped: int = 0
    raw_files_skipped: int = 0
    single_raw_skipped: int = 0
    errors_count: int = 0
    progress_percentage: float = 0.0
    
    class Config:
        from_attributes = True


class ImportStartResponse(BaseModel):
    """Response when starting import"""
    message: str
    import_id: int
    status: str


class ImportTestResponse(BaseModel):
    """Response for single file import test"""
    message: str
    success: bool
    image_id: Optional[int] = None
    hash: Optional[str] = None
    filename: Optional[str] = None


class ImportListResponse(BaseModel):
    """Response for import list"""
    imports: List[ImportResponse]
    total: int = Field(..., description="Total number of sessions")
    
    class Config:
        from_attributes = True