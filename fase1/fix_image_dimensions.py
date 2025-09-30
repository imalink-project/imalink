#!/usr/bin/env python3
"""
Fix existing image dimensions to reflect EXIF rotation
"""
import sys
import os
from PIL import Image as PILImage

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def fix_image_dimensions():
    """Update database dimensions to reflect EXIF rotation"""
    print("🔧 Fixing image dimensions in database...")
    
    try:
        from database.connection import get_db_sync
        from database.models import Image as ImageModel
        from services.image_service import ImageProcessor
        
        db = get_db_sync()
        
        # Get all images
        images = db.query(ImageModel).all()
        
        if not images:
            print("❌ No images found in database")
            return False
            
        print(f"✅ Found {len(images)} images to check")
        
        fixed_count = 0
        for i, image in enumerate(images):
            print(f"\n📸 Image {i+1}: {image.original_filename}")
            print(f"   Current DB dimensions: {image.width}x{image.height}")
            
            # Check if original file exists
            if image.file_path and os.path.exists(image.file_path):
                try:
                    with PILImage.open(image.file_path) as img:
                        # Get original dimensions
                        orig_width, orig_height = img.width, img.height
                        
                        # Apply EXIF rotation
                        img_rotated = ImageProcessor._apply_exif_rotation(img)
                        new_width, new_height = img_rotated.width, img_rotated.height
                        
                        print(f"   Original file dimensions: {orig_width}x{orig_height}")
                        print(f"   After EXIF rotation: {new_width}x{new_height}")
                        
                        # Check if dimensions need updating
                        if image.width != new_width or image.height != new_height:
                            print(f"   🔄 Updating dimensions: {image.width}x{image.height} → {new_width}x{new_height}")
                            
                            # Update database
                            image.width = new_width
                            image.height = new_height
                            fixed_count += 1
                        else:
                            print("   ✅ Dimensions already correct")
                            
                except Exception as e:
                    print(f"   ❌ Error processing {image.file_path}: {e}")
            else:
                print(f"   ⚠️ Original file not found: {image.file_path}")
        
        # Commit changes
        if fixed_count > 0:
            db.commit()
            print(f"\n🎉 Fixed {fixed_count} images")
        else:
            print(f"\n✅ No images needed fixing")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_image_dimensions()
    if success:
        print("\n🎯 Fix completed!")
        print("\n💡 Run test_thumbnail_direct.py again to verify fixes")
    else:
        print("\n💥 Fix failed")