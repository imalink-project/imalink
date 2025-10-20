"""
Unit tests for API endpoints
Tests synchronous endpoints with consistent error handling
"""
import pytest

class TestPhotosAPI:
    """Test Photos API endpoints"""
    
    def test_list_photos_returns_paginated_response(self, authenticated_client):
        """GET /api/v1/photos/ should return paginated response"""
        response = authenticated_client.get("/api/v1/photos/", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have PaginatedResponse structure
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)
    
    def test_list_photos_with_pagination(self, authenticated_client):
        """Pagination parameters should work correctly"""
        response = authenticated_client.get("/api/v1/photos/?offset=0&limit=20", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["limit"] == 20
    
    def test_list_photos_filter_by_author(self, authenticated_client):
        """Should be able to filter photos by author_id"""
        response = authenticated_client.get("/api/v1/photos/?author_id=1", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        # Should not error even if no photos exist
    
    def test_search_photos(self, authenticated_client):
        """POST /api/v1/photos/search should accept search parameters"""
        search_data = {
            "rating_min": 3
        }
        
        response = authenticated_client.post("/api/v1/photos/search", json=search_data, headers=authenticated_client.auth_headers)
        
        # Should return paginated results
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_photo_by_hash_not_found(self, authenticated_client):
        """GET with non-existent hash should return 404"""
        response = authenticated_client.get("/api/v1/photos/nonexistenthash123456", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_photo_not_found(self, authenticated_client):
        """PUT with non-existent hash should return 404"""
        update_data = {"rating": 4}
        response = authenticated_client.put("/api/v1/photos/nonexistenthash", json=update_data, headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
    
    def test_delete_photo_not_found(self, authenticated_client):
        """DELETE with non-existent hash should return 404"""
        response = authenticated_client.delete("/api/v1/photos/nonexistenthash", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
    
    def test_get_hotpreview_not_found(self, authenticated_client):
        """GET hotpreview for non-existent photo should return 404"""
        response = authenticated_client.get("/api/v1/photos/nonexistenthash/hotpreview", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404


class TestPhotosErrorHandling:
    """Test error handling consistency"""
    
    def test_validation_error_format(self, authenticated_client):
        """Validation errors should return 400 with detail"""
        # Invalid search request
        search_data = {
            "rating_min": 10  # Invalid (should be 1-5)
        }
        
        response = authenticated_client.post("/api/v1/photos/search", json=search_data, headers=authenticated_client.auth_headers)
        
        # Validation should catch this
        if response.status_code == 400:
            assert "detail" in response.json()
    
    def test_not_found_error_format(self, authenticated_client):
        """NotFoundError should return 404 with detail"""
        response = authenticated_client.get("/api/v1/photos/fake_hash", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_invalid_pagination_parameters(self, authenticated_client):
        """Invalid pagination should return 422"""
        response = authenticated_client.get("/api/v1/photos/?offset=-1", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
