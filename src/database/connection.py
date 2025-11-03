"""
Database connection and session management
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models import Base
from core.config import Config

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
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def get_db_sync() -> Session:
    """
    Get a database session for synchronous operations
    """
    return SessionLocal()


# Initialize database on import
def init_database():
    """Initialize database with all tables"""
    try:
        create_tables()
    except Exception as e:
        raise
