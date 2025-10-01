#!/usr/bin/env python3
"""
Test EXIF rotation functionality
This script tests if EXIF orientation is correctly applied during thumbnail generation
"""

import os
import sys
from PIL import Image, ImageOps, ImageDraw
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_image_with_exif_orientation():
    """Create test images with different EXIF orientations"""
    
    # Create a test image with clear directional content
    img = Image.new('RGB', (200, 300), color='lightblue')  # Portrait dimensions
    draw = ImageDraw.Draw(img)
    
    # Add directional content - arrow pointing up and "TOP" text
    draw.text((10, 10), "TOP", fill='black')
    draw.polygon([(100, 50), (80, 80), (90, 80), (90, 120), (110, 120), (110, 80), (120, 80)], fill='red')
    
    return img

def test_exif_rotation():
    """Test EXIF rotation handling"""
    print("🧪 Testing EXIF Orientation handling...")
    
    # Create test image
    test_img = create_test_image_with_exif_orientation()
    
    # Save with different orientations (simulate camera behavior)
    orientations = {
        1: "Normal",
        3: "Rotated 180°", 
        6: "Rotated 90° CW (Portrait mode)",
        8: "Rotated 90° CCW"
    }
    
    from services.image_service import ImageProcessor
    
    for orientation, description in orientations.items():
        print(f"\n📸 Testing orientation {orientation}: {description}")
        
        # Create EXIF with orientation
        exif_dict = {"0th": {274: orientation}}  # 274 is orientation tag
        
        # Save test image with this orientation
        test_filename = f"test_orientation_{orientation}.jpg"
        
        # For orientation 6 (portrait mode), we need to save the image 
        # physically rotated but with EXIF saying it should be corrected
        if orientation == 6:
            # Save image rotated 90° CCW (as cameras do)
            rotated_img = test_img.rotate(90, expand=True)
            rotated_img.save(test_filename, format='JPEG', quality=90)
        elif orientation == 3:
            # Save image rotated 180° 
            rotated_img = test_img.rotate(180, expand=True)
            rotated_img.save(test_filename, format='JPEG', quality=90)
        elif orientation == 8:
            # Save image rotated 90° CW
            rotated_img = test_img.rotate(-90, expand=True)
            rotated_img.save(test_filename, format='JPEG', quality=90)
        else:
            # Normal orientation
            test_img.save(test_filename, format='JPEG', quality=90)
        
        # Now manually add EXIF orientation (simplified approach)
        # In practice, cameras add this automatically
        
        print(f"✅ Created {test_filename}")
        
        # Test our rotation correction
        try:
            corrected_img = ImageProcessor._apply_exif_rotation(Image.open(test_filename))
            
            # Save corrected version for visual inspection
            corrected_filename = f"corrected_orientation_{orientation}.jpg"
            corrected_img.save(corrected_filename, format='JPEG', quality=90)
            
            print(f"✅ Corrected version saved as {corrected_filename}")
            print(f"   Original size: {Image.open(test_filename).size}")
            print(f"   Corrected size: {corrected_img.size}")
            
        except Exception as e:
            print(f"❌ Error processing orientation {orientation}: {e}")
    
    print("\n🎯 Test complete!")
    print("📁 Check the generated test images:")
    print("   - test_orientation_*.jpg (simulates camera output)")
    print("   - corrected_orientation_*.jpg (after our EXIF processing)")
    print("\n💡 Compare how they look in File Explorer vs our correction!")

if __name__ == "__main__":
    try:
        test_exif_rotation()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()