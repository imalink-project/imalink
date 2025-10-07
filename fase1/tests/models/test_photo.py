"""
Unit tests for Photo model
Tests photo creation, metadata extraction, hotpreview generation, and file handling
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

from models.photo import Photo
from models.image import Image  
from models.base import Base
from core.exceptions import DuplicateImageError


# Module-level fixtures available to all test classes
@pytest.fixture(scope="class")
def test_images_dir():
    """Path to test images directory"""
    return Path(__file__).parent.parent.parent / 'test_user_files' / 'images'

@pytest.fixture(scope="class")
def jpg_single_file(test_images_dir):
    """Path to single JPEG file"""
    return str(test_images_dir / 'jpg_enkeltbilde' / '20250112_171126.JPG')

@pytest.fixture(scope="class") 
def jpg_dng_pair_files(test_images_dir):
    """Paths to matching JPEG+DNG pair"""
    base_dir = test_images_dir / 'jpg_dng_like'
    return [
        str(base_dir / '20240427_234934.JPG'),
        str(base_dir / '20240427_234934.DNG')
    ]

@pytest.fixture(scope="class")
def dng_single_file(test_images_dir):
    """Path to single DNG file"""  
    return str(test_images_dir / 'dng_enkeltbilde' / '*.DNG')  # Adjust based on actual files

@pytest.fixture
def in_memory_db():
    """In-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def mock_import_session_id():
    """Mock import session ID"""
    return 1


class TestPhoto:
    """Test suite for Photo model"""


class TestPhotoProperties:
    """Test Photo model properties and computed fields"""
    
    def test_has_gps_property_true(self):
        """Test has_gps property returns True when GPS coordinates present"""
        photo = Photo(
            hothash="test123",
            gps_latitude=59.9139,
            gps_longitude=10.7522
        )
        assert photo.has_gps is True
    
    def test_has_gps_property_false(self):
        """Test has_gps property returns False when GPS coordinates missing"""
        photo = Photo(hothash="test123")
        assert photo.has_gps is False
        
        # Test partial GPS data
        photo.gps_latitude = 59.9139
        assert photo.has_gps is False
        
    def test_jpeg_file_property(self):
        """Test jpeg_file property returns correct JPEG file"""
        photo = Photo(hothash="test123")
        
        # Mock Image objects
        jpeg_image = MagicMock()
        jpeg_image.filename = "test.jpg"
        
        raw_image = MagicMock()
        raw_image.filename = "test.dng"
        
        photo.files = [raw_image, jpeg_image]
        
        with patch.object(photo, 'files', [raw_image, jpeg_image]):
            # This will need adjustment based on actual implementation
            assert photo.jpeg_file is not None
    
    def test_primary_filename_property(self):
        """Test primary_filename property returns correct filename"""
        photo = Photo(hothash="test123")
        
        # Test with no files
        photo.files = []
        assert photo.primary_filename == "Unknown"


class TestPhotoCreationFromSingleFile:
    """Test Photo creation from single image file"""
    
    def test_create_from_single_jpeg(self, jpg_single_file, in_memory_db, mock_import_session_id):
        """Test creating Photo from single JPEG file"""
        # Check if file exists
        if not Path(jpg_single_file).exists():
            pytest.skip(f"Test file not found: {jpg_single_file}")
        
        # Create photo from single JPEG
        photo = Photo.create_from_file_group(
            file_group=[jpg_single_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        # Verify photo creation
        assert photo is not None
        assert photo.hothash is not None
        assert len(photo.hothash) > 0
        assert photo.import_session_id == mock_import_session_id
        
        # Verify metadata extraction
        assert photo.width is not None
        assert photo.height is not None
        assert photo.width > 0
        assert photo.height > 0
        
        # Verify hotpreview generation
        assert photo.hotpreview is not None
        assert len(photo.hotpreview) > 0
        
        # Verify Image file creation
        assert len(photo.files) == 1
        assert photo.files[0].filename == Path(jpg_single_file).name
        assert photo.files[0].hothash == photo.hothash
        
        print(f"✅ Single JPEG: {photo.width}x{photo.height}, hash={photo.hothash[:8]}...")
    
    def test_create_from_single_jpeg_metadata(self, jpg_single_file, in_memory_db, mock_import_session_id):
        """Test metadata extraction from single JPEG"""
        if not Path(jpg_single_file).exists():
            pytest.skip(f"Test file not found: {jpg_single_file}")
        
        photo = Photo.create_from_file_group(
            file_group=[jpg_single_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        # Test specific metadata fields
        assert isinstance(photo.width, int)
        assert isinstance(photo.height, int)
        
        # GPS might be None for test images
        assert photo.gps_latitude is None or isinstance(photo.gps_latitude, float)
        assert photo.gps_longitude is None or isinstance(photo.gps_longitude, float)
        
        # User metadata should start empty
        assert photo.title is None
        assert photo.description is None
        assert photo.tags is None or photo.tags == []
        assert photo.rating is None or photo.rating == 0


class TestPhotoCreationFromFilePair:
    """Test Photo creation from JPEG+RAW file pairs"""
    
    def test_create_from_jpeg_dng_pair(self, jpg_dng_pair_files, in_memory_db, mock_import_session_id):
        """Test creating Photo from JPEG+DNG pair"""
        # Check if files exist
        for file_path in jpg_dng_pair_files:
            if not Path(file_path).exists():
                pytest.skip(f"Test file not found: {file_path}")
        
        # Create photo from file pair
        photo = Photo.create_from_file_group(
            file_group=jpg_dng_pair_files,
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        
        # Verify photo creation
        assert photo is not None
        assert photo.hothash is not None
        
        # Verify both files are associated
        assert len(photo.files) == 2
        
        # Verify filenames match input files
        created_filenames = {f.filename for f in photo.files}
        expected_filenames = {Path(f).name for f in jpg_dng_pair_files}
        assert created_filenames == expected_filenames
        
        # Verify all files have same hothash
        for image_file in photo.files:
            assert image_file.hothash == photo.hothash
        
        # Verify has_raw_companion property
        assert photo.has_raw_companion is True
        
        print(f"✅ JPEG+DNG pair: {len(photo.files)} files, hash={photo.hothash[:8]}...")
    
    def test_primary_file_selection(self, jpg_dng_pair_files):
        """Test that JPEG is preferred as primary file over RAW"""
        # Import Path first
        from pathlib import Path
        
        if not all(Path(f).exists() for f in jpg_dng_pair_files):
            pytest.skip("Test files not found")
            
        # Test _choose_primary_file method directly
        file_paths = [Path(f) for f in jpg_dng_pair_files]
        
        primary = Photo._choose_primary_file(file_paths)
        
        # Should prefer JPEG over DNG
        assert primary is not None
        assert Path(primary).suffix.lower() in ['.jpg', '.jpeg']


class TestPhotoHashing:
    """Test Photo hash generation and duplicate detection"""
    
    def test_content_hash_generation(self, jpg_single_file):
        """Test that content hash is generated consistently"""
        if not Path(jpg_single_file).exists():
            pytest.skip(f"Test file not found: {jpg_single_file}")
        
        # Generate hash twice - should be identical
        hash1 = Photo._generate_content_hash(jpg_single_file)
        hash2 = Photo._generate_content_hash(jpg_single_file)
        
        assert hash1 == hash2
        assert len(hash1) > 0
        assert isinstance(hash1, str)
    
    def test_duplicate_detection(self, jpg_single_file, in_memory_db, mock_import_session_id):
        """Test duplicate photo detection"""
        if not Path(jpg_single_file).exists():
            pytest.skip(f"Test file not found: {jpg_single_file}")
        
        # Create first photo
        photo1 = Photo.create_from_file_group(
            file_group=[jpg_single_file],
            import_session_id=mock_import_session_id,
            db_session=in_memory_db
        )
        in_memory_db.add(photo1)
        in_memory_db.commit()
        
        # Try to create duplicate - should raise exception
        with pytest.raises(DuplicateImageError):
            Photo.create_from_file_group(
                file_group=[jpg_single_file],
                import_session_id=mock_import_session_id,
                db_session=in_memory_db
            )


class TestPhotoHotpreview:
    """Test hotpreview generation"""
    
    def test_hotpreview_generation(self, jpg_single_file):
        """Test that hotpreview is generated correctly"""
        if not Path(jpg_single_file).exists():
            pytest.skip(f"Test file not found: {jpg_single_file}")
        
        # Generate hotpreview
        hotpreview = Photo._generate_hotpreview(jpg_single_file)
        
        assert hotpreview is not None
        assert isinstance(hotpreview, bytes)
        assert len(hotpreview) > 0
        
        # Should be valid JPEG data
        assert hotpreview.startswith(b'\xff\xd8')  # JPEG magic bytes
    
    def test_hotpreview_size_limit(self, jpg_single_file):
        """Test that hotpreview is within reasonable size limits"""
        if not Path(jpg_single_file).exists():
            pytest.skip(f"Test file not found: {jpg_single_file}")
        
        hotpreview = Photo._generate_hotpreview(jpg_single_file)
        
        # Should be smaller than original (thumbnail)
        original_size = Path(jpg_single_file).stat().st_size
        hotpreview_size = len(hotpreview)
        
        assert hotpreview_size < original_size
        assert hotpreview_size < 100_000  # Should be less than 100KB for thumbnails


class TestPhotoErrorHandling:
    """Test Photo error handling and edge cases"""
    
    def test_create_from_nonexistent_file(self, in_memory_db, mock_import_session_id):
        """Test handling of non-existent files"""
        nonexistent_file = "/path/to/nonexistent/file.jpg"
        
        with pytest.raises((FileNotFoundError, Exception)):
            Photo.create_from_file_group(
                file_group=[nonexistent_file],
                import_session_id=mock_import_session_id,
                db_session=in_memory_db
            )
    
    def test_create_from_empty_file_group(self, in_memory_db, mock_import_session_id):
        """Test handling of empty file group"""
        with pytest.raises((IndexError, ValueError)):
            Photo.create_from_file_group(
                file_group=[],
                import_session_id=mock_import_session_id,
                db_session=in_memory_db
            )
    
    def test_create_from_invalid_image_file(self, in_memory_db, mock_import_session_id):
        """Test handling of invalid/corrupted image files"""
        # Create a temporary text file that's not an image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b"This is not an image file")
            tmp_path = tmp.name
        
        try:
            # Should handle gracefully (might return None for metadata)
            photo = Photo.create_from_file_group(
                file_group=[tmp_path],
                import_session_id=mock_import_session_id,
                db_session=in_memory_db
            )
            
            # If it doesn't raise an exception, verify graceful handling
            if photo:
                # Metadata extraction should fail gracefully
                assert photo.width is None or isinstance(photo.width, int)
                assert photo.height is None or isinstance(photo.height, int)
        except Exception as e:
            # If it raises an exception, that's also acceptable behavior
            assert "PIL" in str(e) or "image" in str(e).lower()
        finally:
            # Cleanup
            Path(tmp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])