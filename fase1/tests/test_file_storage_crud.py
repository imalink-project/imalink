"""
Simple CRUD tests for FileStorage model - Backend functionality only
"""
import pytest
from unittest.mock import patch
from datetime import datetime

# Add src to path for imports
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from models.file_storage import FileStorage


class TestFileStorageCRUD:
    """Test basic CRUD operations for FileStorage"""
    
    def test_create_storage_basic(self):
        """Test basic FileStorage creation"""
        base_path = "/media/photos"
        
        storage = FileStorage(base_path)
        
        # Test required fields are set
        assert storage.base_path == base_path
        assert storage.storage_uuid is not None
        assert len(storage.storage_uuid) == 36  # UUID4 format
        assert storage.directory_name is not None
        assert storage.full_path == f"{base_path}/{storage.directory_name}"
    
    def test_create_storage_with_metadata(self):
        """Test FileStorage creation with display name and description"""
        base_path = "/media/photos"
        display_name = "My Photo Collection"
        description = "Family photos from 2024"
        
        storage = FileStorage(
            base_path=base_path,
            display_name=display_name,
            description=description
        )
        
        assert storage.base_path == base_path
        assert storage.display_name == display_name
        assert storage.description == description
    
    def test_factory_method_create_storage(self):
        """Test FileStorage.create_storage factory method"""
        base_path = "/home/user/photos"
        display_name = "Test Storage"
        
        storage = FileStorage.create_storage(
            base_path=base_path,
            display_name=display_name
        )
        
        assert isinstance(storage, FileStorage)
        assert storage.base_path == base_path
        assert storage.display_name == display_name
        # Directory name should be valid format (imalink_YYYYMMDD_HHMMSS_uuid8)
        import re
        pattern = r"^imalink_\d{8}_\d{6}_[a-f0-9]{8}$"
        assert re.match(pattern, storage.directory_name)
    
    def test_storage_uuid_uniqueness(self):
        """Test that each storage gets a unique UUID"""
        storage1 = FileStorage("/path1")
        storage2 = FileStorage("/path2")
        
        assert storage1.storage_uuid != storage2.storage_uuid
        assert storage1.directory_name != storage2.directory_name


class TestDirectoryNaming:
    """Test directory name generation and validation"""
    
    def test_directory_name_format(self):
        """Test directory name follows correct format"""
        storage = FileStorage("/test/path")
        
        # Should match pattern: imalink_YYYYMMDD_HHMMSS_uuid8
        assert storage.directory_name.startswith("imalink_")
        
        # Test the pattern more specifically
        import re
        pattern = r'^imalink_\d{8}_\d{6}_[a-f0-9]{8}$'
        assert re.match(pattern, storage.directory_name) is not None
    
    @patch('models.file_storage.datetime')
    def test_directory_name_includes_timestamp(self, mock_datetime):
        """Test that directory name includes creation timestamp"""
        # Mock datetime to return specific time
        mock_now = datetime(2024, 10, 18, 14, 30, 52)
        mock_datetime.now.return_value = mock_now
        
        storage = FileStorage("/test/path")
        
        # Should include the mocked timestamp
        assert "20241018_143052" in storage.directory_name
    
    def test_directory_name_includes_uuid(self):
        """Test that directory name includes part of UUID"""
        storage = FileStorage("/test/path")
        
                # First 8 characters of UUID should be in directory name
        uuid_part = storage.storage_uuid[:8]
        assert uuid_part in storage.directory_name


class TestPathGeneration:
    """Test path generation"""
    
    def test_full_path_computation(self):
        """Test full path computation"""
        import os
        
        test_cases = [
            ("/media/photos", "/media/photos"),
            ("/media/photos/", "/media/photos"),
        ]
        
        for base_path, expected_base in test_cases:
            storage = FileStorage(base_path)
            expected_path = f"{expected_base}/{storage.directory_name}"
            assert storage.full_path == expected_path


class TestIndexPathGeneration:
    """Test JSON index file path generation for hybrid storage"""
    
    def test_master_index_path(self):
        """Test master index.json path generation"""
        base_path = "/media/external"
        storage = FileStorage(base_path)
        
        expected_path = f"{storage.full_path}/index.json"
        assert storage.master_index_path == expected_path
        assert storage.master_index_path.endswith("/index.json")
    
    def test_imports_index_dir(self):
        """Test imports directory path for session indexes"""
        base_path = "/media/photos"
        storage = FileStorage(base_path)
        
        expected_path = f"{storage.full_path}/imports"
        assert storage.imports_index_dir == expected_path
        assert storage.imports_index_dir.endswith("/imports")
    
    def test_session_index_path(self):
        """Test individual session index file paths"""
        storage = FileStorage("/test/path")
        
        session_id = 42
        expected_path = f"{storage.imports_index_dir}/session_{session_id}.json"
        
        assert storage.get_session_index_path(session_id) == expected_path
        assert "session_42.json" in storage.get_session_index_path(session_id)


class TestMasterIndexGeneration:
    """Test master index.json data generation for hybrid storage"""
    
    def test_generate_master_index_basic(self):
        """Test basic master index generation without sessions"""
        storage = FileStorage("/test/path", "Test Storage", "Test Description")
        
        index_data = storage.generate_master_index_data()
        
        # Verify structure
        assert "storage_info" in index_data
        assert "import_sessions" in index_data
        assert "imalink_version" in index_data
        
        # Verify storage info
        storage_info = index_data["storage_info"]
        assert storage_info["uuid"] == storage.storage_uuid
        assert storage_info["directory_name"] == str(storage.directory_name)
        assert storage_info["base_path"] == str(storage.base_path)
        assert storage_info["display_name"] == "Test Storage"
        assert storage_info["description"] == "Test Description"
        
        # Verify empty sessions
        assert index_data["import_sessions"] == []
        assert index_data["imalink_version"] == "2.0"


class TestStringRepresentation:
    """Test string representation"""
    
    def test_repr_basic(self):
        """Test __repr__ basic functionality"""
        storage = FileStorage("/test/path")
        
        repr_str = repr(storage)
        
        assert "FileStorage" in repr_str
        assert str(storage.directory_name) in repr_str


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_base_path(self):
        """Test handling of empty base path"""
        storage = FileStorage("")
        
        # Should still work, just with empty base
        assert storage.base_path == ""
        assert storage.directory_name is not None
        assert storage.full_path.startswith("/")  # Just directory name
    
    def test_very_long_base_path(self):
        """Test handling of very long base paths"""
        long_path = "/very/long/path/" + "subdir/" * 50  # Very long path
        
        storage = FileStorage(long_path)
        
        assert str(storage.base_path) == long_path
        assert storage.full_path.startswith(long_path.rstrip('/'))
    
    def test_special_characters_in_path(self):
        """Test handling of special characters in paths"""
        special_paths = [
            "/path with spaces/test",
            "/path-with-dashes/test",
            "/path_with_underscores/test",
            "/path.with.dots/test",
        ]
        
        for path in special_paths:
            storage = FileStorage(path)
            assert str(storage.base_path) == path
            assert storage.full_path.startswith(path.rstrip('/'))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])