"""
Unit tests for ImportSession services
Tests import process orchestration, file scanning, and Photo/Image creation workflow
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from services.import_sessions_background_service import ImportSessionsBackgroundService
from repositories.import_session_repository import ImportSessionRepository
from models.import_session import ImportSession
from models.photo import Photo
from models.image import Image
from models.base import Base


class TestImportSessionService:
    """Test suite for ImportSession services"""
    
    @pytest.fixture(scope="class")
    def test_images_dir(self):
        """Path to test images directory"""
        return Path(__file__).parent.parent.parent / 'test_user_files' / 'images'
    
    @pytest.fixture
    def in_memory_db(self):
        """In-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    @pytest.fixture
    def import_service(self, in_memory_db):
        """ImportSessionsBackgroundService instance"""
        return ImportSessionsBackgroundService(db=in_memory_db)
    
    @pytest.fixture
    def temp_image_dir(self, test_images_dir):
        """Temporary directory with copies of test images"""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Copy test images to temporary directory
        for category_dir in test_images_dir.iterdir():
            if category_dir.is_dir():
                dest_dir = temp_dir / category_dir.name
                shutil.copytree(category_dir, dest_dir)
        
        yield str(temp_dir)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_import_session(self, in_memory_db, temp_image_dir):
        """Sample import session for testing"""
        import_repo = ImportSessionRepository(in_memory_db)
        
        import_session = ImportSession(
            source_path=temp_image_dir,
            source_description="Test import session",
            status="pending",
            total_files_found=0,
            images_imported=0,
            duplicates_skipped=0,
            errors_count=0
        )
        
        in_memory_db.add(import_session)
        in_memory_db.commit()
        
        return import_session


class TestFileScanning(TestImportSessionService):
    """Test file scanning and grouping functionality"""
    
    def test_find_image_files(self, import_service, temp_image_dir):
        """Test finding image files in directory"""
        image_files = import_service._find_image_files(temp_image_dir)
        
        assert len(image_files) > 0
        
        # Should find all test images
        expected_extensions = {'.jpg', '.jpeg', '.dng'}
        found_extensions = {f.suffix.lower() for f in image_files}
        
        assert found_extensions.intersection(expected_extensions)
        
        # All should be valid paths
        for file_path in image_files:
            assert file_path.exists()
            assert file_path.is_file()
        
        print(f"✅ Found {len(image_files)} image files")
        for ext in found_extensions:
            count = sum(1 for f in image_files if f.suffix.lower() == ext)
            print(f"   {ext.upper()}: {count} files")
    
    def test_group_raw_jpeg_pairs(self, import_service, temp_image_dir):
        """Test grouping RAW/JPEG pairs by basename"""
        image_files = import_service._find_image_files(temp_image_dir)
        file_groups = import_service._group_raw_jpeg_pairs(image_files)
        
        assert len(file_groups) > 0
        
        # Check that pairing logic works
        for basename, files in file_groups.items():
            assert len(files) >= 1  # At least one file per group
            
            # All files in group should have same basename
            for file_path in files:
                assert file_path.stem == basename
        
        # Look for actual pairs in test data
        pairs = {basename: files for basename, files in file_groups.items() if len(files) > 1}
        
        if pairs:
            print(f"✅ Found {len(pairs)} file pairs:")
            for basename, files in pairs.items():
                extensions = [f.suffix.lower() for f in files]
                print(f"   {basename}: {extensions}")
        else:
            print("ℹ️  No file pairs found in test data")
        
        return file_groups
    
    def test_find_files_empty_directory(self, import_service):
        """Test handling of empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_files = import_service._find_image_files(temp_dir)
            assert len(image_files) == 0
    
    def test_find_files_nonexistent_directory(self, import_service):
        """Test handling of non-existent directory"""
        nonexistent_dir = "/path/to/nonexistent/directory"
        
        with pytest.raises(ValueError):
            import_service._find_image_files(nonexistent_dir)


class TestPhotoGroupProcessing(TestImportSessionService):
    """Test processing of photo groups (file pairs/singles)"""
    
    def test_process_single_jpeg(self, import_service, sample_import_session, temp_image_dir):
        """Test processing single JPEG file"""
        # Find single JPEG files
        image_files = import_service._find_image_files(temp_image_dir)
        file_groups = import_service._group_raw_jpeg_pairs(image_files)
        
        # Find a single file group (not a pair)
        single_groups = {name: files for name, files in file_groups.items() if len(files) == 1}
        
        if not single_groups:
            pytest.skip("No single files found in test data")
        
        # Process first single file
        basename, files = next(iter(single_groups.items()))
        
        success = import_service._process_photo_group(files, sample_import_session.id)
        
        assert success is True
        
        # Verify Photo was created
        photos = import_service.db.query(Photo).all()
        assert len(photos) >= 1
        
        # Verify Image was created
        images = import_service.db.query(Image).all()
        assert len(images) >= 1
        
        print(f"✅ Processed single file: {files[0].name}")
    
    def test_process_jpeg_dng_pair(self, import_service, sample_import_session, temp_image_dir):
        """Test processing JPEG+DNG pair"""
        image_files = import_service._find_image_files(temp_image_dir)
        file_groups = import_service._group_raw_jpeg_pairs(image_files)
        
        # Find file pairs
        pairs = {name: files for name, files in file_groups.items() if len(files) > 1}
        
        if not pairs:
            pytest.skip("No file pairs found in test data")
        
        # Process first pair
        basename, files = next(iter(pairs.items()))
        
        success = import_service._process_photo_group(files, sample_import_session.id)
        
        assert success is True
        
        # Verify one Photo was created for the pair
        photos = import_service.db.query(Photo).filter_by(import_session_id=sample_import_session.id).all()
        assert len(photos) >= 1
        
        # Find the photo for this pair
        for photo in photos:
            if len(photo.files) > 1:  # This is our pair
                assert len(photo.files) == 2
                
                # Verify both files link to same photo
                hash_values = {img.hothash for img in photo.files}
                assert len(hash_values) == 1  # Same hash
                
                # Verify different file extensions
                extensions = {Path(img.filename).suffix.lower() for img in photo.files}
                assert len(extensions) == 2  # Different extensions
                
                print(f"✅ Processed pair: {extensions}")
                break
        else:
            pytest.fail("No photo pair found after processing")


class TestFullImportProcess(TestImportSessionService):
    """Test complete import process from start to finish"""
    
    def test_process_import_complete_workflow(self, import_service, sample_import_session, temp_image_dir):
        """Test complete import workflow"""
        import_id = sample_import_session.id
        
        # Run complete import process
        success = import_service.process_directory_import(import_id, temp_image_dir)
        
        assert success is True
        
        # Verify import session was updated
        updated_session = import_service.db.query(ImportSession).get(import_id)
        
        assert updated_session.status == "completed"
        assert updated_session.total_files_found > 0
        assert updated_session.images_imported > 0
        
        # Verify Photos were created
        photos = import_service.db.query(Photo).filter_by(import_session_id=import_id).all()
        assert len(photos) > 0
        
        # Verify Images were created  
        images = import_service.db.query(Image).filter_by(import_session_id=import_id).all()
        assert len(images) > 0
        
        # Images should be >= Photos (pairs create multiple Images per Photo)
        assert len(images) >= len(photos)
        
        print(f"✅ Import completed: {len(photos)} photos, {len(images)} images")
        print(f"   Files found: {updated_session.total_files_found}")
        print(f"   Imported: {updated_session.images_imported}")
        print(f"   Duplicates: {updated_session.duplicates_skipped}")
        print(f"   Errors: {updated_session.errors}")
    
    def test_import_duplicate_handling(self, import_service, sample_import_session, temp_image_dir):
        """Test that duplicate imports are handled correctly"""
        import_id = sample_import_session.id
        
        # Run import twice
        success1 = import_service.process_directory_import(import_id, temp_image_dir)
        
        # Reset import session for second run
        import_service.db.query(ImportSession).filter_by(id=import_id).update({
            "status": "pending",
            "images_imported": 0,
            "duplicates_skipped": 0,
            "errors": 0
        })
        import_service.db.commit()
        
        success2 = import_service.process_directory_import(import_id, temp_image_dir)
        
        assert success1 is True
        assert success2 is True
        
        # Second run should have more duplicates
        final_session = import_service.db.query(ImportSession).get(import_id)
        assert final_session.duplicates_skipped > 0
        
        print(f"✅ Duplicate handling: {final_session.duplicates_skipped} duplicates skipped")


class TestImportErrorHandling(TestImportSessionService):
    """Test import error handling and edge cases"""
    
    def test_import_nonexistent_session(self, import_service, temp_image_dir):
        """Test handling of non-existent import session"""
        nonexistent_id = 99999
        
        success = import_service.process_directory_import(nonexistent_id, temp_image_dir)
        
        assert success is False
    
    def test_import_invalid_source_path(self, import_service, sample_import_session):
        """Test handling of invalid source path"""
        import_id = sample_import_session.id
        invalid_path = "/path/to/nonexistent/directory"
        
        success = import_service.process_directory_import(import_id, invalid_path)
        
        assert success is False
        
        # Import session should be marked as failed
        updated_session = import_service.db.query(ImportSession).get(import_id)
        assert updated_session.status == "failed"
    
    def test_import_empty_directory(self, import_service, sample_import_session):
        """Test importing from empty directory"""
        import_id = sample_import_session.id
        
        with tempfile.TemporaryDirectory() as empty_dir:
            success = import_service.process_directory_import(import_id, empty_dir)
        
        # Should complete successfully but import nothing
        assert success is True
        
        updated_session = import_service.db.query(ImportSession).get(import_id)
        assert updated_session.status == "completed"
        assert updated_session.total_files_found == 0
        assert updated_session.images_imported == 0


class TestImportPerformance(TestImportSessionService):
    """Test import performance and resource usage"""
    
    def test_import_performance_metrics(self, import_service, sample_import_session, temp_image_dir):
        """Test that import completes in reasonable time"""
        import time
        import_id = sample_import_session.id
        
        start_time = time.time()
        success = import_service.process_directory_import(import_id, temp_image_dir)
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert success is True
        assert duration < 60  # Should complete within 60 seconds for test data
        
        # Calculate throughput
        updated_session = import_service.db.query(ImportSession).get(import_id)
        if updated_session.total_files_found > 0:
            throughput = updated_session.total_files_found / duration
            print(f"✅ Import performance: {throughput:.1f} files/second")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Files processed: {updated_session.total_files_found}")


class TestImportSessionIntegration(TestImportSessionService):
    """Test integration between ImportSession components"""
    
    def test_import_session_repository_integration(self, import_service, sample_import_session):
        """Test integration with ImportSessionRepository"""
        import_id = sample_import_session.id
        
        # Test repository methods through service
        session = import_service.import_repo.get_import_by_id(import_id)
        assert session is not None
        assert session.id == import_id
        
        # Test status updates
        import_service.import_repo.update_import(import_id, {"status": "processing"})
        
        updated = import_service.import_repo.get_import_by_id(import_id)
        assert updated.status == "processing"
    
    def test_photo_image_relationship_after_import(self, import_service, sample_import_session, temp_image_dir):
        """Test that Photo-Image relationships are correct after import"""
        import_id = sample_import_session.id
        
        success = import_service.process_directory_import(import_id, temp_image_dir)
        assert success is True
        
        # Verify all Images have valid Photo relationships
        images = import_service.db.query(Image).filter_by(import_session_id=import_id).all()
        
        for image in images:
            assert image.hothash is not None
            
            # Verify Photo exists
            photo = import_service.db.query(Photo).filter_by(hothash=image.hothash).first()
            assert photo is not None
            
            # Verify back-reference
            assert image in photo.files


if __name__ == "__main__":
    pytest.main([__file__])