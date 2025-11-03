"""
Development/Debug API endpoints - ONLY for development use
"""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.core.dependencies import get_db
from src.core.config import Config
from src.database.connection import init_database

router = APIRouter()

def is_development_mode():
    """Check if we're in development mode - multiple safety checks"""
    # Check multiple indicators for development
    dev_indicators = [
        os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
        os.getenv("ENVIRONMENT", "").lower() in ("dev", "development", "local"),
        "temp" in Config.DATABASE_URL.lower(),  # Database in temp folder
        "test" in Config.DATABASE_URL.lower(),  # Test database
    ]
    return any(dev_indicators)

@router.get("/status")
async def dev_status():
    """Get development environment status"""
    return {
        "development_mode": is_development_mode(),
        "database_url": Config.DATABASE_URL,
        "data_directory": Config.DATA_DIRECTORY,
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@router.post("/reset-database")
async def reset_database(
    confirm: str = "no",
    db: Session = Depends(get_db)
):
    """
    🚨 DANGER: Reset entire database (development only)
    
    This will delete ALL data in the database!
    
    Parameters:
    - confirm: Must be exactly "DELETE_EVERYTHING" to proceed
    """
    
    # Safety check 1: Development mode only
    if not is_development_mode():
        raise HTTPException(
            status_code=403,
            detail="Database reset only allowed in development mode"
        )
    
    # Safety check 2: Confirmation required
    if confirm != "DELETE_EVERYTHING":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Confirmation required",
                "required_confirm": "DELETE_EVERYTHING",
                "message": "This will delete ALL data. Use with extreme caution."
            }
        )
    
    try:
        # Get all table names
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """))
        tables = [row[0] for row in result.fetchall()]
        
        # Drop all tables
        for table in tables:
            db.execute(text(f"DROP TABLE IF EXISTS {table}"))
        
        db.commit()
        db.close()
        
        # Reinitialize database with fresh schema
        init_database()
        
        return {
            "status": "success",
            "message": f"Database reset complete. Deleted {len(tables)} tables.",
            "tables_deleted": tables,
            "database_reinitialized": True
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database reset failed: {str(e)}"
        )

@router.delete("/clear-table/{table_name}")
async def clear_table(
    table_name: str,
    confirm: str = "no",
    db: Session = Depends(get_db)
):
    """
    Clear specific table (development only)
    
    Parameters:
    - table_name: Name of table to clear (images, authors, import_sessions)
    - confirm: Must be "CLEAR_TABLE" to proceed
    """
    
    if not is_development_mode():
        raise HTTPException(
            status_code=403,
            detail="Table clearing only allowed in development mode"
        )
    
    if confirm != "CLEAR_TABLE":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Confirmation required",
                "required_confirm": "CLEAR_TABLE",
                "available_tables": ["images", "authors", "import_sessions"]
            }
        )
    
    allowed_tables = ["images", "authors", "import_sessions"]
    if table_name not in allowed_tables:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{table_name}' not allowed. Use: {allowed_tables}"
        )
    
    try:
        result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count_before = result.scalar()
        
        db.execute(text(f"DELETE FROM {table_name}"))
        db.commit()
        
        return {
            "status": "success",
            "table": table_name,
            "rows_deleted": count_before,
            "message": f"Table '{table_name}' cleared successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear table '{table_name}': {str(e)}"
        )

@router.get("/database-stats")
async def database_stats(db: Session = Depends(get_db)):
    """Get current database statistics"""
    
    if not is_development_mode():
        raise HTTPException(
            status_code=403,
            detail="Database stats only available in development mode"
        )
    
    try:
        stats = {}
        tables = ["images", "authors", "import_sessions"]
        
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                stats[table] = result.scalar()
            except:
                stats[table] = "table not found"
        
        return {
            "database_url": Config.DATABASE_URL,
            "table_counts": stats,
            "development_mode": is_development_mode()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database stats: {str(e)}"
        )

@router.get("/database-schema")
async def database_schema(db: Session = Depends(get_db)):
    """Get detailed database schema information"""
    
    if not is_development_mode():
        raise HTTPException(
            status_code=403,
            detail="Database schema info only available in development mode"
        )
    
    try:
        schema_info = {}
        
        # Get all table names
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        tables = [row[0] for row in result.fetchall()]
        
        for table_name in tables:
            # Get table info (columns, types, etc.)
            table_info = db.execute(text(f"PRAGMA table_info({table_name})"))
            columns = []
            
            for column in table_info.fetchall():
                columns.append({
                    "name": column[1],  # column name
                    "type": column[2],  # data type
                    "not_null": bool(column[3]),  # not null constraint
                    "default_value": column[4],  # default value
                    "primary_key": bool(column[5])  # primary key
                })
            
            # Get row count
            count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar()
            
            schema_info[table_name] = {
                "columns": columns,
                "row_count": row_count
            }
        
        return {
            "database_url": Config.DATABASE_URL,
            "tables": schema_info,
            "total_tables": len(tables),
            "development_mode": is_development_mode()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database schema: {str(e)}"
        )

@router.post("/clear-database")
async def clear_database(db: Session = Depends(get_db)):
    """
    🚨 DANGER: Clear all data from database (development only)
    
    This will delete ALL records from all tables but preserve the schema.
    Safer than reset-database as it doesn't drop tables.
    """
    
    # Safety check: Development mode only
    if not is_development_mode():
        raise HTTPException(
            status_code=403,
            detail="Database clear only allowed in development mode"
        )
    
    try:
        # Get all table names
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """))
        tables = [row[0] for row in result.fetchall()]
        
        # Count records before deletion
        counts_before = {}
        for table in tables:
            count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts_before[table] = count_result.scalar()
        
        # Disable foreign key constraints temporarily
        db.execute(text("PRAGMA foreign_keys = OFF"))
        
        # Clear all tables (but preserve schema)
        for table in tables:
            db.execute(text(f"DELETE FROM {table}"))
        
        # Re-enable foreign key constraints
        db.execute(text("PRAGMA foreign_keys = ON"))
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Database cleared successfully. Deleted data from {len(tables)} tables.",
            "tables_cleared": len(tables),
            "photos_deleted": counts_before.get("photos", 0),
            "images_deleted": counts_before.get("images", 0),
            "authors_deleted": counts_before.get("authors", 0),
            "import_sessions_deleted": counts_before.get("import_sessions", 0),
            "total_records_deleted": sum(counts_before.values())
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database clear failed: {str(e)}"
        )