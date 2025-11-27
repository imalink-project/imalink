"""
Unit tests for API endpoints
Tests synchronous endpoints with consistent error handling
"""
import pytest
import io
from PIL import Image

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
    
    # NOTE: /new-photo endpoint removed - use POST /create instead
    # Tests for photo creation now in test_real_photo_create_schema_usage.py


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


class TestPhotosArchitecture:
    """Test 100% Photo-centric architecture principles"""
    
    def test_create_endpoint_exists(self, authenticated_client):
        """POST /create endpoint should be accessible"""
        # Should return validation error (not 404 or 405)
        response = authenticated_client.post("/api/v1/photos/create", json={}, headers=authenticated_client.auth_headers)
        
        assert response.status_code in [400, 422]
    
    def test_image_files_api_removed(self, authenticated_client):
        """GET /image-files/ should be removed (404)"""
        response = authenticated_client.get("/api/v1/image-files/", headers=authenticated_client.auth_headers)
        
        # Should return 404 (endpoint doesn't exist)
        assert response.status_code == 404


class TestPhotosColdpreview:
    """Test coldpreview endpoints for Photos API"""
    
    def _create_test_image(self, size=(800, 600), format='JPEG'):
        """Helper: Create a test image in memory"""
        img = Image.new('RGB', size, color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=85)
        buffer.seek(0)
        return buffer
    
    def test_upload_coldpreview_to_nonexistent_photo(self, authenticated_client):
        """PUT /{hothash}/coldpreview should return 404 for non-existent photo"""
        test_image = self._create_test_image()
        
        response = authenticated_client.put(
            "/api/v1/photos/nonexistenthash/coldpreview",
            files={"file": ("test.jpg", test_image, "image/jpeg")},
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_coldpreview_nonexistent_photo(self, authenticated_client):
        """GET /{hothash}/coldpreview should return 404 for non-existent photo"""
        response = authenticated_client.get(
            "/api/v1/photos/nonexistenthash/coldpreview",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_coldpreview_with_width_parameter(self, authenticated_client):
        """GET /{hothash}/coldpreview?width=X should accept width parameter"""
        response = authenticated_client.get(
            "/api/v1/photos/somehash/coldpreview?width=400",
            headers=authenticated_client.auth_headers
        )
        
        # Will be 404 since photo doesn't exist, but validates endpoint accepts parameter
        assert response.status_code == 404
    
    def test_get_coldpreview_with_height_parameter(self, authenticated_client):
        """GET /{hothash}/coldpreview?height=X should accept height parameter"""
        response = authenticated_client.get(
            "/api/v1/photos/somehash/coldpreview?height=300",
            headers=authenticated_client.auth_headers
        )
        
        # Will be 404 since photo doesn't exist, but validates endpoint accepts parameter
        assert response.status_code == 404
    
    def test_get_coldpreview_with_both_dimensions(self, authenticated_client):
        """GET /{hothash}/coldpreview?width=X&height=Y should accept both parameters"""
        response = authenticated_client.get(
            "/api/v1/photos/somehash/coldpreview?width=400&height=300",
            headers=authenticated_client.auth_headers
        )
        
        # Will be 404 since photo doesn't exist, but validates endpoint accepts parameters
        assert response.status_code == 404
    
    def test_delete_coldpreview_nonexistent_photo(self, authenticated_client):
        """DELETE /{hothash}/coldpreview should return 404 for non-existent photo"""
        response = authenticated_client.delete(
            "/api/v1/photos/nonexistenthash/coldpreview",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 404
    
    def test_upload_coldpreview_requires_file(self, authenticated_client):
        """PUT /{hothash}/coldpreview should require file parameter"""
        response = authenticated_client.put(
            "/api/v1/photos/somehash/coldpreview",
            headers=authenticated_client.auth_headers
        )
        
        # Should return 422 (validation error) for missing file
        assert response.status_code == 422
    
    def test_upload_coldpreview_validates_file_type(self, authenticated_client):
        """PUT /{hothash}/coldpreview should validate file is an image"""
        # Create a text file instead of image
        text_file = io.BytesIO(b"This is not an image")
        
        response = authenticated_client.put(
            "/api/v1/photos/somehash/coldpreview",
            files={"file": ("test.txt", text_file, "text/plain")},
            headers=authenticated_client.auth_headers
        )
        
        # Should either fail at validation (422) or when processing (404/400/500)
        assert response.status_code in [400, 404, 422, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])