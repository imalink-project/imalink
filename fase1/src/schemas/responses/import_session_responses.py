"""
Import session response schemas
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ImportResponse(BaseModel):
    """Import session response model"""
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
    
    # Import result classification and user feedback
    import_result_type: Optional[str] = Field(None, description="Classification: all_new, all_duplicates, mixed")
    user_feedback_message: Optional[str] = Field(None, description="User-friendly message about import result")
    
    # Storage information (integrated from import_once)
    storage_name: Optional[str] = Field(None, description="Unique storage folder name")
    archive_base_path: Optional[str] = Field(None, description="Base path where storage folder is located")
    files_copied: int = 0
    files_copy_skipped: int = 0
    storage_errors: List[str] = Field(default_factory=list, description="Storage-related errors")
    
    class Config:
        from_attributes = True


class ImportStartResponse(BaseModel):
    """Response when starting import session"""
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
    """Response for import session list"""
    imports: List[ImportResponse]
    total: int = Field(..., description="Total number of sessions")
    
    class Config:
        from_attributes = True