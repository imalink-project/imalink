"""
Integration test for full import workflow
Tests complete import process from test_user_files directory

NOTE: These tests are for the OLD import system architecture.
The new architecture has ImportSession as a simple metadata container,
not an import processor. Import is now handled by client applications.

TODO: Update these tests for the new frontend-driven import architecture.
"""
import pytest

# Skip all tests in this module - outdated architecture
pytestmark = pytest.mark.skip(reason="Tests for old import architecture - needs update for frontend-driven import")
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from models.base import Base
from models.photo import Photo
from models.image import Image
from models.import_session import ImportSession
# from services.import_sessions_background_service import ImportSessionsBackgroundService  # DELETED - old architecture
from repositories.import_session_repository import ImportSessionRepository


@pytest.fixture
def in_memory_db():
    """Clean in-memory database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_images_dir():
    """Path to test images directory"""
    return Path(__file__).parent.parent.parent / 'test_user_files'


@pytest.fixture
def temp_import_dir(test_images_dir):
    """Create temporary copy of test images for import testing"""
    temp_dir = tempfile.mkdtemp()
    
    # Copy entire test_user_files structure to temp location
    shutil.copytree(test_images_dir, Path(temp_dir) / 'test_import', dirs_exist_ok=True)
    
    yield str(Path(temp_dir) / 'test_import')
    
    # Cleanup
    shutil.rmtree(temp_dir)


class TestFullImportWorkflow:
    """Integration tests for complete import workflow"""
    
    def test_import_full_test_directory(self, temp_import_dir, in_memory_db):
        """Test importing entire test_user_files directory"""
        print(f"\n🚀 Testing full import from: {temp_import_dir}")
        
        # 1. Create ImportSession
        import_repo = ImportSessionRepository(in_memory_db)
        import_session = ImportSession(
            title="Full test directory import",
            storage_location=str(temp_import_dir)
        )
        in_memory_db.add(import_session)
        in_memory_db.commit()
        
        print(f"✅ Created ImportSession ID: {import_session.id}")
        
        # 2. Run import process
        import_service = ImportSessionsBackgroundService(in_memory_db)
        success = import_service.process_directory_import(import_session.id, temp_import_dir)
        
        assert success is True, "Import process should succeed"
        print("✅ Import process completed successfully")
        
        # 3. Verify ImportSession was updated
        updated_session = in_memory_db.query(ImportSession).get(import_session.id)
        assert updated_session.status == "completed"
        assert updated_session.total_files_found > 0
        assert updated_session.images_imported > 0
        
        print(f"📊 Import Statistics:")
        print(f"   Total files found: {updated_session.total_files_found}")
        print(f"   Images imported: {updated_session.images_imported}")
        print(f"   Duplicates skipped: {updated_session.duplicates_skipped}")
        print(f"   RAW files skipped: {updated_session.raw_files_skipped}")
        print(f"   Single RAW skipped: {updated_session.single_raw_skipped}")
        print(f"   Errors: {updated_session.errors_count}")
        
        # 4. Verify Photos were created
        photos = in_memory_db.query(Photo).all()
        assert len(photos) > 0, "Should have created Photo records"
        
        print(f"📷 Created {len(photos)} Photo records")
        
        # 5. Verify Images were created
        images = in_memory_db.query(Image).all()
        assert len(images) > 0, "Should have created Image records"
        assert len(images) >= len(photos), "Should have at least as many Images as Photos"
        
        print(f"🖼️ Created {len(images)} Image records")
        
        # 6. Verify relationships are correct
        for photo in photos:
            assert len(photo.files) > 0, f"Photo {photo.hothash[:8]} should have associated files"
            for image in photo.files:
                assert image.hothash == photo.hothash, "Image and Photo should have same hothash"
                assert image.import_session_id == import_session.id, "Image should reference import session"
        
        print("✅ All Photo-Image relationships verified")
        
        # 7. Check specific file types were processed
        jpeg_images = [img for img in images if img.filename.lower().endswith('.jpg')]
        dng_images = [img for img in images if img.filename.lower().endswith('.dng')]
        
        assert len(jpeg_images) > 0, "Should have processed JPEG files"
        print(f"   JPEG files: {len(jpeg_images)}")
        
        if len(dng_images) > 0:
            print(f"   DNG files: {len(dng_images)}")
        
        # 8. Verify Photo metadata extraction
        photos_with_dimensions = [p for p in photos if p.width and p.height]
        assert len(photos_with_dimensions) > 0, "Should have extracted dimensions from some photos"
        
        photos_with_previews = [p for p in photos if p.hotpreview]
        assert len(photos_with_previews) > 0, "Should have generated hotpreviews"
        
        print(f"   Photos with dimensions: {len(photos_with_dimensions)}")
        print(f"   Photos with hotpreviews: {len(photos_with_previews)}")
        
        return {
            'import_session': updated_session,
            'photos': photos,
            'images': images,
            'temp_dir': temp_import_dir
        }
    
    def test_duplicate_import_detection(self, temp_import_dir, in_memory_db):
        """Test that importing same files again detects duplicates"""
        print(f"\n🔄 Testing duplicate detection on re-import")
        
        # 1. First import
        first_result = self.test_import_full_test_directory(temp_import_dir, in_memory_db)
        original_photos = len(first_result['photos'])
        original_images = len(first_result['images'])
        
        print(f"📊 After first import: {original_photos} photos, {original_images} images")
        
        # 2. Create second ImportSession for same directory
        import_session2 = ImportSession(
            title="Duplicate import test",
            storage_location=str(temp_import_dir)
        )
        in_memory_db.add(import_session2)
        in_memory_db.commit()
        
        # 3. Run second import
        import_service = ImportSessionsBackgroundService(in_memory_db)
        success = import_service.process_directory_import(import_session2.id, temp_import_dir)
        
        assert success is True, "Second import should also succeed"
        print("✅ Second import completed")
        
        # 4. Verify duplicate detection
        updated_session2 = in_memory_db.query(ImportSession).get(import_session2.id)
        print(f"📊 Second import statistics:")
        print(f"   Total files found: {updated_session2.total_files_found}")
        print(f"   Images imported: {updated_session2.images_imported}")
        print(f"   Duplicates skipped: {updated_session2.duplicates_skipped}")
        
        # Should have found files but skipped most as duplicates
        assert updated_session2.total_files_found > 0, "Should have found files"
        assert updated_session2.duplicates_skipped > 0, "Should have detected duplicates"
        
        # 5. Verify database didn't get duplicate Photos
        final_photos = in_memory_db.query(Photo).all()
        final_images = in_memory_db.query(Image).all()
        
        print(f"📊 After second import: {len(final_photos)} photos, {len(final_images)} images")
        
        # Photo count should be the same (no duplicates created)
        assert len(final_photos) == original_photos, "Should not create duplicate Photos"
        
        # Image count might be higher if we track per-import, but let's check the logic
        print(f"✅ Duplicate detection working: {updated_session2.duplicates_skipped} duplicates skipped")
    
    def test_import_with_mixed_file_types(self, temp_import_dir, in_memory_db):
        """Test importing directory with mixed JPEG/RAW pairs and singles"""
        print(f"\n🎭 Testing mixed file type handling")
        
        result = self.test_import_full_test_directory(temp_import_dir, in_memory_db)
        photos = result['photos']
        images = result['images']
        
        # Analyze file pairing
        jpeg_files = [img for img in images if img.filename.lower().endswith('.jpg')]
        raw_files = [img for img in images if img.filename.lower().endswith(('.dng', '.raw'))]
        
        # Check for JPEG+RAW pairs (same basename, different extensions)
        pairs_found = 0
        singles_found = 0
        
        for photo in photos:
            photo_files = photo.files
            extensions = [Path(f.filename).suffix.lower() for f in photo_files]
            
            if len(photo_files) == 2 and '.jpg' in extensions and any(ext in ['.dng', '.raw'] for ext in extensions):
                pairs_found += 1
                print(f"   📸 Found JPEG+RAW pair: {photo.primary_filename}")
            elif len(photo_files) == 1:
                singles_found += 1
        
        print(f"📊 File pairing analysis:")
        print(f"   JPEG+RAW pairs: {pairs_found}")
        print(f"   Single files: {singles_found}")
        print(f"   Total JPEG files: {len(jpeg_files)}")
        print(f"   Total RAW files: {len(raw_files)}")
        
        # Verify that each Photo has sensible file associations
        for photo in photos:
            assert len(photo.files) >= 1, "Each Photo should have at least one file"
            # If multiple files, they should have same basename
            if len(photo.files) > 1:
                basenames = [Path(f.filename).stem for f in photo.files]
                assert len(set(basenames)) == 1, f"Files in Photo should have same basename: {basenames}"
    
    def test_import_error_handling(self, in_memory_db):
        """Test import error handling with invalid paths"""
        print(f"\n❌ Testing error handling")
        
        # Test with non-existent directory
        import_session = ImportSession(
            title="Error handling test",
            storage_location="/nonexistent/directory"
        )
        in_memory_db.add(import_session)
        in_memory_db.commit()
        
        import_service = ImportSessionsBackgroundService(in_memory_db)
        success = import_service.process_directory_import(import_session.id, "/nonexistent/directory")
        
        # Should handle error gracefully
        assert success is False, "Import should fail for non-existent directory"
        
        updated_session = in_memory_db.query(ImportSession).get(import_session.id)
        assert updated_session.status in ["failed", "error"], "Session should be marked as failed"
        
        print("✅ Error handling works correctly")
    
    def test_import_performance_metrics(self, temp_import_dir, in_memory_db):
        """Test that import process tracks performance metrics"""
        print(f"\n⚡ Testing performance metrics")
        
        import time
        start_time = time.time()
        
        result = self.test_import_full_test_directory(temp_import_dir, in_memory_db)
        
        end_time = time.time()
        duration = end_time - start_time
        
        import_session = result['import_session']
        files_processed = import_session.images_imported
        
        if files_processed > 0:
            files_per_second = files_processed / duration
            print(f"⚡ Performance metrics:")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Files processed: {files_processed}")
            print(f"   Files per second: {files_per_second:.1f}")
            
            # Basic performance assertion (should process at least 1 file per second)
            assert files_per_second > 0.5, "Import should maintain reasonable performance"
        
        print("✅ Performance tracking working")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "-s"])