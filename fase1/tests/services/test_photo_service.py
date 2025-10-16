"""
Unit tests for PhotoService  
Tests synchronous service layer with consistent exception handling
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from services.photo_service import PhotoService
from core.exceptions import NotFoundError, ValidationError
from schemas.photo_schemas import PhotoUpdateRequest


class TestPhotoService:
    """Test PhotoService business logic"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_photo_repo(self):
        """Mock PhotoRepository"""
        return Mock()
    
    @pytest.fixture
    def photo_service(self, mock_db, mock_photo_repo):
        """Create PhotoService with mocked dependencies"""
        service = PhotoService(mock_db)
        service.photo_repo = mock_photo_repo
        return service
    
    def test_get_photos_returns_paginated_response(self, photo_service, mock_photo_repo):
        """get_photos should return PaginatedResponse"""
        mock_photo_repo.get_photos.return_value = []
        mock_photo_repo.count_photos.return_value = 0
        
        result = photo_service.get_photos(offset=0, limit=20)
        
        # Should call repository methods
        mock_photo_repo.get_photos.assert_called_once()
        mock_photo_repo.count_photos.assert_called_once()
        
        # Should return PaginatedResponse structure
        assert hasattr(result, 'data')
        assert hasattr(result, 'meta')
    
    def test_get_photo_by_hash_not_found_raises_exception(self, photo_service, mock_photo_repo):
        """get_photo_by_hash should raise NotFoundError when photo doesn't exist"""
        mock_photo_repo.get_by_hash.return_value = None
        
        with pytest.raises(NotFoundError) as exc_info:
            photo_service.get_photo_by_hash("nonexistenthash")
        
        assert "Photo" in str(exc_info.value)
    
    def test_update_photo_validates_tags(self, photo_service, mock_photo_repo):
        """update_photo should validate tags format"""
        # Mock existing photo
        mock_photo = Mock()
        mock_photo_repo.get_by_hash.return_value = mock_photo
        
        # Invalid tags should raise ValidationError
        invalid_tags = ["tag1", "tag with spaces that is way too long" * 10]
        
        with pytest.raises(ValidationError):
            photo_service.update_photo(
                "somehash",
                PhotoUpdateRequest(tags=invalid_tags)
            )
    
    def test_delete_photo_not_found_raises_exception(self, photo_service, mock_photo_repo):
        """delete_photo should raise NotFoundError when photo doesn't exist"""
        mock_photo_repo.get_by_hash.return_value = None
        
        with pytest.raises(NotFoundError):
            photo_service.delete_photo("nonexistenthash")
    
    def test_search_photos_returns_paginated_response(self, photo_service, mock_photo_repo):
        """search_photos should return PaginatedResponse"""
        mock_photo_repo.get_photos.return_value = []
        mock_photo_repo.count_photos.return_value = 0
        
        from schemas.photo_schemas import PhotoSearchRequest
        search_params = PhotoSearchRequest(tags=["test"])
        
        result = photo_service.search_photos(search_params)
        
        # Should return PaginatedResponse structure
        assert hasattr(result, 'data')
        assert hasattr(result, 'meta')


class TestPhotoServiceSync:
    """Test that PhotoService is synchronous"""
    
    def test_service_methods_are_not_async(self):
        """All service methods should be synchronous (not async)"""
        import inspect
        
        # Get all methods
        methods = [
            method for method in dir(PhotoService)
            if not method.startswith('_') and callable(getattr(PhotoService, method))
        ]
        
        # Check they're not async
        for method_name in methods:
            method = getattr(PhotoService, method_name)
            if callable(method):
                assert not inspect.iscoroutinefunction(method), \
                    f"Method {method_name} should not be async"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
