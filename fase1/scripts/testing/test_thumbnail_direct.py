#!/usr/bin/env python3
"""
Test preview image EXIF rotation directly in database
"""
import sys
import os
from pathlib import Path
from PIL import Image
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_preview_image_rotation_direct():
    """Test preview image rotation by checking database directly"""
    print("🧪 Testing preview image EXIF rotation (database direct)...")
    
    try:
        # Import database modules
        from database.connection import get_db_sync
        from models import Image as ImageModel
        
        db = get_db_sync()
        
        # Get first few images
        images = db.query(ImageModel).limit(3).all()
        
        if not images:
            print("❌ No images found in database")
            return False
            
        print(f"✅ Found {len(images)} test images")
        
        for i, image in enumerate(images):
            print(f"\n📸 Image {i+1}: {image.original_filename}")
            print(f"   ID: {image.id}")
            print(f"   Database dimensions: {image.width}x{image.height}")
            
            if image.preview_image:
                # Load preview image from database
                preview_img = Image.open(io.BytesIO(image.preview_image))
                print(f"   Preview image dimensions: {preview_img.size[0]}x{preview_img.size[1]}")
                
                # Check if orientation matches expectations
                db_is_portrait = image.height > image.width
                preview_is_portrait = preview_img.size[1] > preview_img.size[0]
                
                print(f"   DB says portrait: {db_is_portrait}")
                print(f"   Preview image is portrait: {preview_is_portrait}")
                
                if db_is_portrait and not preview_is_portrait:
                    print("   ⚠️ ISSUE: DB says portrait, preview image is landscape - EXIF rotation not applied!")
                elif not db_is_portrait and preview_is_portrait:
                    print("   ⚠️ ISSUE: DB says landscape, preview image is portrait")
                else:
                    print("   ✅ Orientation consistent")
                
                # Test if original file still exists and has EXIF data
                if image.file_path and os.path.exists(image.file_path):
                    try:
                        with Image.open(image.file_path) as original_img:
                            exif_data = original_img.getexif()
                            if 274 in exif_data:  # Orientation tag
                                orientation = exif_data[274]
                                print(f"   Original EXIF orientation: {orientation}")
                                if orientation == 6:  # 90° CW rotation needed
                                    print("   📱 This is a portrait photo that needs rotation")
                            else:
                                print("   📷 No EXIF orientation data")
                    except Exception as e:
                        print(f"   ⚠️ Cannot read original file: {e}")
                else:
                    print(f"   ⚠️ Original file not found: {image.file_path}")
            else:
                print("   ❌ No preview image in database")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_preview_image_rotation_direct()
    if success:
        print("\n🎯 Test completed!")
        print("\n💡 If thumbnails show wrong orientation:")
        print("  1. Old thumbnails were created without EXIF rotation")  
        print("  2. New code applies EXIF rotation during thumbnail creation")
        print("  3. Solution: Re-import images or regenerate thumbnails")
    else:
        print("\n💥 Test failed")