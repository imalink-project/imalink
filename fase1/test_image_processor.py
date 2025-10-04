"""
Test the new ImageProcessor service with actual image files
"""
from services.importing.image_processor import ImageProcessor
from pathlib import Path

def test_image_processor():
    processor = ImageProcessor()
    
    # Test files from our known set
    test_files = [
        r"C:\temp\PHOTOS_SRC_TEST_MICRO\2024_04_27_taipei_beitou\20240427_234934.JPG",
        r"C:\temp\PHOTOS_SRC_TEST_MICRO\2024_04_27_taipei_beitou\IMG_20240427_145518.jpg",
        r"C:\temp\PHOTOS_SRC_TEST_MICRO\oman\20250112_171126.JPG"
    ]
    
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            print(f"\n🔍 Testing: {path.name}")
            
            # Extract metadata
            metadata = processor.extract_metadata(path)
            
            print(f"  📐 Dimensions: {metadata.width} x {metadata.height}")
            print(f"  📅 Taken at: {metadata.taken_at}")
            print(f"  🌍 GPS: {metadata.gps_latitude}, {metadata.gps_longitude}")
            print(f"  📊 EXIF data: {'Yes' if metadata.exif_data else 'No'} ({len(metadata.exif_data) if metadata.exif_data else 0} bytes)")
            
            # Test image validation
            is_valid, error = processor.validate_image(path)
            print(f"  ✅ Valid: {is_valid} {f'(Error: {error})' if error else ''}")
            
            # Test image type detection
            image_type = processor.detect_image_type(path)
            print(f"  🏷️  Type: {image_type}")
        else:
            print(f"❌ File not found: {path}")

if __name__ == "__main__":
    test_image_processor()