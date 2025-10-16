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
    
    # Progress tracking
    progress_percentage: float = 0.0
    files_processed: int = 0
    current_file: Optional[str] = None
    is_cancelled: bool = False
    
    # Import result classification and user feedback
    import_result_type: Optional[str] = Field(None, description="Classification: all_new, all_duplicates, mixed")
    user_feedback_message: Optional[str] = Field(None, description="User-friendly message about import result")
    
    # Optional: Client-managed storage directory name
    storage_name: Optional[str] = Field(None, description="Storage directory name chosen by client (e.g., '20241004_vacation_photos')")
    
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


class ImportProgressResponse(BaseModel):
    """Response for import progress tracking"""
    import_id: int
    status: str
    progress_percentage: float = 0.0
    files_processed: int = 0
    total_files_found: int = 0
    current_file: Optional[str] = None
    is_cancelled: bool = False
    
    # Quick stats
    images_imported: int = 0
    duplicates_skipped: int = 0
    errors_count: int = 0
    
    class Config:
        from_attributes = True


class ImportCancelResponse(BaseModel):
    """Response when cancelling import"""
    message: str
    import_id: int
    success: bool
    status: str