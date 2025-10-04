"""
Minimal route testing - sjekker at API-endepunkter eksisterer og returnerer korrekte statuskoder.
Fokuserer på de vanligste feilene: 404 (rute ikke funnet) og 500 (server errors).
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path so we can import from it
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from fastapi.testclient import TestClient
from main import app

# Test client
client = TestClient(app)


class TestAPIRoutes:
    """Test that API routes exist and return expected status codes"""
    
    def test_health_endpoint(self):
        """Health endpoint should always work"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_images_api_exists(self):
        """Images API should exist and return 200 with structured data"""
        response = client.get("/api/v1/images/")
        assert response.status_code == 200
        data = response.json()
        # Modern API returns structured response
        assert "data" in data or isinstance(data, list)
        if "data" in data:
            assert isinstance(data["data"], list)
    
    def test_authors_api_exists(self):
        """Authors API should exist and return 200"""
        response = client.get("/api/v1/authors/")
        assert response.status_code == 200
        data = response.json()
        # Modern API returns structured response
        assert "data" in data or isinstance(data, list)
        if "data" in data:
            assert isinstance(data["data"], list)
    
    def test_import_sessions_api_exists(self):
        """Import sessions API should exist"""
        response = client.get("/api/v1/import_sessions/")
        assert response.status_code == 200
        data = response.json()
        # Import sessions API returns list of import sessions
        assert isinstance(data, list) or "data" in data


class TestAPIOnlySystem:
    """Test that system is now API-only without HTML routes"""
    
    def test_no_root_route(self):
        """Root route should not exist in API-only system"""
        response = client.get("/")
        assert response.status_code == 404
    
    def test_debug_routes_endpoint(self):
        """Debug routes endpoint should exist for introspection"""
        response = client.get("/debug/routes")
        assert response.status_code == 200
        data = response.json()
        assert "routes" in data
        assert isinstance(data["routes"], list)


class TestCommonErrors:
    """Test common error scenarios"""
    
    def test_404_for_nonexistent_route(self):
        """Non-existent routes should return 404"""
        response = client.get("/this-route-does-not-exist")
        assert response.status_code == 404
    
    def test_404_for_nonexistent_api_route(self):
        """Non-existent API routes should return 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_demo_routes_removed(self):
        """Old demo routes should be removed"""
        response = client.get("/demo")
        assert response.status_code == 404
        
        response = client.get("/demo/import")
        assert response.status_code == 404


if __name__ == "__main__":
    # Kjør testene direkte
    pytest.main([__file__, "-v"])
