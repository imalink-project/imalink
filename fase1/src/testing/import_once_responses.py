"""
Import Once response schemas
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ImportOnceResponse(BaseModel):
    """Response from import once operation"""
    success: bool = Field(..., description="Whether the operation succeeded")
    source_path: str = Field(..., description="Source path that was processed")
    storage_path: str = Field(..., description="Storage path where files were copied")
    
    total_files_found: int = Field(0, description="Total number of image files found in source")
    files_copied: int = Field(0, description="Number of files successfully copied")
    files_skipped: int = Field(0, description="Number of files skipped (already exist)")
    errors: List[str] = Field(default_factory=list, description="Any errors that occurred")
    
    started_at: datetime = Field(..., description="When the operation started")
    completed_at: Optional[datetime] = Field(None, description="When the operation completed")
    
    copied_files: List[Dict[str, Any]] = Field(default_factory=list, description="List of copied files with details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "source_path": "E:/DCIM/100CANON",
                "storage_path": "C:/ImaLink/Storage/import_2025-10-04_143022",
                "total_files_found": 25,
                "files_copied": 23,
                "files_skipped": 2,
                "errors": [],
                "started_at": "2025-10-04T14:30:22",
                "completed_at": "2025-10-04T14:32:15",
                "copied_files": []
            }
        }


class ImportOnceValidationResponse(BaseModel):
    """Response for path validation"""
    valid: bool = Field(..., description="Whether paths are valid")
    message: str = Field(..., description="Validation message")
    source_info: Optional[Dict[str, Any]] = Field(None, description="Source path information")
    storage_info: Optional[Dict[str, Any]] = Field(None, description="Storage path information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "message": "Paths validated successfully",
                "source_info": {
                    "path": "E:/DCIM/100CANON",
                    "exists": True,
                    "files_found": 25
                },
                "storage_info": {
                    "base_path": "C:/ImaLink/Storage",
                    "target_path": "C:/ImaLink/Storage/import_2025-10-04_143022",
                    "writable": True
                }
            }
        }