"""
Pytest configuration and fixtures
Sets up test environment for all test modules
"""
import sys
import pytest
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import after path setup
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def test_client():
    """FastAPI test client for API endpoint testing"""
    return TestClient(app)


@pytest.fixture(scope="session")
def test_db():
    """
    Test database session
    TODO: Setup test database for integration tests
    """
    pass
