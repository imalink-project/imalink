"""
Pytest configuration and fixtures
Sets up test environment for all test modules
"""
import sys
import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import after path setup
from fastapi.testclient import TestClient
from main import app
from database.connection import get_db
from models import Base


@pytest.fixture(scope="function")
def test_db_engine():
    """
    Create a fresh in-memory SQLite database for each test
    
    This ensures complete test isolation - each test gets its own database
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    Create a database session for a test
    
    Uses the test database engine to ensure isolation
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """
    FastAPI test client with isolated test database
    
    Each test gets:
    - Fresh in-memory database
    - Clean test client
    - Complete test isolation
    """
    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass  # Session cleanup handled by test_db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()
