"""
Unit tests for API endpoints
Tests synchronous endpoints with consistent error handling
"""
import pytest

class TestImportSessionsAPI:
    """Test ImportSessions API endpoints"""
    
    def test_list_import_sessions(self, test_client):
        """GET /api/v1/import_sessions/ should return list"""
        response = test_client.get("/api/v1/import_sessions/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return ImportSessionListResponse
        assert "sessions" in data or "imports" in data or isinstance(data, list)
    
    def test_create_import_session_success(self, test_client):
        """POST /api/v1/import_sessions/ should create session"""
        session_data = {
            "title": "Test Import Session",
            "description": "Test description",
            "storage_location": "/test/path"
        }
        
        response = test_client.post("/api/v1/import_sessions/", json=session_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["title"] == "Test Import Session"
    
    def test_create_import_session_without_required_fields(self, test_client):
        """POST without fields should succeed (all fields optional)"""
        response = test_client.post("/api/v1/import_sessions/", json={})
        
        # All fields are optional, so empty request is valid
        assert response.status_code == 201
    
    def test_get_import_session_by_id_not_found(self, test_client):
        """GET with non-existent ID should return 404"""
        response = test_client.get("/api/v1/import_sessions/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_import_session_not_found(self, test_client):
        """PATCH with non-existent ID should return 404"""
        update_data = {"title": "Updated Title"}
        response = test_client.patch("/api/v1/import_sessions/99999", json=update_data)
        
        assert response.status_code == 404
    
    def test_delete_import_session_not_found(self, test_client):
        """DELETE with non-existent ID should return 404"""
        response = test_client.delete("/api/v1/import_sessions/99999")
        
        assert response.status_code == 404
    
    def test_delete_import_session_returns_success_response(self, test_client):
        """DELETE should use create_success_response format"""
        # First create a session
        session_data = {"title": "Delete Test"}
        create_response = test_client.post("/api/v1/import_sessions/", json=session_data)
        session_id = create_response.json()["id"]
        
        # Then delete it
        response = test_client.delete(f"/api/v1/import_sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use create_success_response format
        assert "success" in data
        assert "message" in data


class TestImportSessionsErrorHandling:
    """Test error handling consistency"""
    
    def test_not_found_error_format(self, test_client):
        """NotFoundError should return 404 with detail"""
        response = test_client.get("/api/v1/import_sessions/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_validation_error_format(self, test_client):
        """Validation errors should return 400 with detail"""
        # All fields are optional, so use invalid data type instead
        response = test_client.post("/api/v1/import_sessions/", json={"default_author_id": "not_an_int"})
        
        assert response.status_code in [400, 422]
        assert "detail" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
