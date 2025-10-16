"""
Import session response schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ImportSessionResponse(BaseModel):
    """Import session metadata response"""
    id: int
    imported_at: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    storage_location: Optional[str] = None
    default_author_id: Optional[int] = None
    images_count: int = Field(0, description="Number of images in this import session")
    
    class Config:
        from_attributes = True


class ImportSessionListResponse(BaseModel):
    """Response for import session list"""
    sessions: list[ImportSessionResponse]
    total: int = Field(..., description="Total number of sessions")
    
    class Config:
        from_attributes = True


# Backward compatibility - deprecated responses
class ImportResponse(ImportSessionResponse):
    """DEPRECATED: Use ImportSessionResponse instead"""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "completed"
    source_path: Optional[str] = None
    source_description: Optional[str] = None
    total_files_found: int = 0
    images_imported: int = 0
    duplicates_skipped: int = 0
    raw_files_skipped: int = 0
    single_raw_skipped: int = 0
    errors_count: int = 0
    progress_percentage: float = 0.0
    files_processed: int = 0
    current_file: Optional[str] = None
    is_cancelled: bool = False
    import_result_type: Optional[str] = None
    user_feedback_message: Optional[str] = None
    storage_name: Optional[str] = None


class ImportStartResponse(BaseModel):
    """DEPRECATED: Response when starting import session"""
    message: str
    import_id: int
    status: str = "completed"


class ImportTestResponse(BaseModel):
    """Response for single file import test"""
    message: str
    success: bool
    image_id: Optional[int] = None
    hash: Optional[str] = None
    filename: Optional[str] = None


class ImportListResponse(BaseModel):
    """DEPRECATED: Use ImportSessionListResponse instead"""
    imports: list[ImportResponse] = []
    total: int = 0


class ImportProgressResponse(BaseModel):
    """DEPRECATED: Progress tracking is now client responsibility"""
    import_id: int
    status: str = "completed"
    progress_percentage: float = 100.0
    files_processed: int = 0
    total_files_found: int = 0
    current_file: Optional[str] = None
    is_cancelled: bool = False
    images_imported: int = 0
    duplicates_skipped: int = 0
    errors_count: int = 0
    
    class Config:
        from_attributes = True


class ImportCancelResponse(BaseModel):
    """DEPRECATED: Cancellation is now client responsibility"""
    message: str
    import_id: int
    success: bool
    status: str = "completed"