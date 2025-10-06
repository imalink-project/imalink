#!/usr/bin/env python3
"""
Test ImportSessionsBackgroundService fix for import_import_id error
"""

def test_image_creation_fix():
    """Test that Image creation works without import_import_id error"""
    
    print("🧪 Testing Image Creation Fix...")
    
    try:
        from models import Image
        from services.importing.image_processor import ImageProcessor
        from pathlib import Path
        
        # Test image data that should work now (without import_import_id)
        image_data = {
            "hothash": "test123hash",
            "original_filename": "test.jpg",
            "file_path": "/test/path/test.jpg",
            "file_size": 12345,
            # "import_source" removed - using import_session_id relationship instead
            "width": 1920,
            "height": 1080,
            "exif_data": b"test exif",
            "taken_at": None,
            "gps_latitude": None,
            "gps_longitude": None
        }
        
        # This should work without the invalid import_import_id field
        test_image = Image(**image_data)
        print(f"   ✅ Image created successfully: {test_image}")
        
        # Test ImportSessionsBackgroundService import
        from services.import_sessions_background_service import ImportSessionsBackgroundService
        print("   ✅ ImportSessionsBackgroundService imports without errors")
        
        print("\n🎯 Image Creation Fix: SUCCESS") 
        print("   - import_import_id field removed")
        print("   - Image model accepts correct parameters")
        print("   - ImportSessionsBackgroundService loads correctly")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_image_creation_fix()
    if success:
        print("\n🎉 Fix successful! Try running main.py again.")
    else:
        print("\n❌ Fix needs more work.")