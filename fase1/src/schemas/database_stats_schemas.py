"""
Database statistics schemas
"""
from pydantic import BaseModel, Field
from typing import Dict


class TableStats(BaseModel):
    """Statistics for a single database table"""
    name: str = Field(..., description="Table name")
    record_count: int = Field(..., ge=0, description="Number of records in the table")
    size_bytes: int = Field(..., ge=0, description="Approximate size on disk in bytes")
    size_mb: float = Field(..., ge=0, description="Approximate size on disk in MB")


class StorageStats(BaseModel):
    """Statistics for file storage"""
    path: str = Field(..., description="Storage path")
    total_files: int = Field(..., ge=0, description="Total number of files")
    total_size_bytes: int = Field(..., ge=0, description="Total size in bytes")
    total_size_mb: float = Field(..., ge=0, description="Total size in MB")
    total_size_gb: float = Field(..., ge=0, description="Total size in GB")


class DatabaseStatsResponse(BaseModel):
    """Complete database and storage statistics"""
    tables: Dict[str, TableStats] = Field(..., description="Statistics per table")
    coldstorage: StorageStats = Field(..., description="Cold storage statistics")
    database_file: str = Field(..., description="Database file path")
    database_size_bytes: int = Field(..., ge=0, description="Total database file size in bytes")
    database_size_mb: float = Field(..., ge=0, description="Total database file size in MB")
