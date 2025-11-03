"""
Unit tests for API endpoints
Tests synchronous endpoints with consistent error handling
"""
import pytest

class TestAuthorsAPI:
    """Test Authors API endpoints"""
    
    def test_list_authors_returns_paginated_response(self, authenticated_client):
        """GET /api/v1/authors/ should return paginated response"""
        response = authenticated_client.get("/api/v1/authors/", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have PaginatedResponse structure
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)
        assert "total" in data["meta"]
        assert "offset" in data["meta"]
        assert "limit" in data["meta"]
    
    def test_list_authors_with_pagination(self, authenticated_client):
        """Pagination parameters should work correctly"""
        response = authenticated_client.get("/api/v1/authors/?offset=0&limit=10", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["limit"] == 10
        assert data["meta"]["offset"] == 0
    
    def test_list_authors_invalid_pagination(self, authenticated_client):
        """Invalid pagination should return 422 validation error"""
        response = authenticated_client.get("/api/v1/authors/?offset=-1&limit=0", headers=authenticated_client.auth_headers)
        
        # FastAPI validation should catch this
        assert response.status_code == 422
    
    def test_create_author_success(self, authenticated_client):
        """POST /api/v1/authors/ should create new author"""
        author_data = {
            "name": "Test Author",
            "email": "test@example.com",
            "bio": "Test bio"
        }
        
        response = authenticated_client.post("/api/v1/authors/", json=author_data, headers=authenticated_client.auth_headers)
        
        # Debug the response if it fails
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        
        assert response.status_code == 201  # Created
        data = response.json()
        
        assert data["name"] == "Test Author"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_author_missing_required_field(self, authenticated_client):
        """POST without required field should return 422"""
        author_data = {
            "email": "test@example.com"
            # Missing required 'name'
        }
        
        response = authenticated_client.post("/api/v1/authors/", json=author_data, headers=authenticated_client.auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_author_invalid_email(self, authenticated_client):
        """POST with invalid email should return 400"""
        author_data = {
            "name": "Test Author",
            "email": "invalid-email"  # Invalid format
        }
        
        response = authenticated_client.post("/api/v1/authors/", json=author_data, headers=authenticated_client.auth_headers)
        
        # Service layer validation should catch this
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()
    
    def test_get_author_by_id_success(self, authenticated_client):
        """GET /api/v1/authors/{id} should return single author"""
        # First create an author
        author_data = {"name": "Get Test Author"}
        create_response = authenticated_client.post("/api/v1/authors/", json=author_data, headers=authenticated_client.auth_headers)
        author_id = create_response.json()["id"]
        
        # Then get it
        response = authenticated_client.get(f"/api/v1/authors/{author_id}", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == author_id
        assert data["name"] == "Get Test Author"
    
    def test_get_author_not_found(self, authenticated_client):
        """GET with non-existent ID should return 404"""
        response = authenticated_client.get("/api/v1/authors/99999", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_author_success(self, authenticated_client):
        """PUT /api/v1/authors/{id} should update author"""
        # Create author
        create_data = {"name": "Update Test"}
        create_response = authenticated_client.post("/api/v1/authors/", json=create_data, headers=authenticated_client.auth_headers)
        author_id = create_response.json()["id"]
        
        # Update it
        update_data = {
            "name": "Updated Name",
            "bio": "Updated bio"
        }
        response = authenticated_client.put(f"/api/v1/authors/{author_id}", json=update_data, headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
    
    def test_update_author_not_found(self, authenticated_client):
        """PUT with non-existent ID should return 404"""
        update_data = {"name": "New Name"}
        response = authenticated_client.put("/api/v1/authors/99999", json=update_data, headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
    
    def test_delete_author_success(self, authenticated_client):
        """DELETE /api/v1/authors/{id} should delete author"""
        # Create author
        create_data = {"name": "Delete Test"}
        create_response = authenticated_client.post("/api/v1/authors/", json=create_data, headers=authenticated_client.auth_headers)
        author_id = create_response.json()["id"]
        
        # Delete it
        response = authenticated_client.delete(f"/api/v1/authors/{author_id}", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use create_success_response format
        assert data["success"] is True
        assert "message" in data
        
        # Verify it's deleted
        get_response = authenticated_client.get(f"/api/v1/authors/{author_id}", headers=authenticated_client.auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_author_not_found(self, authenticated_client):
        """DELETE with non-existent ID should return 404"""
        response = authenticated_client.delete("/api/v1/authors/99999", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
    
    def test_error_response_format(self, authenticated_client):
        """All error responses should have consistent format"""
        response = authenticated_client.get("/api/v1/authors/99999", headers=authenticated_client.auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        
        # Should have detail field
        assert "detail" in data
        assert isinstance(data["detail"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
