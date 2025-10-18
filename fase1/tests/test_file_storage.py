"""
Unit tests for FileStorage model
Tests the hybrid storage architecture functionality including directory naming, 
accessibility tracking, index generation, and relationship management.
"""
import pytest
import uuid
import re
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.file_storage import FileStorage
from src.models.import_session import ImportSession
from src.models.author import Author


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_author(in_memory_db):
    """Create a sample author for import sessions"""
    author = Author(name="Test Author", email="test@example.com")
    in_memory_db.add(author)
    in_memory_db.commit()
    return author


class TestFileStorageCreation:
    """Test FileStorage model creation and initialization"""
    
    def test_create_basic_storage(self, in_memory_db):
        """Test basic FileStorage creation"""
        base_path = "/media/external-disk"
        
        storage = FileStorage(base_path=base_path)
        
        # Add to session and flush to get defaults applied
        in_memory_db.add(storage)
        in_memory_db.flush()
        
        assert storage.base_path == base_path
        assert storage.storage_uuid is not None
        assert len(storage.storage_uuid) == 36  # UUID4 format
        assert storage.directory_name is not None
        assert storage.full_path == f"{base_path}/{storage.directory_name}"
        assert storage.is_active is True  # default=True
        assert storage.is_accessible is False  # default=False
        assert storage.total_files == 0  # default=0
        assert storage.total_size_bytes == 0  # default=0
    
    def test_create_storage_with_metadata(self, in_memory_db):
        """Test FileStorage creation with display name and description"""
        base_path = "/media/photos"
        display_name = "My Photo Collection"
        description = "Family photos from 2024"
        
        storage = FileStorage(
            base_path=base_path,
            display_name=display_name,
            description=description
        )
        
        assert storage.display_name == display_name
        assert storage.description == description
    
    def test_factory_method_create_storage(self, in_memory_db):
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
        assert storage.is_directory_name_valid is True
    
    def test_storage_uuid_uniqueness(self, in_memory_db):
        """Test that each storage gets a unique UUID"""
        storage1 = FileStorage("/path1")
        storage2 = FileStorage("/path2")
        
        assert storage1.storage_uuid != storage2.storage_uuid
        assert len(storage1.storage_uuid) == 36
        assert len(storage2.storage_uuid) == 36


class TestDirectoryNaming:
    """Test directory naming patterns and validation"""
    
    def test_directory_name_format(self, in_memory_db):
        """Test directory name follows correct pattern"""
        storage = FileStorage("/test/path")
        
        # Pattern: imalink_YYYYMMDD_HHMMSS_uuid8
        pattern = r'^imalink_\d{8}_\d{6}_[a-f0-9]{8}$'
        assert re.match(pattern, storage.directory_name)
    
    def test_directory_name_validation_valid(self, in_memory_db):
        """Test valid directory name validation"""
        storage = FileStorage("/test/path")
        
        # Should be valid by default
        assert storage.is_directory_name_valid is True
    
    def test_directory_name_validation_invalid(self, in_memory_db):
        """Test invalid directory name validation"""
        storage = FileStorage("/test/path")
        
        # Corrupt the directory name
        storage.directory_name = "invalid_name"
        assert storage.is_directory_name_valid is False
        
        # Test various invalid patterns
        invalid_names = [
            "imalink_20241018_143052",  # Missing UUID
            "wrongprefix_20241018_143052_a1b2c3d4",  # Wrong prefix
            "imalink_2024101_143052_a1b2c3d4",  # Wrong date format
            "imalink_20241018_14305_a1b2c3d4",  # Wrong time format
            "imalink_20241018_143052_g1h2i3j4",  # Invalid hex characters
            "",  # Empty name
        ]
        
        for invalid_name in invalid_names:
            storage.directory_name = invalid_name
            assert storage.is_directory_name_valid is False, f"Should be invalid: {invalid_name}"
    
    @patch('src.models.file_storage.datetime')
    def test_directory_name_timestamp(self, mock_datetime, in_memory_db):
        """Test directory name includes correct timestamp"""
        # Mock datetime.now() to return predictable timestamp
        mock_now = datetime(2024, 10, 18, 14, 30, 52)
        mock_datetime.now.return_value = mock_now
        
        storage = FileStorage("/test/path")
        
        assert storage.directory_name.startswith("imalink_20241018_143052_")
    
    def test_full_path_generation(self, in_memory_db):
        """Test full path is correctly generated"""
        base_paths = [
            "/media/external-disk",
            "/media/external-disk/",  # With trailing slash
            "D:\\PhotoStorage",
            "D:\\PhotoStorage\\",  # With trailing slash
        ]
        
        for base_path in base_paths:
            storage = FileStorage(base_path)
            expected_path = f"{base_path.rstrip('/')}/{storage.directory_name}"
            assert storage.full_path == expected_path


class TestStorageProperties:
    """Test computed properties and utilities"""
    
    def test_storage_size_mb_zero(self, in_memory_db):
        """Test storage size calculation when empty"""
        storage = FileStorage("/test/path")
        
        assert storage.storage_size_mb == 0.0
    
    def test_storage_size_mb_calculation(self, in_memory_db):
        """Test storage size calculation with data"""
        storage = FileStorage("/test/path")
        
        # Set size to 1 GB (1,073,741,824 bytes)
        storage.total_size_bytes = 1073741824
        expected_mb = round(1073741824 / (1024 * 1024), 2)  # 1024.0 MB
        
        assert storage.storage_size_mb == expected_mb
        assert storage.storage_size_mb == 1024.0
    
    def test_storage_size_mb_fractional(self, in_memory_db):
        """Test storage size calculation with fractional MB"""
        storage = FileStorage("/test/path")
        
        # Set size to 1.5 MB (1,572,864 bytes)
        storage.total_size_bytes = 1572864
        expected_mb = round(1572864 / (1024 * 1024), 2)  # 1.5 MB
        
        assert storage.storage_size_mb == expected_mb
        assert storage.storage_size_mb == 1.5


class TestAccessibilityTracking:
    """Test storage accessibility status tracking"""
    
    def test_initial_accessibility_status(self, in_memory_db):
        """Test storage starts as not accessible"""
        storage = FileStorage("/test/path")
        
        # Add to session and flush to get defaults applied
        in_memory_db.add(storage)
        in_memory_db.flush()
        
        assert storage.is_accessible is False
        assert storage.last_accessed is None
    
    @patch('src.models.file_storage.datetime')
    def test_update_accessibility_true(self, mock_datetime, in_memory_db):
        """Test updating accessibility to accessible"""
        mock_now = datetime(2024, 10, 18, 14, 30, 52)
        mock_datetime.now.return_value = mock_now
        
        storage = FileStorage("/test/path")
        storage.update_accessibility(True)
        
        assert storage.is_accessible is True
        assert storage.last_accessed == mock_now
    
    def test_update_accessibility_false(self, in_memory_db):
        """Test updating accessibility to not accessible"""
        storage = FileStorage("/test/path")
        
        # First make it accessible
        storage.update_accessibility(True)
        old_last_accessed = storage.last_accessed
        
        # Then make it not accessible
        storage.update_accessibility(False)
        
        assert storage.is_accessible is False
        # last_accessed should remain unchanged
        assert storage.last_accessed == old_last_accessed


class TestStatisticsManagement:
    """Test storage statistics tracking"""
    
    def test_initial_statistics(self, in_memory_db):
        """Test initial statistics values"""
        storage = FileStorage("/test/path")
        
        # Add to session and flush to get defaults applied
        in_memory_db.add(storage)
        in_memory_db.flush()
        
        assert storage.total_files == 0
        assert storage.total_size_bytes == 0
    
    def test_update_statistics(self, in_memory_db):
        """Test updating storage statistics"""
        storage = FileStorage("/test/path")
        
        total_files = 150
        total_size = 2147483648  # 2 GB
        
        storage.update_statistics(total_files, total_size)
        
        assert storage.total_files == total_files
        assert storage.total_size_bytes == total_size
        assert storage.storage_size_mb == 2048.0  # 2 GB in MB


class TestIndexPathGeneration:
    """Test JSON index file path generation for hybrid storage"""
    
    def test_master_index_path(self, in_memory_db):
        """Test master index.json path generation"""
        base_path = "/media/external"
        storage = FileStorage(base_path)
        
        expected_path = f"{storage.full_path}/index.json"
        assert storage.master_index_path == expected_path
        assert storage.master_index_path.endswith("/index.json")
    
    def test_imports_index_dir(self, in_memory_db):
        """Test imports directory path for session indexes"""
        base_path = "/media/photos"
        storage = FileStorage(base_path)
        
        expected_path = f"{storage.full_path}/imports"
        assert storage.imports_index_dir == expected_path
        assert storage.imports_index_dir.endswith("/imports")
    
    def test_session_index_path(self, in_memory_db):
        """Test individual session index file paths"""
        storage = FileStorage("/test/path")
        
        session_id = 42
        expected_path = f"{storage.imports_index_dir}/session_{session_id}.json"
        
        assert storage.get_session_index_path(session_id) == expected_path
        assert "session_42.json" in storage.get_session_index_path(session_id)


class TestMasterIndexGeneration:
    """Test master index.json data generation for hybrid storage"""
    
    def test_generate_master_index_basic(self, in_memory_db):
        """Test basic master index generation without sessions"""
        storage = FileStorage("/test/path", "Test Storage", "Test Description")
        storage.total_files = 100
        storage.total_size_bytes = 1048576  # 1 MB
        storage.is_accessible = True
        
        index_data = storage.generate_master_index_data()
        
        # Verify structure
        assert "storage_info" in index_data
        assert "import_sessions" in index_data
        assert "imalink_version" in index_data
        
        # Verify storage info
        storage_info = index_data["storage_info"]
        assert storage_info["uuid"] == storage.storage_uuid
        assert storage_info["directory_name"] == storage.directory_name
        assert storage_info["base_path"] == storage.base_path
        assert storage_info["display_name"] == "Test Storage"
        assert storage_info["description"] == "Test Description"
        assert storage_info["is_accessible"] is True
        assert storage_info["total_files"] == 100
        assert storage_info["total_size_mb"] == 1.0
        
        # Verify empty sessions
        assert index_data["import_sessions"] == []
        assert index_data["imalink_version"] == "2.0"
    
    def test_generate_master_index_with_sessions(self, in_memory_db, sample_author):
        """Test master index generation with import sessions"""
        storage = FileStorage("/test/path")
        in_memory_db.add(storage)
        in_memory_db.flush()  # Get storage ID
        
        # Create import sessions
        session1 = ImportSession(
            title="Summer Vacation",
            description="Beach photos",
            file_storage_id=storage.id,
            default_author_id=sample_author.id
        )
        # Set imported_at directly during creation or after
        session1.imported_at = datetime(2024, 7, 15, 12, 0, 0)
        
        session2 = ImportSession(
            title="Birthday Party",
            description="Family celebration",
            file_storage_id=storage.id,
            default_author_id=sample_author.id
        )
        session2.imported_at = datetime(2024, 8, 20, 18, 30, 0)
        
        in_memory_db.add_all([session1, session2])
        in_memory_db.commit()
        
        # Refresh to load relationships
        in_memory_db.refresh(storage)
        
        index_data = storage.generate_master_index_data()
        
        # Verify sessions are included
        sessions = index_data["import_sessions"]
        assert len(sessions) == 2
        
        # Check first session
        session_data = next(s for s in sessions if s["title"] == "Summer Vacation")
        assert session_data["id"] == session1.id
        assert session_data["file_count"] == 0  # No image files created in test
        assert session_data["imported_at"] == "2024-07-15T12:00:00"
        assert session_data["index_file"] == f"imports/session_{session1.id}.json"
        
        # Check second session
        session_data = next(s for s in sessions if s["title"] == "Birthday Party")
        assert session_data["id"] == session2.id
        assert session_data["file_count"] == 0  # No image files created in test
        assert session_data["imported_at"] == "2024-08-20T18:30:00"
    
    def test_generate_master_index_null_handling(self, in_memory_db):
        """Test master index handles null values gracefully"""
        storage = FileStorage("/test/path")
        # Don't set optional fields
        storage.display_name = None
        storage.description = None
        storage.total_files = None
        storage.total_size_bytes = None
        
        index_data = storage.generate_master_index_data()
        
        storage_info = index_data["storage_info"]
        assert storage_info["display_name"] is None
        assert storage_info["description"] is None
        assert storage_info["total_files"] == 0  # Should default to 0
        assert storage_info["total_size_mb"] == 0.0  # Should default to 0.0


class TestDatabaseOperations:
    """Test database persistence and querying"""
    
    def test_save_and_retrieve_storage(self, in_memory_db):
        """Test saving and retrieving FileStorage from database"""
        original_storage = FileStorage(
            base_path="/media/test",
            display_name="Test Storage",
            description="Test description"
        )
        
        in_memory_db.add(original_storage)
        in_memory_db.commit()
        
        # Retrieve from database
        retrieved_storage = in_memory_db.query(FileStorage).filter_by(
            storage_uuid=original_storage.storage_uuid
        ).first()
        
        assert retrieved_storage is not None
        assert retrieved_storage.storage_uuid == original_storage.storage_uuid
        assert retrieved_storage.directory_name == original_storage.directory_name
        assert retrieved_storage.base_path == original_storage.base_path
        assert retrieved_storage.display_name == original_storage.display_name
        assert retrieved_storage.description == original_storage.description
    
    def test_storage_uuid_uniqueness_constraint(self, in_memory_db):
        """Test that storage_uuid must be unique"""
        uuid_value = str(uuid.uuid4())
        
        storage1 = FileStorage("/path1")
        storage1.storage_uuid = uuid_value
        
        storage2 = FileStorage("/path2")
        storage2.storage_uuid = uuid_value
        
        in_memory_db.add(storage1)
        in_memory_db.commit()
        
        # Adding second storage with same UUID should fail
        in_memory_db.add(storage2)
        
        with pytest.raises(Exception):  # IntegrityError or similar
            in_memory_db.commit()
    
    def test_directory_name_uniqueness_constraint(self, in_memory_db):
        """Test that directory_name must be unique"""
        storage1 = FileStorage("/path1")
        storage2 = FileStorage("/path2")
        
        # Force same directory name
        storage2.directory_name = storage1.directory_name
        
        in_memory_db.add(storage1)
        in_memory_db.commit()
        
        # Adding second storage with same directory name should fail
        in_memory_db.add(storage2)
        
        with pytest.raises(Exception):  # IntegrityError or similar
            in_memory_db.commit()


class TestRelationships:
    """Test relationships with other models"""
    
    def test_import_sessions_relationship(self, in_memory_db, sample_author):
        """Test relationship with ImportSession model"""
        storage = FileStorage("/test/path", "Test Storage")
        in_memory_db.add(storage)
        in_memory_db.flush()  # Get storage ID
        
        # Create import sessions
        session1 = ImportSession(
            title="Session 1",
            file_storage_id=storage.id,
            default_author_id=sample_author.id
        )
        session2 = ImportSession(
            title="Session 2", 
            file_storage_id=storage.id,
            default_author_id=sample_author.id
        )
        
        in_memory_db.add_all([session1, session2])
        in_memory_db.commit()
        
        # Test relationship loading
        in_memory_db.refresh(storage)
        assert len(storage.import_sessions) == 2
        assert session1 in storage.import_sessions
        assert session2 in storage.import_sessions
        
        # Test reverse relationship
        assert session1.file_storage == storage
        assert session2.file_storage == storage


class TestStringRepresentation:
    """Test string representation and formatting"""
    
    def test_repr_accessible(self, in_memory_db):
        """Test __repr__ when storage is accessible"""
        storage = FileStorage("/test/path")
        storage.id = 1
        storage.is_accessible = True
        
        repr_str = repr(storage)
        
        assert "FileStorage" in repr_str
        assert "id=1" in repr_str
        assert storage.directory_name in repr_str
        assert "accessible" in repr_str
        assert "not accessible" not in repr_str
    
    def test_repr_not_accessible(self, in_memory_db):
        """Test __repr__ when storage is not accessible"""
        storage = FileStorage("/test/path")
        storage.id = 2
        storage.is_accessible = False
        
        repr_str = repr(storage)
        
        assert "FileStorage" in repr_str
        assert "id=2" in repr_str
        assert storage.directory_name in repr_str
        assert "not accessible" in repr_str


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_base_path(self, in_memory_db):
        """Test handling of empty base path"""
        storage = FileStorage("")
        
        # Should still generate directory name and UUID
        assert storage.directory_name is not None
        assert storage.storage_uuid is not None
        assert storage.full_path == f"/{storage.directory_name}"
    
    def test_very_long_base_path(self, in_memory_db):
        """Test handling of very long base paths"""
        long_path = "/very/long/path/" + "subdir/" * 50  # Very long path
        
        storage = FileStorage(long_path)
        
        assert storage.base_path == long_path
        assert storage.full_path.startswith(long_path.rstrip('/'))
    
    def test_special_characters_in_path(self, in_memory_db):
        """Test handling of special characters in paths"""
        special_paths = [
            "/path with spaces/test",
            "/path-with-dashes/test",
            "/path_with_underscores/test",
            "/path.with.dots/test",
        ]
        
        for path in special_paths:
            storage = FileStorage(path)
            assert storage.base_path == path
            assert storage.full_path.startswith(path.rstrip('/'))
    
    def test_negative_statistics(self, in_memory_db):
        """Test handling of negative statistics values"""
        storage = FileStorage("/test/path")
        
        # Should handle negative values (though they shouldn't occur normally)
        storage.update_statistics(-1, -1000)
        
        assert storage.total_files == -1
        assert storage.total_size_bytes == -1000
        # Size in MB should handle negative values (allow for -0.0 floating point behavior)
        assert storage.storage_size_mb <= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])