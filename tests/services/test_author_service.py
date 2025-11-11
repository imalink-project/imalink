"""
Unit tests for AuthorService
Tests synchronous service layer with consistent exception handling
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from services.author_service import AuthorService
from src.core.exceptions import NotFoundError, ValidationError
from schemas.requests.author_requests import AuthorCreateRequest, AuthorUpdateRequest


class TestAuthorService:
    """Test AuthorService business logic"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_author_repo(self):
        """Mock AuthorRepository"""
        return Mock()
    
    @pytest.fixture
    def author_service(self, mock_db, mock_author_repo):
        """Create AuthorService with mocked dependencies"""
        service = AuthorService(mock_db)
        service.author_repo = mock_author_repo
        return service
    
    def test_get_authors_returns_paginated_response(self, author_service, mock_author_repo):
        """get_authors should return PaginatedResponse"""
        # Mock repository response
        mock_author_repo.get_all.return_value = []
        mock_author_repo.count_all.return_value = 0
        
        result = author_service.get_authors(offset=0, limit=10)
        
        # Should call repository methods
        mock_author_repo.get_all.assert_called_once_with(0, 10)
        mock_author_repo.count_all.assert_called_once()
        
        # Should return PaginatedResponse structure
        assert hasattr(result, 'data')
        assert hasattr(result, 'meta')
    
    def test_get_author_by_id_not_found_raises_exception(self, author_service, mock_author_repo):
        """get_author_by_id should raise NotFoundError when author doesn't exist"""
        mock_author_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError) as exc_info:
            author_service.get_author_by_id(999)
        
        assert "Author" in str(exc_info.value)
        assert "999" in str(exc_info.value)
    
    def test_create_author_validates_name(self, author_service):
        """create_author should validate name format - tested at Pydantic schema level"""
        # Empty name is caught by Pydantic before reaching service
        from pydantic import ValidationError as PydanticValidationError
        with pytest.raises(PydanticValidationError) as exc_info:
            AuthorCreateRequest(name="")
        
        assert "name" in str(exc_info.value).lower()
    
    def test_create_author_validates_name_length(self, author_service):
        """create_author should validate minimum name length - tested at Pydantic schema level"""
        # Name too short is caught by Pydantic before reaching service
        from pydantic import ValidationError as PydanticValidationError
        with pytest.raises(PydanticValidationError) as exc_info:
            AuthorCreateRequest(name="")
        
        assert "at least 1 character" in str(exc_info.value).lower()
    
    def test_create_author_validates_email_format(self, author_service, mock_author_repo):
        """create_author should validate email format"""
        mock_author_repo.exists_by_name.return_value = False
        
        with pytest.raises(ValidationError) as exc_info:
            author_service.create_author(
                AuthorCreateRequest(name="Test", email="invalid-email"),
                user_id=1
            )
        
        assert "email" in str(exc_info.value).lower()
    
    def test_create_author_checks_for_duplicates(self, author_service, mock_author_repo):
        """create_author should check for duplicate names"""
        mock_author_repo.exists_by_name.return_value = True
        
        with pytest.raises(ValidationError) as exc_info:
            author_service.create_author(AuthorCreateRequest(name="Duplicate Name"), user_id=1)
        
        assert "already exists" in str(exc_info.value)
    
    def test_update_author_not_found_raises_exception(self, author_service, mock_author_repo):
        """update_author should raise NotFoundError when author doesn't exist"""
        mock_author_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            author_service.update_author(
                999, 
                AuthorUpdateRequest(name="Updated")
            )
    
    def test_delete_author_not_found_raises_exception(self, author_service, mock_author_repo):
        """delete_author should raise NotFoundError when author doesn't exist"""
        mock_author_repo.get_by_id.return_value = None  # Author not found
        
        with pytest.raises(NotFoundError):
            author_service.delete_author(999)


class TestAuthorServiceSync:
    """Test that AuthorService is synchronous"""
    
    def test_service_methods_are_not_async(self):
        """All service methods should be synchronous (not async)"""
        import inspect
        
        # Get all methods
        methods = [
            method for method in dir(AuthorService)
            if not method.startswith('_') and callable(getattr(AuthorService, method))
        ]
        
        # Check they're not async
        for method_name in methods:
            method = getattr(AuthorService, method_name)
            if callable(method):
                assert not inspect.iscoroutinefunction(method), \
                    f"Method {method_name} should not be async"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
