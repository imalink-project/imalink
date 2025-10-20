"""
Unit tests for API endpoints
Tests synchronous endpoints with consistent error handling
"""
import pytest

class TestImageFilesAPI:
    """Test Images API endpoints"""
    
    def test_list_images_returns_paginated_response(self, authenticated_client):
        """GET /api/v1/image-files/ should return paginated response"""
        response = authenticated_client.get("/api/v1/image-files/", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have PaginatedResponse structure
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)
    
    def test_list_images_with_pagination(self, authenticated_client):
        """Pagination parameters should work correctly"""
        response = authenticated_client.get("/api/v1/image-files/?offset=0&limit=50", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["limit"] == 50
        assert data["meta"]["offset"] == 0
    
    def test_get_image_not_found(self, authenticated_client):
        """GET with non-existent ID should return 404"""
        response = authenticated_client.get("/api/v1/image-files/99999", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_hotpreview_not_found(self, authenticated_client):
        """GET hotpreview for non-existent image should return 404"""
        response = authenticated_client.get("/api/v1/image-files/99999/hotpreview", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
    
    def test_create_image_without_data(self, authenticated_client):
        """POST without required data should return 422"""
        response = authenticated_client.post("/api/v1/image-files/", json={}, headers=authenticated_client.auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_image_missing_hotpreview(self, authenticated_client):
        """POST without hotpreview should return 422"""
        image_data = {
            "filename": "test.jpg",
            "file_size": 1000
            # Missing hotpreview
        }
        
        response = authenticated_client.post("/api/v1/image-files/", json=image_data, headers=authenticated_client.auth_headers)
        
        # Accept both 400 (service validation) and 422 (pydantic validation)
        assert response.status_code in [400, 422]


class TestImageFilesErrorHandling:
    """Test error handling consistency for Images API"""
    
    def test_not_found_error_format(self, authenticated_client):
        """NotFoundError should return 404 with detail"""
        response = authenticated_client.get("/api/v1/image-files/99999", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_validation_error_format(self, authenticated_client):
        """Validation errors should return 400 or 422 with detail"""
        response = authenticated_client.post("/api/v1/image-files/", json={}, headers=authenticated_client.auth_headers)
        
        assert response.status_code in [400, 422]
        assert "detail" in response.json()
    
    def test_invalid_pagination(self, authenticated_client):
        """Invalid pagination should return 422"""
        response = authenticated_client.get("/api/v1/image-files/?offset=-1&limit=0", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 422


class TestImageFilesArchitecture:
    """Test ImageFile-first architecture principles"""
    
    def test_images_endpoint_exists(self, authenticated_client):
        """Images endpoint should be accessible"""
        response = authenticated_client.get("/api/v1/image-files/", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
    
    def test_post_images_creates_photo(self, authenticated_client):
        """POST /images should auto-create Photo (architecture test)"""
        # This would require a full test with actual image data
        # For now, just verify the endpoint exists and accepts POST
        response = authenticated_client.post("/api/v1/image-files/", json={}, headers=authenticated_client.auth_headers)
        
        # Should return validation error (not 404 or 405)
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
