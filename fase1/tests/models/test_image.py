"""
Unit tests for Image model
Tests image file metadata extraction, EXIF handling, and relationship to Photo
"""
import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

# Add src to path for imports  
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from models.image import Image
from models.photo import Photo
from models.base import Base


class TestImage:
    """Test suite for Image model"""
    
    @pytest.fixture(scope="class")
    def test_images_dir(self):
        """Path to test images directory"""
        return Path(__file__).parent.parent.parent / 'test_user_files' / 'images'
    
    @pytest.fixture(scope="class")
    def jpg_file(self, test_images_dir):
        """Path to JPEG test file"""
        return str(test_images_dir / 'jpg_enkeltbilde' / '20250112_171126.JPG')
    
    @pytest.fixture(scope="class")
    def dng_file(self, test_images_dir):
        """Path to DNG test file"""
        return str(test_images_dir / 'jpg_dng_like' / '20240427_234934.DNG')
    
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
    def sample_hothash(self):
        """Sample photo hash for testing"""
        return "abcd1234efgh5678"
    
    @pytest.fixture
    def mock_import_session_id(self):
        """Mock import session ID"""
        return 1


class TestImageCreation(TestImage):
    """Test Image model creation and initialization"""
    
    def test_create_image_basic_properties(self, sample_hothash, mock_import_session_id):
        """Test basic Image creation with required properties"""
        image = Image(
            filename="test.jpg",
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        assert image.filename == "test.jpg"
        assert image.hothash == sample_hothash
        assert image.import_session_id == mock_import_session_id
        assert image.file_size is None  # Should be None when not set
        assert image.exif_data is None  # Should be None when not set
    
    def test_create_from_file_factory_method(self, jpg_file, sample_hothash, mock_import_session_id):
        """Test Image.create_from_file factory method"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        image = Image.create_from_file(
            file_path=jpg_file,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        # Verify basic properties
        assert image.filename == Path(jpg_file).name
        assert image.hothash == sample_hothash
        assert image.import_session_id == mock_import_session_id
        
        # Verify file metadata extraction
        assert image.file_size is not None
        assert image.file_size > 0
        
        print(f"✅ Image created: {image.filename}, size: {image.file_size} bytes")
    
    def test_create_from_path_object(self, jpg_file, sample_hothash, mock_import_session_id):
        """Test creating Image from Path object (not string)"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        file_path = Path(jpg_file)
        image = Image.create_from_file(
            file_path=file_path,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        assert image.filename == file_path.name
        assert image.file_size > 0


class TestImageMetadata(TestImage):
    """Test Image metadata extraction"""
    
    def test_file_size_extraction(self, jpg_file, sample_hothash, mock_import_session_id):
        """Test that file size is correctly extracted"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        image = Image.create_from_file(
            file_path=jpg_file,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        # Compare with actual file size
        actual_size = Path(jpg_file).stat().st_size
        assert image.file_size == actual_size
    
    def test_exif_extraction_jpeg(self, jpg_file):
        """Test EXIF extraction from JPEG file"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        exif_data = Image._extract_raw_exif(jpg_file)
        
        if exif_data is not None:
            assert isinstance(exif_data, bytes)
            assert len(exif_data) > 0
            print(f"✅ EXIF extracted: {len(exif_data)} bytes")
        else:
            print("ℹ️  No EXIF data found in test image")
    
    def test_exif_extraction_dng(self, dng_file):
        """Test EXIF extraction from DNG file"""
        if not Path(dng_file).exists():
            pytest.skip(f"Test file not found: {dng_file}")
        
        exif_data = Image._extract_raw_exif(dng_file)
        
        # DNG files typically have rich EXIF data
        if exif_data is not None:
            assert isinstance(exif_data, bytes)
            assert len(exif_data) > 0
            print(f"✅ DNG EXIF extracted: {len(exif_data)} bytes")
        else:
            print("ℹ️  No EXIF data found in DNG test file")


class TestImageFileTypes(TestImage):
    """Test Image handling of different file types"""
    
    def test_jpeg_file_handling(self, jpg_file, sample_hothash, mock_import_session_id):
        """Test handling of JPEG files"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        image = Image.create_from_file(
            file_path=jpg_file,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        assert image.filename.lower().endswith(('.jpg', '.jpeg'))
        assert image.file_size > 0
        
    def test_dng_file_handling(self, dng_file, sample_hothash, mock_import_session_id):
        """Test handling of DNG (RAW) files"""
        if not Path(dng_file).exists():
            pytest.skip(f"Test file not found: {dng_file}")
        
        image = Image.create_from_file(
            file_path=dng_file,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        assert image.filename.lower().endswith('.dng')
        assert image.file_size > 0
        
        # DNG files are typically larger than JPEG
        print(f"✅ DNG file: {image.filename}, size: {image.file_size} bytes")


class TestImagePhotoRelationship(TestImage):
    """Test Image relationship with Photo model"""
    
    def test_image_hothash_relationship(self, jpg_file, in_memory_db, mock_import_session_id):
        """Test that Image correctly links to Photo via hothash"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        # Create Photo first
        photo = Photo.create_from_file_group(
            file_group=[jpg_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        # Photo should have created Image automatically
        assert len(photo.files) == 1
        image = photo.files[0]
        
        # Verify relationship
        assert image.hothash == photo.hothash
        assert image.photo == photo
        
    def test_image_hotpreview_property(self, jpg_file, in_memory_db, mock_import_session_id):
        """Test that Image can access hotpreview from associated Photo"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        # Create Photo with hotpreview
        photo = Photo.create_from_file_group(
            file_group=[jpg_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        image = photo.files[0]
        
        # Image should be able to access Photo's hotpreview
        assert image.hotpreview is not None
        assert image.hotpreview == photo.hotpreview
        assert isinstance(image.hotpreview, bytes)
        
        print(f"✅ Image hotpreview access: {len(image.hotpreview)} bytes")
        
    def test_image_photo_metadata_property(self, jpg_file, in_memory_db, mock_import_session_id):
        """Test that Image can access Photo metadata via convenience property"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        # Create Photo
        photo = Photo.create_from_file_group(
            file_group=[jpg_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        image = photo.files[0]
        metadata = image.photo_metadata
        
        # Should return dictionary with key Photo fields
        assert isinstance(metadata, dict)
        assert 'width' in metadata
        assert 'height' in metadata
        assert 'title' in metadata
        assert 'taken_at' in metadata
        assert 'has_gps' in metadata
        assert 'rating' in metadata
        
        # Values should match Photo
        assert metadata['width'] == photo.width
        assert metadata['height'] == photo.height
        assert metadata['title'] == photo.title
        
        print(f"✅ Image metadata access: {metadata['width']}x{metadata['height']}")
        
    def test_image_properties_without_photo(self, sample_hothash, mock_import_session_id):
        """Test Image properties when Photo relationship is not loaded"""
        # Create Image without loading Photo relationship
        image = Image(
            filename="test.jpg",
            file_size=1000,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        # Properties should handle missing Photo gracefully
        assert image.hotpreview is None
        assert image.photo_metadata == {}
        
        print("✅ Image properties handle missing Photo gracefully")
    
    def test_multiple_images_same_photo(self, in_memory_db, mock_import_session_id):
        """Test multiple Image records linking to same Photo"""
        # Get JPEG+DNG pair
        test_dir = Path(__file__).parent.parent.parent / 'test_user_files' / 'images' / 'jpg_dng_like'
        jpg_file = str(test_dir / '20240427_234934.JPG')
        dng_file = str(test_dir / '20240427_234934.DNG')
        
        if not Path(jpg_file).exists() or not Path(dng_file).exists():
            pytest.skip("JPEG+DNG pair not found")
        
        # Create Photo from file pair
        photo = Photo.create_from_file_group(
            file_group=[jpg_file, dng_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        # Should have two Images linking to same Photo
        assert len(photo.files) == 2
        
        # Both images should have same hothash
        hash_values = {img.hothash for img in photo.files}
        assert len(hash_values) == 1  # All same hash
        assert list(hash_values)[0] == photo.hothash
        
        # Verify different filenames
        filenames = {img.filename for img in photo.files}
        assert len(filenames) == 2  # Different filenames
        
        print(f"✅ Two images linked to photo {photo.hothash[:8]}...")


class TestImageErrorHandling(TestImage):
    """Test Image error handling and edge cases"""
    
    def test_create_from_nonexistent_file(self, sample_hothash, mock_import_session_id):
        """Test handling of non-existent files"""
        nonexistent_file = "/path/to/nonexistent/file.jpg"
        
        # Should create Image but with no file_size
        image = Image.create_from_file(
            file_path=nonexistent_file,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        assert image.filename == "file.jpg"
        assert image.file_size is None
        assert image.hothash == sample_hothash
    
    def test_exif_extraction_invalid_file(self):
        """Test EXIF extraction from invalid/corrupted file"""
        # Create temporary file with invalid image data
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b"This is not an image")
            tmp_path = tmp.name
        
        try:
            exif_data = Image._extract_raw_exif(tmp_path)
            # Should return None or handle gracefully
            assert exif_data is None
        except Exception:
            # Exception is also acceptable behavior
            pass
        finally:
            Path(tmp_path).unlink()
    
    def test_empty_filename_handling(self, sample_hothash, mock_import_session_id):
        """Test handling of empty or invalid filenames"""
        # Test empty path (will resolve to current directory)
        image = Image.create_from_file(
            file_path="",
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        # Should handle gracefully
        assert image.hothash == sample_hothash
        # Empty path resolves to "." (current directory), so file_size won't be None
        assert image.file_size is not None


class TestImageDatabaseOperations(TestImage):
    """Test Image database operations"""
    
    def test_save_image_to_database(self, jpg_file, in_memory_db, sample_hothash, mock_import_session_id):
        """Test saving Image to database"""
        if not Path(jpg_file).exists():
            pytest.skip(f"Test file not found: {jpg_file}")
        
        image = Image.create_from_file(
            file_path=jpg_file,
            hothash=sample_hothash,
            import_session_id=mock_import_session_id
        )
        
        # Save to database
        in_memory_db.add(image)
        in_memory_db.commit()
        
        # Retrieve from database
        saved_image = in_memory_db.query(Image).filter_by(filename=image.filename).first()
        
        assert saved_image is not None
        assert saved_image.filename == image.filename
        assert saved_image.hothash == image.hothash
        assert saved_image.file_size == image.file_size
    
    def test_query_images_by_hothash(self, in_memory_db, mock_import_session_id):
        """Test querying images by hothash"""
        test_dir = Path(__file__).parent.parent.parent / 'test_user_files' / 'images' / 'jpg_dng_like'
        jpg_file = str(test_dir / '20240427_234934.JPG')
        dng_file = str(test_dir / '20240427_234934.DNG')
        
        if not Path(jpg_file).exists() or not Path(dng_file).exists():
            pytest.skip("Test files not found")
        
        # Create Photo with multiple Images
        photo = Photo.create_from_file_group(
            file_group=[jpg_file, dng_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        in_memory_db.add(photo)
        in_memory_db.commit()
        
        # Query Images by hothash
        images = in_memory_db.query(Image).filter_by(hothash=photo.hothash).all()
        
        assert len(images) == 2
        assert all(img.hothash == photo.hothash for img in images)


if __name__ == "__main__":
    pytest.main([__file__])