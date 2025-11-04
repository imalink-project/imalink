"""
Database connection and session management
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.models import Base
from src.core.config import Config

# Database configuration
# Use configuration from config.py
config = Config()
DATABASE_URL = config.DATABASE_URL

# Determine database type and configure accordingly
is_sqlite = DATABASE_URL.startswith("sqlite")
is_postgresql = DATABASE_URL.startswith("postgresql")

# Database-specific configuration
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,  # Set to True for SQL debugging
}

if is_sqlite:
    # SQLite specific configuration for better performance
    engine_kwargs["poolclass"] = StaticPool
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,  # Allow SQLite to be used across threads
        "timeout": 30,  # 30 second timeout for locks
    }
elif is_postgresql:
    # PostgreSQL specific configuration
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions
    Ensures proper cleanup even if transaction fails
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback on any exception to prevent aborted transaction state
        db.rollback()
        raise
    finally:
        # Always close the session
        db.close()



def get_db_sync() -> Session:
    """
    Get a database session for synchronous operations
    """
    return SessionLocal()


# Initialize database on import
def init_database():
    """Initialize database with all tables"""
    # Dispose of any existing connections first to ensure clean state
    engine.dispose()
    
    # Create tables if they don't exist
    # This uses engine directly, not a session, so no transaction to worry about
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Log but don't fail startup
        print(f"Warning: Could not create tables: {e}")
        # Not raising - tables might already exist
    
    # Dispose again to ensure no lingering connections from table creation
    engine.dispose()
