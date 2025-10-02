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
        response = client.get("/api/images/")
        assert response.status_code == 200
        data = response.json()
        # Modern API returns structured response with 'data' field
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_authors_api_exists(self):
        """Authors API should exist and return 200"""
        response = client.get("/api/authors/")
        assert response.status_code == 200
        data = response.json()
        # Modern API returns structured response with 'data' field
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_imports_api_imports_exists(self):
        """Import imports API should exist"""
        response = client.get("/api/imports/imports")
        assert response.status_code == 200
        data = response.json()
        # Import API returns different structure with 'imports' field
        assert "imports" in data
        assert isinstance(data["imports"], list)


class TestFrontendRoutes:
    """Test that frontend HTML routes exist"""
    
    def test_main_page(self):
        """Main dashboard should load"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_gallery_page(self):
        """Gallery page should load"""
        response = client.get("/gallery")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_import_page(self):
        """Import management page should load"""
        response = client.get("/import")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_authors_page(self):
        """Authors management page should load"""
        response = client.get("/authors")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


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
    
    def test_static_css_exists(self):
        """Main CSS file should be accessible"""
        response = client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]


if __name__ == "__main__":
    # Kjør testene direkte
    pytest.main([__file__, "-v"])
