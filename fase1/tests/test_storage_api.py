"""
Tests for Storage API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.services.storage_service import StorageResult, StorageProgress


client = TestClient(app)


class TestStorageAPIEndpoints:
    """Test storage-related API endpoints"""

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    def test_prepare_storage_success(self, mock_storage_service_class, mock_get_db):
        """Test successful storage preparation"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        
        # Mock async method
        async def mock_prepare_storage(import_id, session_name=None):
            return StorageResult(
                success=True,
                message="Storage prepared successfully",
                total_size_mb=150
            )
        mock_storage_service.prepare_storage = mock_prepare_storage
        
        # Make request
        response = client.post("/api/v1/import_sessions/1/prepare-storage")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_size_mb"] == 150
        assert data["import_id"] == 1

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    def test_prepare_storage_failure(self, mock_storage_service_class, mock_get_db):
        """Test storage preparation failure"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        
        # Mock async method to return failure
        async def mock_prepare_storage(import_id, session_name=None):
            return StorageResult(
                success=False,
                message="ImportSession not found"
            )
        mock_storage_service.prepare_storage = mock_prepare_storage
        
        # Make request
        response = client.post("/api/v1/import_sessions/999/prepare-storage")
        
        assert response.status_code == 400
        data = response.json()
        assert "ImportSession not found" in data["detail"]

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    @patch('src.models.import_session.ImportSession')
    def test_copy_to_permanent_storage_success(self, mock_import_session_class, mock_storage_service_class, mock_get_db):
        """Test successful start of storage copy"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_import_session = MagicMock()
        mock_import_session.storage_uuid = "test-uuid-123"
        mock_import_session.storage_path = "/test/storage/path"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        
        # Make request
        response = client.post("/api/v1/import_sessions/1/copy-to-permanent-storage")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["import_id"] == 1
        assert data["storage_uuid"] == "test-uuid-123"

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    @patch('src.models.import_session.ImportSession')
    def test_copy_to_permanent_storage_not_prepared(self, mock_import_session_class, mock_storage_service_class, mock_get_db):
        """Test storage copy when storage not prepared"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_import_session = MagicMock()
        mock_import_session.storage_uuid = None  # Not prepared
        mock_db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        
        # Make request
        response = client.post("/api/v1/import_sessions/1/copy-to-permanent-storage")
        
        assert response.status_code == 400
        data = response.json()
        assert "not prepared" in data["detail"].lower()

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    def test_get_storage_status_success(self, mock_storage_service_class, mock_get_db):
        """Test successful storage status retrieval"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        
        # Mock ImportSession
        mock_import_session = MagicMock()
        mock_import_session.storage_uuid = "test-uuid"
        mock_import_session.storage_path = "/test/path"
        mock_import_session.has_permanent_storage = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        # Mock storage progress
        progress = StorageProgress(
            session_id=1,
            status="completed",
            progress_percentage=100.0,
            files_processed=10,
            total_files=10,
            files_copied=10,
            files_skipped=0,
            total_size_mb=250,
            errors=[]
        )
        mock_storage_service.get_storage_status.return_value = progress
        
        # Make request
        response = client.get("/api/v1/import_sessions/1/storage-status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["import_id"] == 1
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100.0
        assert data["files_copied"] == 10
        assert data["total_size_mb"] == 250
        assert data["storage_uuid"] == "test-uuid"
        assert data["has_permanent_storage"] is True

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    def test_get_storage_status_not_found(self, mock_storage_service_class, mock_get_db):
        """Test storage status for non-existent ImportSession"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_storage_service.get_storage_status.return_value = None
        
        # Make request
        response = client.get("/api/v1/import_sessions/999/storage-status")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    def test_verify_storage_success(self, mock_storage_service_class, mock_get_db):
        """Test successful storage verification"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        
        # Mock verification result
        mock_storage_service.verify_storage_integrity.return_value = StorageResult(
            success=True,
            message="Verification passed: 10/10 files OK",
            files_copied=10,
            errors=[]
        )
        
        # Make request
        response = client.post("/api/v1/import_sessions/1/verify-storage")
        
        assert response.status_code == 200
        data = response.json()
        assert data["import_id"] == 1
        assert data["success"] is True
        assert data["files_verified"] == 10
        assert "verification passed" in data["message"].lower()

    @patch('src.api.v1.import_sessions.get_db_sync')
    @patch('src.services.storage_service.StorageService')
    def test_verify_storage_with_errors(self, mock_storage_service_class, mock_get_db):
        """Test storage verification with errors"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_storage_service = MagicMock()
        mock_storage_service_class.return_value = mock_storage_service
        
        # Mock verification result with errors
        mock_storage_service.verify_storage_integrity.return_value = StorageResult(
            success=False,
            message="Verification failed: 8/10 files OK",
            files_copied=8,
            errors=["Missing file: test1.jpg", "Size mismatch: test2.jpg"]
        )
        
        # Make request
        response = client.post("/api/v1/import_sessions/1/verify-storage")
        
        assert response.status_code == 200
        data = response.json()
        assert data["import_id"] == 1
        assert data["success"] is False
        assert data["files_verified"] == 8
        assert len(data["errors"]) == 2
        assert "verification failed" in data["message"].lower()


@pytest.mark.integration
class TestStorageAPIIntegration:
    """Integration tests for storage API endpoints"""

    def test_storage_endpoints_exist(self):
        """Test that all storage endpoints are accessible"""
        # Test prepare-storage endpoint exists
        response = client.post("/api/v1/import_sessions/1/prepare-storage")
        # Should not be 404 (endpoint exists), might be other error
        assert response.status_code != 404
        
        # Test copy-to-permanent-storage endpoint exists  
        response = client.post("/api/v1/import_sessions/1/copy-to-permanent-storage")
        assert response.status_code != 404
        
        # Test storage-status endpoint exists
        response = client.get("/api/v1/import_sessions/1/storage-status")
        assert response.status_code != 404
        
        # Test verify-storage endpoint exists
        response = client.post("/api/v1/import_sessions/1/verify-storage")
        assert response.status_code != 404


if __name__ == "__main__":
    pytest.main([__file__])