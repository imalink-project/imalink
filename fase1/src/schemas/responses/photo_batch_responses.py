"""
Photo batch response schemas for bulk photo creation operations
"""
from typing import Optional, List
from pydantic import BaseModel, Field

from ..photo_schemas import PhotoResponse


class PhotoGroupResult(BaseModel):
    """Result for single photo group creation within a batch operation"""
    success: bool = Field(..., description="Whether this photo group was created successfully")
    hothash: str = Field(..., description="The hothash identifier for this photo group")
    
    # Success case data
    photo: Optional[PhotoResponse] = Field(None, description="Created photo data (if successful)")
    images_created: int = Field(0, ge=0, description="Number of images successfully created for this photo")
    
    # Duplicate handling data
    is_duplicate: bool = Field(False, description="Whether this photo was detected as a duplicate")
    existing_photo: Optional[PhotoResponse] = Field(None, description="Existing photo data (if duplicate)")
    partial_duplicate: bool = Field(False, description="Whether only some files were duplicates")
    images_added_to_existing: int = Field(0, ge=0, description="Number of new images added to existing photo")
    images_skipped_duplicate: int = Field(0, ge=0, description="Number of images skipped as duplicates")
    
    # Error case data
    error: Optional[str] = Field(None, description="Error message (if failed)")
    images_failed: int = Field(0, ge=0, description="Number of images that failed to create")
    
    class Config:
        from_attributes = True


class BatchPhotoResponse(BaseModel):
    """Response for batch photo creation operation"""
    success: bool = Field(..., description="Whether the overall batch operation was successful")
    
    # Summary statistics
    total_requested: int = Field(..., ge=0, description="Total number of photo groups requested")
    photos_created: int = Field(0, ge=0, description="Number of photos successfully created")
    photos_failed: int = Field(0, ge=0, description="Number of photos that failed to create")
    photos_duplicates: int = Field(0, ge=0, description="Number of photos detected as duplicates")
    partial_duplicates: int = Field(0, ge=0, description="Number of photos with partial duplicates")
    images_created: int = Field(0, ge=0, description="Total number of images successfully created")
    images_failed: int = Field(0, ge=0, description="Total number of images that failed to create")
    images_added_to_existing: int = Field(0, ge=0, description="Total number of images added to existing photos")
    images_skipped_duplicate: int = Field(0, ge=0, description="Total number of images skipped as duplicates")
    
    # Performance metrics
    processing_time_seconds: float = Field(..., ge=0.0, description="Total processing time in seconds")
    
    # Detailed results per photo group
    results: List[PhotoGroupResult] = Field(..., description="Detailed results for each photo group")
    
    # Error summary (if any critical errors occurred)
    error: Optional[str] = Field(None, description="Overall error message (if batch failed critically)")
    
    class Config:
        from_attributes = True