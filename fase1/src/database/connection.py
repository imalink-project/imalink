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

# SQLite specific configuration for better performance
engine = create_engine(
    DATABASE_URL,
    # SQLite specific options
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL debugging
    connect_args={
        "check_same_thread": False,  # Allow SQLite to be used across threads
        "timeout": 30,  # 30 second timeout for locks
    }
)

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
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise