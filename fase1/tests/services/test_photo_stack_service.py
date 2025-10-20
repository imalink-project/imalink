"""
Unit tests for PhotoStack Service
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from services.photo_stack_service import PhotoStackService
from core.exceptions import NotFoundError, ValidationError
from schemas.common import PaginatedResponse


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def mock_stack_repo():
    """Mock PhotoStack repository"""
    return Mock()


@pytest.fixture
def photo_stack_service(mock_db, mock_stack_repo):
    """Create PhotoStackService with mocked dependencies"""
    with patch('services.photo_stack_service.PhotoStackRepository') as mock_repo_class:
        mock_repo_class.return_value = mock_stack_repo
        service = PhotoStackService(mock_db)
        service.stack_repo = mock_stack_repo
        return service


@pytest.fixture
def sample_stack_data():
    """Sample stack data for testing"""
    return {
        "id": 1,
        "cover_photo_hothash": "hash001",
        "stack_type": "panorama",
        "user_id": 1,
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:00:00"
    }


@pytest.fixture
def sample_stack_object():
    """Sample PhotoStack object for testing"""
    stack = Mock()
    stack.id = 1
    stack.cover_photo_hothash = "hash001"
    stack.stack_type = "panorama"
    stack.user_id = 1
    stack.created_at = Mock()
    stack.created_at.isoformat.return_value = "2024-01-01T10:00:00"
    stack.updated_at = Mock()
    stack.updated_at.isoformat.return_value = "2024-01-01T10:00:00"
    return stack


class TestPhotoStackService:
    """Test PhotoStack service business logic"""
    
    def test_get_stacks_success(self, photo_stack_service, mock_stack_repo):
        """Test successful pagination of stacks"""
        # Mock data
        mock_stacks = [Mock(), Mock()]
        mock_stack_repo.get_all.return_value = mock_stacks
        mock_stack_repo.count_all.return_value = 2
        mock_stack_repo.get_photo_count.return_value = 5
        
        # Mock stack attributes
        for i, stack in enumerate(mock_stacks):
            stack.id = i + 1
            stack.cover_photo_hothash = f"hash{i + 1}"
            stack.stack_type = "panorama"
            stack.created_at = Mock()
            stack.created_at.isoformat.return_value = "2024-01-01T10:00:00"
            stack.updated_at = Mock()
            stack.updated_at.isoformat.return_value = "2024-01-01T10:00:00"
        
        # Execute
        result = photo_stack_service.get_stacks(user_id=1, offset=0, limit=10)
        
        # Verify
        assert isinstance(result, PaginatedResponse)
        assert result.meta.total == 2
        assert len(result.data) == 2
        mock_stack_repo.get_all.assert_called_once_with(1, 0, 10)
        mock_stack_repo.count_all.assert_called_once_with(1)
    
    def test_get_stack_by_id_success(self, photo_stack_service, mock_stack_repo, sample_stack_object):
        """Test getting stack by ID with photos"""
        # Mock repository responses
        mock_stack_repo.get_by_id.return_value = sample_stack_object
        mock_stack_repo.get_photos_in_stack.return_value = ["hash001", "hash002"]
        mock_stack_repo.get_photo_count.return_value = 2
        
        # Execute
        result = photo_stack_service.get_stack_by_id(stack_id=1, user_id=1, include_photos=True)
        
        # Verify
        assert result["id"] == 1
        assert result["photo_hothashes"] == ["hash001", "hash002"]
        assert result["photo_count"] == 2
        mock_stack_repo.get_by_id.assert_called_once_with(1, 1)
        mock_stack_repo.get_photos_in_stack.assert_called_once_with(1, 1)
    
    def test_get_stack_by_id_not_found(self, photo_stack_service, mock_stack_repo):
        """Test getting non-existent stack raises exception"""
        mock_stack_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError) as exc_info:
            photo_stack_service.get_stack_by_id(stack_id=999, user_id=1)
        
        assert "PhotoStack" in str(exc_info.value)
        assert "999" in str(exc_info.value)
    
    def test_create_stack_success(self, photo_stack_service, mock_stack_repo, sample_stack_object):
        """Test creating stack - photos are added separately now"""
        # Mock repository 
        mock_stack_repo.create.return_value = sample_stack_object
        
        with patch.object(photo_stack_service, 'get_stack_by_id') as mock_get:
            mock_get.return_value = {"id": 1, "stack_type": "panorama"}
            
            # Execute - create stack without photos
            stack_data = {
                "stack_type": "panorama"
            }
            
            result = photo_stack_service.create_stack(stack_data=stack_data, user_id=1)
            
            # Verify
            assert result["id"] == 1
            mock_stack_repo.create.assert_called_once()
    
    def test_create_stack_invalid_stack_type(self, photo_stack_service):
        """Test creating stack with invalid stack type"""
        stack_data = {"stack_type": "a" * 51}  # Too long
        
        with pytest.raises(ValidationError) as exc_info:
            photo_stack_service.create_stack(stack_data=stack_data, user_id=1)
        
        assert "stack type" in str(exc_info.value).lower()
    
    def test_create_stack_with_cover_photo_validation(self, photo_stack_service, mock_stack_repo):
        """Test creating stack with cover photo validation"""
        stack_data = {
            "stack_type": "panorama",
            "cover_photo_hothash": "nonexistent"
        }
        
        mock_stack_repo.get_photos_in_stack.return_value = []
        
        with patch.object(photo_stack_service, '_validate_photos_exist', return_value=False):
            with pytest.raises(ValidationError) as exc_info:
                photo_stack_service.create_stack(stack_data=stack_data, user_id=1)
            
            assert "cover photo does not exist" in str(exc_info.value).lower()
    
    def test_update_stack_success(self, photo_stack_service, mock_stack_repo, sample_stack_object):
        """Test updating stack metadata"""
        # Mock repository responses
        mock_stack_repo.get_by_id.return_value = sample_stack_object
        mock_stack_repo.update.return_value = sample_stack_object
        
        with patch.object(photo_stack_service, 'get_stack_by_id') as mock_get:
            mock_get.return_value = {"id": 1, "stack_type": "updated"}
            
            # Execute
            update_data = {"stack_type": "updated"}
            result = photo_stack_service.update_stack(stack_id=1, update_data=update_data, user_id=1)
            
            # Verify
            assert result["id"] == 1
            mock_stack_repo.get_by_id.assert_called_once_with(1, 1)
            mock_stack_repo.update.assert_called_once_with(1, update_data, 1)
    
    def test_update_stack_not_found(self, photo_stack_service, mock_stack_repo):
        """Test updating non-existent stack"""
        mock_stack_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            photo_stack_service.update_stack(stack_id=999, update_data={}, user_id=1)
    
    def test_delete_stack_success(self, photo_stack_service, mock_stack_repo):
        """Test deleting stack"""
        mock_stack_repo.delete.return_value = True
        
        result = photo_stack_service.delete_stack(stack_id=1, user_id=1)
        
        assert result is True
        mock_stack_repo.delete.assert_called_once_with(1, 1)
    
    def test_delete_stack_not_found(self, photo_stack_service, mock_stack_repo):
        """Test deleting non-existent stack"""
        mock_stack_repo.delete.return_value = False
        
        with pytest.raises(NotFoundError):
            photo_stack_service.delete_stack(stack_id=999, user_id=1)
    
    def test_add_photo_to_stack_success(self, photo_stack_service, mock_stack_repo, sample_stack_object):
        """Test adding single photo to stack"""
        # Mock repository responses
        mock_stack_repo.get_by_id.return_value = sample_stack_object
        mock_stack_repo.add_photos.return_value = True
        
        with patch.object(photo_stack_service, '_validate_photos_exist', return_value=True):
            with patch.object(photo_stack_service, 'get_stack_by_id') as mock_get:
                mock_get.return_value = {"id": 1, "photo_count": 2}
                
                # Execute
                result = photo_stack_service.add_photo_to_stack(
                    stack_id=1, 
                    photo_hothash="new_hash",
                    user_id=1
                )
                
                # Verify
                assert "stack" in result
                mock_stack_repo.add_photos.assert_called_once_with(1, ["new_hash"], 1)
    
    def test_add_photo_stack_not_found(self, photo_stack_service, mock_stack_repo):
        """Test adding photo to non-existent stack"""
        mock_stack_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            photo_stack_service.add_photo_to_stack(stack_id=999, photo_hothash="hash", user_id=1)
    
    def test_remove_photo_from_stack_success(self, photo_stack_service, mock_stack_repo, sample_stack_object):
        """Test removing single photo from stack"""
        # Mock repository responses
        mock_stack_repo.get_by_id.return_value = sample_stack_object
        mock_stack_repo.remove_photos.return_value = True
        
        with patch.object(photo_stack_service, 'get_stack_by_id') as mock_get:
            mock_get.return_value = {"id": 1, "photo_count": 1}
            
            # Execute
            result = photo_stack_service.remove_photo_from_stack(
                stack_id=1,
                photo_hothash="hash_to_remove",
                user_id=1
            )
            
            # Verify
            assert "stack" in result
            mock_stack_repo.remove_photos.assert_called_once_with(1, ["hash_to_remove"], 1)
    
    def test_remove_photo_stack_not_found(self, photo_stack_service, mock_stack_repo):
        """Test removing photo from non-existent stack"""
        mock_stack_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            photo_stack_service.remove_photo_from_stack(stack_id=999, photo_hothash="hash", user_id=1)
    
    def test_get_photo_stack(self, photo_stack_service, mock_stack_repo):
        """Test getting stack containing specific photo"""
        from datetime import datetime
        
        # Mock repository response with single stack
        mock_stack = Mock()
        mock_stack.id = 1
        mock_stack.cover_photo_hothash = "hash001"
        mock_stack.stack_type = "panorama"
        mock_stack.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_stack.updated_at = datetime(2024, 1, 1, 10, 0, 0)
        
        mock_stack_repo.get_photo_stack.return_value = mock_stack
        mock_stack_repo.get_photo_count.return_value = 5
        
        # Execute
        result = photo_stack_service.get_photo_stack(
            photo_hothash="hash001", 
            user_id=1
        )
        
        # Verify
        assert result is not None
        assert result.id == 1
        assert result.stack_type == "panorama"
        assert result.photo_count == 5
        mock_stack_repo.get_photo_stack.assert_called_once_with("hash001", 1)
        mock_stack_repo.get_photo_count.assert_called_once_with(1, 1)
    
    def test_get_photo_stack_nonexistent(self, photo_stack_service, mock_stack_repo):
        """Test getting stack for photo not in any stack returns None"""
        mock_stack_repo.get_photo_stack.return_value = None
        
        # Execute - should return None for photo not in any stack
        result = photo_stack_service.get_photo_stack(
            photo_hothash="nonexistent", 
            user_id=1
        )
        
        # Verify
        assert result is None
        mock_stack_repo.get_photo_stack.assert_called_once_with("nonexistent", 1)
    
    def test_validate_stack_type_valid(self, photo_stack_service):
        """Test stack type validation with valid types"""
        valid_types = ["panorama", "burst", "animation", "hdr", "bracket"]
        
        for stack_type in valid_types:
            # Should not raise exception
            photo_stack_service._validate_stack_type(stack_type)
    
    def test_validate_stack_type_invalid(self, photo_stack_service):
        """Test stack type validation with invalid types"""
        # Too long
        with pytest.raises(ValidationError):
            photo_stack_service._validate_stack_type("a" * 51)
        
        # Invalid characters (if validation is added later)
        # This test can be extended when more validation is added
    
    def test_validate_photos_exist_success(self, photo_stack_service):
        """Test photo existence validation success"""
        mock_photo_repo = Mock()
        mock_photo_repo.get_by_hash.return_value = Mock()  # Photo exists
        photo_stack_service.photo_repo = mock_photo_repo
        
        result = photo_stack_service._validate_photos_exist(["hash001"], user_id=1)
        
        assert result is True
        mock_photo_repo.get_by_hash.assert_called_once_with("hash001", 1)
    
    def test_validate_photos_exist_failure(self, photo_stack_service):
        """Test photo existence validation failure"""
        mock_photo_repo = Mock()
        mock_photo_repo.get_by_hash.return_value = None  # Photo doesn't exist
        photo_stack_service.photo_repo = mock_photo_repo
        
        result = photo_stack_service._validate_photos_exist(["nonexistent"], user_id=1)
        
        assert result is False