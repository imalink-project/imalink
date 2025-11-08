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

# Set test environment BEFORE any imports
# This must happen before importing main.py or database.connection
os.environ["TESTING"] = "1"
# Use file-based memory database that can be shared across connections
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared&uri=true"

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import after path setup
from fastapi.testclient import TestClient
from main import app
from database.connection import get_db, engine as global_engine, SessionLocal
from models import Base
from models.user import User
from services.auth_service import AuthService
from utils.security import create_access_token


@pytest.fixture(scope="function")
def test_db_engine():
    """
    Use the global in-memory SQLite database engine from database.connection
    
    Since we set DATABASE_URL=sqlite:///:memory: before import,
    the global engine is already configured for testing.
    """
    # Create all tables in the test database
    Base.metadata.create_all(bind=global_engine)
    
    yield global_engine
    
    # Cleanup - drop all tables after test
    Base.metadata.drop_all(bind=global_engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    Create a database session for a test
    
    Uses the global test database engine
    """
    # Use the global SessionLocal which is already bound to our test engine
    session = SessionLocal()
    
    yield session
    
    # Rollback any uncommitted changes and close
    session.rollback()
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


@pytest.fixture(scope="function")
def test_user(test_db_session):
    """
    Create a test user for authentication tests
    """
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$test_hash_for_testing",  # Pre-hashed test password
        display_name="Test User",
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def auth_token(test_user):
    """
    Create a valid JWT token for the test user
    """
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """
    Create authorization headers with valid JWT token
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def authenticated_client(test_db_engine, test_client, test_db_session, auth_headers):
    """
    Test client with authentication headers pre-configured
    
    Explicitly depends on test_db_engine to ensure tables are created first
    """
    # Store the headers and user for easy access in tests
    test_client.auth_headers = auth_headers
    
    return test_client


@pytest.fixture(scope="function")
def client(test_client):
    """
    Unauthenticated test client for testing anonymous access
    """
    return test_client


@pytest.fixture(scope="function")
def second_user(test_db_session):
    """
    Create a second test user for multi-user tests
    """
    user = User(
        username="seconduser",
        email="second@example.com",
        password_hash="$2b$12$test_hash_for_testing",
        display_name="Second User",
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def second_user_token(second_user):
    """
    Create a valid JWT token for the second test user
    """
    return create_access_token(data={"sub": str(second_user.id)})


@pytest.fixture(scope="function")
def second_user_headers(second_user_token):
    """
    Create authorization headers for second user
    """
    return {"Authorization": f"Bearer {second_user_token}"}


@pytest.fixture(scope="function")
def second_user_client(test_client, second_user_headers):
    """
    Test client with second user authentication
    """
    test_client.auth_headers = second_user_headers
    return test_client
