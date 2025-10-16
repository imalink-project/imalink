"""
Tests for Storage Service functionality
"""
import pytest
import tempfile
import shutil
import os
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.services.storage_service import StorageService, StorageResult, StorageProgress
from src.models.import_session import ImportSession
from src.models.image import Image


class TestStorageService:
    """Test StorageService functionality"""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage directory for tests"""
        temp_dir = tempfile.mkdtemp(prefix="imalink_storage_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def temp_source_files(self):
        """Create temporary source files for testing"""
        temp_dir = tempfile.mkdtemp(prefix="imalink_source_test_")
        
        # Create test files
        test_files = []
        for i in range(3):
            file_path = Path(temp_dir) / f"test_image_{i}.jpg"
            file_path.write_text(f"test content {i}" * 100)  # Create some content
            test_files.append(str(file_path))
        
        yield test_files
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def storage_service(self, mock_db_session, temp_storage_path):
        """Create StorageService instance with test configuration"""
        return StorageService(mock_db_session, temp_storage_path)

    @pytest.fixture
    def mock_import_session(self):
        """Create mock ImportSession"""
        session = MagicMock(spec=ImportSession)
        session.id = 1
        session.source_path = "/test/source"
        session.total_files_found = 3
        session.storage_uuid = None
        session.storage_path = None
        session.copy_status = "not_started"
        session.files_copied = 0
        session.files_copy_skipped = 0
        session.storage_errors_count = 0
        session.storage_size_mb = 0
        return session

    @pytest.fixture
    def mock_images(self, temp_source_files):
        """Create mock Image objects"""
        images = []
        for i, file_path in enumerate(temp_source_files):
            image = MagicMock(spec=Image)
            image.id = i + 1
            image.filename = f"test_image_{i}.jpg"
            image.file_path = file_path
            images.append(image)
        return images

    def test_generate_storage_uuid(self, storage_service):
        """Test UUID generation"""
        uuid_str = storage_service.generate_storage_uuid()
        
        # Should be valid UUID string
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36
        
        # Should parse as UUID
        parsed_uuid = uuid.UUID(uuid_str)
        assert str(parsed_uuid) == uuid_str

    def test_generate_storage_path_with_session_name(self, storage_service, temp_storage_path):
        """Test storage path generation with session name"""
        test_uuid = "12345678-1234-1234-1234-123456789012"
        session_name = "test_session"
        
        path = storage_service.generate_storage_path(test_uuid, session_name)
        
        expected_path = f"{temp_storage_path}/test_session_12345678"
        assert path == expected_path

    def test_generate_storage_path_without_session_name(self, storage_service, temp_storage_path):
        """Test storage path generation without session name"""
        test_uuid = "12345678-1234-1234-1234-123456789012"
        
        path = storage_service.generate_storage_path(test_uuid)
        
        expected_path = f"{temp_storage_path}/{test_uuid}"
        assert path == expected_path

    def test_validate_storage_path_success(self, storage_service, temp_storage_path):
        """Test storage path validation success"""
        test_path = f"{temp_storage_path}/valid_path"
        
        is_valid, message = storage_service.validate_storage_path(test_path)
        
        assert is_valid is True
        assert "valid" in message.lower()
        assert os.path.exists(test_path)

    def test_validate_storage_path_invalid_parent(self, storage_service):
        """Test storage path validation with invalid parent directory"""
        invalid_path = "/nonexistent/parent/directory/storage"
        
        # Mock to simulate permission error
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            is_valid, message = storage_service.validate_storage_path(invalid_path)
        
        assert is_valid is False
        assert "cannot create" in message.lower()

    def test_get_import_session_files(self, storage_service, mock_import_session, mock_images):
        """Test getting files from import session"""
        # Setup mock database query
        storage_service.db.query.return_value.filter.return_value.all.return_value = mock_images
        
        files = storage_service.get_import_session_files(mock_import_session)
        
        assert len(files) == 3
        for i, file_info in enumerate(files):
            assert file_info['filename'] == f"test_image_{i}.jpg"
            assert 'source_path' in file_info
            assert 'size_bytes' in file_info
            assert 'image_id' in file_info

    def test_calculate_total_size(self, storage_service):
        """Test total size calculation"""
        files = [
            {'size_bytes': 1024 * 1024},      # 1 MB
            {'size_bytes': 2 * 1024 * 1024},  # 2 MB
            {'size_bytes': 512 * 1024}        # 0.5 MB
        ]
        
        total_mb = storage_service.calculate_total_size(files)
        
        assert total_mb == 3  # Should round down 3.5 MB to 3 MB

    @pytest.mark.asyncio
    async def test_prepare_storage_success(self, storage_service, mock_import_session):
        """Test successful storage preparation"""
        # Setup mock database
        storage_service.db.query.return_value.filter.return_value.first.return_value = mock_import_session
        storage_service.db.query.return_value.filter.return_value.all.return_value = []  # No files for simplicity
        
        result = await storage_service.prepare_storage(1, "test_session")
        
        assert result.success is True
        assert "prepared" in result.message.lower()
        assert mock_import_session.storage_uuid is not None
        assert mock_import_session.storage_path is not None
        assert mock_import_session.copy_status == "not_started"

    @pytest.mark.asyncio
    async def test_prepare_storage_already_configured(self, storage_service, mock_import_session):
        """Test storage preparation when already configured"""
        # Setup import session as already having storage
        mock_import_session.storage_uuid = "existing-uuid"
        storage_service.db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        result = await storage_service.prepare_storage(1)
        
        assert result.success is False
        assert "already has storage" in result.message.lower()

    @pytest.mark.asyncio
    async def test_prepare_storage_import_not_found(self, storage_service):
        """Test storage preparation when ImportSession not found"""
        storage_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = await storage_service.prepare_storage(999)
        
        assert result.success is False
        assert "not found" in result.message.lower()

    @pytest.mark.asyncio
    async def test_copy_files_to_storage_success(self, storage_service, mock_import_session, mock_images, temp_storage_path):
        """Test successful file copy to storage"""
        # Setup import session with storage configured
        mock_import_session.storage_uuid = "test-uuid"
        mock_import_session.storage_path = f"{temp_storage_path}/test_storage"
        mock_import_session.copy_status = "not_started"
        
        # Setup mock database
        storage_service.db.query.return_value.filter.return_value.first.return_value = mock_import_session
        storage_service.db.query.return_value.filter.return_value.all.return_value = mock_images
        
        result = await storage_service.copy_files_to_storage(1)
        
        assert result.success is True
        assert result.files_copied == 3
        assert result.files_skipped == 0
        assert mock_import_session.copy_status == "completed"

    @pytest.mark.asyncio
    async def test_copy_files_already_completed(self, storage_service, mock_import_session):
        """Test copy when already completed"""
        mock_import_session.storage_uuid = "test-uuid"
        mock_import_session.storage_path = "/test/path"
        mock_import_session.copy_status = "completed"
        mock_import_session.files_copied = 5
        mock_import_session.storage_size_mb = 100
        
        storage_service.db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        result = await storage_service.copy_files_to_storage(1)
        
        assert result.success is True
        assert "already completed" in result.message.lower()
        assert result.files_copied == 5

    def test_get_storage_status_active_operation(self, storage_service):
        """Test getting storage status for active operation"""
        # Setup active operation
        progress = StorageProgress(
            session_id=1,
            status="in_progress",
            files_processed=2,
            total_files=5
        )
        storage_service._active_operations[1] = progress
        
        result = storage_service.get_storage_status(1)
        
        assert result == progress
        assert result.status == "in_progress"

    def test_get_storage_status_from_database(self, storage_service, mock_import_session):
        """Test getting storage status from database"""
        mock_import_session.copy_status = "completed"
        mock_import_session.files_copied = 10
        mock_import_session.total_files_found = 10
        
        storage_service.db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        result = storage_service.get_storage_status(1)
        
        assert result is not None
        assert result.status == "completed"
        assert result.files_copied == 10

    def test_verify_storage_integrity_success(self, storage_service, mock_import_session, temp_storage_path, temp_source_files):
        """Test successful storage integrity verification"""
        # Setup storage path with files
        storage_path = Path(temp_storage_path) / "test_storage"
        storage_path.mkdir()
        
        mock_import_session.storage_path = str(storage_path)
        storage_service.db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        # Create mock files in storage that match source files
        mock_files = []
        for i, source_file in enumerate(temp_source_files):
            filename = f"test_image_{i}.jpg"
            size = os.path.getsize(source_file)
            
            # Copy file to storage
            dest_file = storage_path / filename
            shutil.copy2(source_file, dest_file)
            
            mock_files.append({
                'filename': filename,
                'source_path': source_file,
                'size_bytes': size,
                'image_id': i + 1
            })
        
        # Mock the get_import_session_files method
        with patch.object(storage_service, 'get_import_session_files', return_value=mock_files):
            result = storage_service.verify_storage_integrity(1)
        
        assert result.success is True
        assert result.files_copied == 3
        assert len(result.errors) == 0

    def test_verify_storage_integrity_missing_files(self, storage_service, mock_import_session, temp_storage_path):
        """Test storage verification with missing files"""
        storage_path = Path(temp_storage_path) / "test_storage"
        storage_path.mkdir()
        
        mock_import_session.storage_path = str(storage_path)
        storage_service.db.query.return_value.filter.return_value.first.return_value = mock_import_session
        
        # Mock files that don't exist in storage
        mock_files = [
            {'filename': 'missing.jpg', 'source_path': '/test/missing.jpg', 'size_bytes': 1000, 'image_id': 1}
        ]
        
        with patch.object(storage_service, 'get_import_session_files', return_value=mock_files):
            result = storage_service.verify_storage_integrity(1)
        
        assert result.success is False
        assert len(result.errors) == 1
        assert "missing" in result.errors[0].lower()


@pytest.mark.integration
class TestStorageServiceIntegration:
    """Integration tests for StorageService with real filesystem operations"""

    @pytest.fixture
    def real_temp_dirs(self):
        """Create real temporary directories for integration tests"""
        source_dir = tempfile.mkdtemp(prefix="imalink_source_")
        storage_dir = tempfile.mkdtemp(prefix="imalink_storage_")
        
        # Create test files in source
        test_files = []
        for i in range(2):
            file_path = Path(source_dir) / f"integration_test_{i}.jpg"
            content = f"Integration test content {i}" * 200
            file_path.write_text(content)
            test_files.append(str(file_path))
        
        yield {
            'source_dir': source_dir,
            'storage_dir': storage_dir,
            'test_files': test_files
        }
        
        # Cleanup
        shutil.rmtree(source_dir, ignore_errors=True)
        shutil.rmtree(storage_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_full_storage_workflow(self, real_temp_dirs, mock_db_session):
        """Test complete storage workflow from preparation to verification"""
        # Setup
        storage_service = StorageService(mock_db_session, real_temp_dirs['storage_dir'])
        
        # Mock ImportSession and Images
        import_session = MagicMock(spec=ImportSession)
        import_session.id = 1
        import_session.storage_uuid = None
        import_session.storage_path = None
        import_session.copy_status = "not_started"
        import_session.total_files_found = 2
        
        images = []
        for i, file_path in enumerate(real_temp_dirs['test_files']):
            image = MagicMock(spec=Image)
            image.id = i + 1
            image.filename = f"integration_test_{i}.jpg"
            image.file_path = file_path
            images.append(image)
        
        # Setup database mocks
        mock_db_session.query.return_value.filter.return_value.first.return_value = import_session
        mock_db_session.query.return_value.filter.return_value.all.return_value = images
        
        # Step 1: Prepare storage
        prepare_result = await storage_service.prepare_storage(1, "integration_test")
        assert prepare_result.success is True
        assert import_session.storage_uuid is not None
        assert import_session.storage_path is not None
        
        # Step 2: Copy files to storage
        copy_result = await storage_service.copy_files_to_storage(1)
        assert copy_result.success is True
        assert copy_result.files_copied == 2
        
        # Step 3: Verify storage integrity
        verify_result = storage_service.verify_storage_integrity(1)
        assert verify_result.success is True
        assert verify_result.files_copied == 2
        
        # Check that files actually exist in storage
        storage_path = Path(import_session.storage_path)
        assert storage_path.exists()
        assert (storage_path / "integration_test_0.jpg").exists()
        assert (storage_path / "integration_test_1.jpg").exists()


if __name__ == "__main__":
    pytest.main([__file__])