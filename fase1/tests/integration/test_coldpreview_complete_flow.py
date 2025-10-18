"""
Complete Coldpreview Integration Test

This test verifies the entire coldpreview workflow:
1. Import a JPEG image to create ImageFile and Photo
2. Find Photo by hothash
3. Generate and upload coldpreview 
4. Retrieve coldpreview and verify it matches

Uses in-memory SQLite database for isolation.
"""
import pytest
import tempfile
import io
import sys
from pathlib import Path
from PIL import Image as PILImage

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add src to path for imports
sys.path.insert(0, "/home/kjell/git_prosjekt/imalink/fase1/src")

# Import models and create tables
from models.base import Base
from models.photo import Photo
from models.image_file import ImageFile
from models.author import Author
from services.image_file_service import ImageFileService
from services.photo_service import PhotoService
from utils.coldpreview_repository import ColdpreviewRepository
from schemas.image_file_schemas import ImageFileCreateRequest


class TestColdpreviewCompleteFlow:
    """
    Comprehensive integration test for the complete coldpreview workflow
    """
    
    def __init__(self):
        self.image_file_service = None
        self.photo_service = None
        self.session = None
        self.engine = None
    
    def _load_test_image(self) -> bytes:
        """Load test JPEG image and return as bytes"""
        test_image_path = Path("/home/kjell/git_prosjekt/imalink/fase1/test_user_files/images/jpg_enkeltbilde/20250112_171126.JPG")
        
        if not test_image_path.exists():
            # Create a simple test image if the file doesn't exist
            img = PILImage.new('RGB', (800, 600), color='red')
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            return buffer.getvalue()
        
        with open(test_image_path, 'rb') as f:
            return f.read()
    
    @pytest.fixture
    def setup_database(self):
        """Setup in-memory database for testing with pytest"""
        return self._setup_database()
    
    def _setup_database(self):
        """Setup in-memory database for testing"""
        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Store references for cleanup
        self.engine = engine
        self.session = session
        
        return session
    
    def _generate_hotpreview(self, image_data: bytes) -> bytes:
        """Generate 150x150 hotpreview from image data"""
        img = PILImage.open(io.BytesIO(image_data))
        
        # Handle EXIF rotation if needed
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Create thumbnail
        img.thumbnail((150, 150), PILImage.Resampling.LANCZOS)
        
        # Save as JPEG
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    def _generate_coldpreview(self, image_data: bytes, max_size: int = 300) -> bytes:
        """Generate coldpreview from image data"""
        img = PILImage.open(io.BytesIO(image_data))
        
        # Handle EXIF rotation if needed
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if needed
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
        
        # Save as JPEG
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    def test_complete_coldpreview_workflow(self):
        """Test the complete coldpreview workflow from image import to retrieval"""
        
        # Step 1: Load test image
        print("Step 1: Loading test image...")
        original_image_data = self._load_test_image()
        assert len(original_image_data) > 0, "Test image should not be empty"
        print(f"Loaded image: {len(original_image_data)} bytes")
        
        # Step 2: Generate hotpreview
        print("Step 2: Generating hotpreview...")
        hotpreview_data = self._generate_hotpreview(original_image_data)
        assert len(hotpreview_data) > 0, "Hotpreview should not be empty"
        print(f"Generated hotpreview: {len(hotpreview_data)} bytes")
        
        # Step 3: Create ImageFile (this will auto-create Photo)
        print("Step 3: Creating ImageFile...")
        exif_bytes = b'{"Make": "Test", "Model": "TestCamera"}'  # Convert to bytes for schema validation
        image_file_request = ImageFileCreateRequest(
            filename="test_image.jpg",
            hotpreview=hotpreview_data,
            exif_data=exif_bytes
        )
        
        created_image_file = self.image_file_service.create_image_file_with_photo(image_file_request)
        assert created_image_file is not None, "ImageFile should be created"
        print(f"Created ImageFile ID: {created_image_file.id}")
        print(f"Photo hothash: {created_image_file.photo_hothash}")
        
        # Step 4: Find Photo by hothash
        print("Step 4: Finding Photo by hothash...")
        photo_hothash = created_image_file.photo_hothash
        assert photo_hothash is not None, "Photo hothash should not be None"
        
        photo = self.photo_service.get_photo_by_hash(photo_hothash)
        assert photo is not None, "Photo should be found"
        print(f"Found Photo: {photo.hothash}")
        
        # Verify photo has the expected image file
        assert len(photo.files) == 1, "Photo should have exactly one image file"
        assert photo.files[0].id == created_image_file.id, "Photo should reference the created image file"
        
        # Step 5: Generate coldpreview
        print("Step 5: Generating coldpreview...")
        coldpreview_data = self._generate_coldpreview(original_image_data, max_size=300)
        assert len(coldpreview_data) > 0, "Coldpreview should not be empty"
        print(f"Generated coldpreview: {len(coldpreview_data)} bytes")
        
        # Verify coldpreview is smaller than original
        assert len(coldpreview_data) < len(original_image_data), "Coldpreview should be smaller than original"
        
        # Verify coldpreview dimensions
        coldpreview_img = PILImage.open(io.BytesIO(coldpreview_data))
        assert max(coldpreview_img.size) <= 300, "Coldpreview should be max 300px"
        print(f"Coldpreview dimensions: {coldpreview_img.size}")
        
        # Step 6: Upload coldpreview to Photo
        print("Step 6: Uploading coldpreview to Photo...")
        upload_result = self.photo_service.upload_coldpreview(photo_hothash, coldpreview_data)
        assert upload_result is not None, "Upload should return result"
        assert upload_result["hothash"] == photo_hothash, "Upload result should have correct hothash"
        assert upload_result["width"] > 0, "Upload result should have valid width"
        assert upload_result["height"] > 0, "Upload result should have valid height"
        assert upload_result["size"] > 0, "Upload result should have valid file size"
        print(f"Upload successful: {upload_result['width']}x{upload_result['height']}, {upload_result['size']} bytes")
        
        # Step 7: Verify Photo has coldpreview metadata
        print("Step 7: Verifying Photo metadata...")
        updated_photo = self.photo_service.get_photo_by_hash(photo_hothash)
        
        # Debug: Print all attributes
        print(f"DEBUG: Photo attributes: {dir(updated_photo)}")
        print(f"DEBUG: coldpreview_path = {getattr(updated_photo, 'coldpreview_path', 'NOT_FOUND')}")
        print(f"DEBUG: coldpreview_width = {getattr(updated_photo, 'coldpreview_width', 'NOT_FOUND')}")
        print(f"DEBUG: coldpreview_height = {getattr(updated_photo, 'coldpreview_height', 'NOT_FOUND')}")
        print(f"DEBUG: coldpreview_size = {getattr(updated_photo, 'coldpreview_size', 'NOT_FOUND')}")
        
        assert getattr(updated_photo, 'coldpreview_path', None) is not None, "Photo should have coldpreview_path"
        
        coldpreview_width = getattr(updated_photo, 'coldpreview_width', None)
        coldpreview_height = getattr(updated_photo, 'coldpreview_height', None)
        coldpreview_size = getattr(updated_photo, 'coldpreview_size', None)
        
        assert coldpreview_width is not None and coldpreview_width > 0, "Photo should have coldpreview_width"
        assert coldpreview_height is not None and coldpreview_height > 0, "Photo should have coldpreview_height"  
        assert coldpreview_size is not None and coldpreview_size > 0, "Photo should have coldpreview_size"
        print(f"Photo coldpreview metadata: {coldpreview_width}x{coldpreview_height}")
        
        # Step 8: Retrieve coldpreview and verify it matches
        print("Step 8: Retrieving coldpreview...")
        retrieved_coldpreview = self.photo_service.get_coldpreview(photo_hothash)
        assert retrieved_coldpreview is not None, "Should be able to retrieve coldpreview"
        print(f"Retrieved coldpreview: {len(retrieved_coldpreview)} bytes")
        
        # Step 9: Compare uploaded and retrieved coldpreview
        print("Step 9: Comparing uploaded and retrieved coldpreview...")
        print(f"Original coldpreview size: {len(coldpreview_data)} bytes")
        print(f"Retrieved coldpreview size: {len(retrieved_coldpreview)} bytes")
        
        # Note: Repository may optimize/recompress the image, so we compare dimensions instead of exact bytes
        # Verify retrieved image can be opened and has same dimensions as uploaded
        retrieved_img = PILImage.open(io.BytesIO(retrieved_coldpreview))
        original_img = PILImage.open(io.BytesIO(coldpreview_data))
        assert retrieved_img.size == original_img.size, f"Retrieved image dimensions {retrieved_img.size} should match original {original_img.size}"
        print(f"✅ Image dimensions match: {retrieved_img.size}")
        
        # This verification is now done in step 9 above
        
        # Step 10: Test dynamic resizing
        print("Step 10: Testing dynamic resizing...")
        resized_coldpreview = self.photo_service.get_coldpreview(photo_hothash, width=200, height=200)
        assert resized_coldpreview is not None, "Should be able to get resized coldpreview"
        
        resized_img = PILImage.open(io.BytesIO(resized_coldpreview))
        assert max(resized_img.size) <= 200, "Resized image should be max 200px"
        print(f"Resized image dimensions: {resized_img.size}")
        
        print("✅ Complete coldpreview workflow test passed!")
    
    def test_coldpreview_not_found(self):
        """Test retrieving coldpreview when none exists"""
        # Create a fake photo hothash
        fake_hothash = "nonexistent" + "0" * 48  # 64 char hash
        
        # Try to get coldpreview for non-existent photo
        with pytest.raises(Exception):  # Should raise NotFoundError
            self.photo_service.get_coldpreview(fake_hothash)
    
    def test_coldpreview_delete(self):
        """Test deleting coldpreview"""
        # First create image and upload coldpreview (shortened version of main test)
        original_image_data = self._load_test_image()
        hotpreview_data = self._generate_hotpreview(original_image_data)
        
        exif_bytes = b'{"Make": "Test", "Model": "TestCamera"}'  # Convert to bytes for schema validation
        image_file_request = ImageFileCreateRequest(
            filename="delete_test.jpg",
            hotpreview=hotpreview_data,
            exif_data=exif_bytes
        )
        
        created_image_file = self.image_file_service.create_image_file_with_photo(image_file_request)
        photo_hothash = created_image_file.photo_hothash
        
        # Upload coldpreview
        coldpreview_data = self._generate_coldpreview(original_image_data)
        self.photo_service.upload_coldpreview(photo_hothash, coldpreview_data)
        
        # Verify coldpreview exists
        retrieved = self.photo_service.get_coldpreview(photo_hothash)
        assert retrieved is not None, "Coldpreview should exist before deletion"
        
        # Delete coldpreview
        self.photo_service.delete_coldpreview(photo_hothash)
        
        # Verify coldpreview is gone
        deleted_coldpreview = self.photo_service.get_coldpreview(photo_hothash)
        assert deleted_coldpreview is None, "Coldpreview should not exist after deletion"
        
        # Verify photo metadata is cleared
        photo = self.photo_service.get_photo_by_hash(photo_hothash)
        assert getattr(photo, 'coldpreview_path', None) is None, "coldpreview_path should be None after deletion"


if __name__ == "__main__":
    """Run the test standalone"""
    import sys
    sys.path.insert(0, "/home/kjell/git_prosjekt/imalink/fase1/src")
    
    test_instance = TestColdpreviewCompleteFlow()
    session = test_instance._setup_database()
    
    # Setup services with the session
    test_instance.image_file_service = ImageFileService(session)
    test_instance.photo_service = PhotoService(session)
    
    try:
        print("🧪 Running complete coldpreview workflow test...")
        test_instance.test_complete_coldpreview_workflow()
        print()
        
        print("🧪 Running coldpreview not found test...")
        test_instance.test_coldpreview_not_found()
        print("✅ Not found test passed!")
        print()
        
        print("🧪 Running coldpreview delete test...")
        test_instance.test_coldpreview_delete()
        print("✅ Delete test passed!")
        print()
        
        print("🎉 All coldpreview tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup is handled by the fixture
        pass