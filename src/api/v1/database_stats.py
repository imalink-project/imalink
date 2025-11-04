"""
Database statistics API endpoint
Provides overview of database table sizes and storage usage
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import os
import logging
from pathlib import Path
from typing import Dict

from src.database.connection import get_db
from src.schemas.database_stats_schemas import DatabaseStatsResponse, TableStats, StorageStats
from src.core.config import Config

router = APIRouter(prefix="/database-stats", tags=["System"])
logger = logging.getLogger(__name__)

config = Config()


def get_directory_size(path: Path) -> tuple[int, int]:
    """
    Calculate total size and file count of a directory
    
    Returns:
        Tuple of (total_size_bytes, total_files)
    """
    total_size = 0
    total_files = 0
    
    if not path.exists():
        return 0, 0
    
    for item in path.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size
            total_files += 1
    
    return total_size, total_files


@router.get("", response_model=DatabaseStatsResponse)
def get_database_stats(db: Session = Depends(get_db)):
    """
    Get database and storage statistics
    
    Returns overview of:
    - Table sizes (record count and disk size)
    - Cold storage usage
    - Total database file size
    
    No authentication required - intended for system monitoring.
    """
    try:
        logger.info("Starting database stats collection")
        
        # Get database file path and size
        db_url = config.DATABASE_URL
        logger.info(f"Database URL type: {db_url.split(':')[0]}")
        
        if db_url.startswith("sqlite:///"):
            db_file_path = db_url.replace("sqlite:///", "")
        else:
            db_file_path = "unknown"
        
        db_file_size_bytes = 0
        if os.path.exists(db_file_path):
            db_file_size_bytes = os.path.getsize(db_file_path)
        
        logger.info("Creating inspector")
        # Get table statistics
        inspector = inspect(db.bind)
        
        logger.info("Getting table names")
        table_names = inspector.get_table_names()
        logger.info(f"Found tables: {table_names}")
        
        tables_stats: Dict[str, TableStats] = {}
        
        for table_name in table_names:
            try:
                # Get record count
                logger.info(f"Querying table: {table_name}")
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                record_count = result.scalar() or 0
                
                # Get table size - database specific
                size_bytes = 0
                if is_sqlite := db_url.startswith("sqlite"):
                    # For SQLite, get approximate size using DBSTAT (if available)
                    try:
                        result = db.execute(text(
                            f"SELECT SUM(pgsize) FROM dbstat WHERE name='{table_name}'"
                        ))
                        size_bytes = result.scalar() or 0
                    except Exception:
                        # Fallback for SQLite
                        size_bytes = record_count * 1024
                else:
                    # For PostgreSQL, use pg_total_relation_size
                    try:
                        result = db.execute(text(
                            f"SELECT pg_total_relation_size('{table_name}')"
                        ))
                        size_bytes = result.scalar() or 0
                    except Exception:
                        # Fallback: rough estimate
                        size_bytes = record_count * 1024
                
                tables_stats[table_name] = TableStats(
                    name=table_name,
                    record_count=record_count,
                    size_bytes=size_bytes,
                    size_mb=round(size_bytes / (1024 * 1024), 2)
                )
            except Exception as e:
                logger.error(f"Failed to query table {table_name}: {e}")
                # Skip this table and continue with others
                continue
        
        # Get cold storage statistics
        # Coldpreviews are stored in DATA_DIRECTORY/coldpreviews
        coldstorage_path = Path(config.DATA_DIRECTORY) / "coldpreviews"
        coldstorage_size_bytes, coldstorage_files = get_directory_size(coldstorage_path)
        
        coldstorage_stats = StorageStats(
            path=str(coldstorage_path),
            total_files=coldstorage_files,
            total_size_bytes=coldstorage_size_bytes,
            total_size_mb=round(coldstorage_size_bytes / (1024 * 1024), 2),
            total_size_gb=round(coldstorage_size_bytes / (1024 * 1024 * 1024), 2)
        )
        
        return DatabaseStatsResponse(
            tables=tables_stats,
            coldstorage=coldstorage_stats,
            database_file=db_file_path,
            database_size_bytes=db_file_size_bytes,
            database_size_mb=round(db_file_size_bytes / (1024 * 1024), 2)
        )
    except Exception as e:
        # Rollback any failed transaction
        db.rollback()
        logger.error(f"Failed to get database stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get database statistics: {str(e)}")
