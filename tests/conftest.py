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
from models.user import User
from services.auth_service import AuthService
from utils.security import create_access_token


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
def authenticated_client(test_client, test_db_session, auth_headers):
    """
    Test client with authentication headers pre-configured
    """
    # Store the headers and user for easy access in tests
    test_client.auth_headers = auth_headers
    
    return test_client
