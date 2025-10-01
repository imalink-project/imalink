#!/usr/bin/env python3
"""
Test script to demonstrate rotation-invariant hashing
"""

import os
import sys
from PIL import Image
import imagehash
import io

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.image_service import ImageProcessor

def create_test_image():
    """Create a simple test image with clear directional pattern"""
    img = Image.new('RGB', (150, 150), color='white')
    
    # Add some directional content (arrow pointing right)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Arrow shape
    points = [(50, 75), (100, 50), (100, 65), (120, 65), (120, 85), (100, 85), (100, 100)]
    draw.polygon(points, fill='black')
    
    return img

def test_rotation_invariant_hash():
    """Test if our rotation-invariant hash works"""
    print("🧪 Testing rotation-invariant hash...")
    
    # Create test image
    original = create_test_image()
    
    # Create rotated versions
    rotated_90 = original.rotate(90, expand=True)
    rotated_180 = original.rotate(180, expand=True)
    rotated_270 = original.rotate(270, expand=True)
    
    # Convert to bytes (simulate thumbnail creation)
    def img_to_bytes(img):
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        return buffer.getvalue()
    
    original_bytes = img_to_bytes(original)
    rotated_90_bytes = img_to_bytes(rotated_90)
    rotated_180_bytes = img_to_bytes(rotated_180)
    rotated_270_bytes = img_to_bytes(rotated_270)
    
    # Test old method (rotation-sensitive)
    print("\n📊 OLD METHOD (rotation-sensitive):")
    hash_orig_old = str(imagehash.phash(original))
    hash_90_old = str(imagehash.phash(rotated_90))
    hash_180_old = str(imagehash.phash(rotated_180))
    hash_270_old = str(imagehash.phash(rotated_270))
    
    print(f"Original (0°):   {hash_orig_old}")
    print(f"Rotated 90°:     {hash_90_old}")
    print(f"Rotated 180°:    {hash_180_old}")
    print(f"Rotated 270°:    {hash_270_old}")
    print(f"All same? {len(set([hash_orig_old, hash_90_old, hash_180_old, hash_270_old])) == 1}")
    
    # Test new method (rotation-invariant)
    print("\n✨ NEW METHOD (rotation-invariant):")
    hash_orig_new = ImageProcessor.generate_perceptual_hash_from_thumbnail(original_bytes)
    hash_90_new = ImageProcessor.generate_perceptual_hash_from_thumbnail(rotated_90_bytes)
    hash_180_new = ImageProcessor.generate_perceptual_hash_from_thumbnail(rotated_180_bytes)
    hash_270_new = ImageProcessor.generate_perceptual_hash_from_thumbnail(rotated_270_bytes)
    
    print(f"Original (0°):   {hash_orig_new}")
    print(f"Rotated 90°:     {hash_90_new}")
    print(f"Rotated 180°:    {hash_180_new}")
    print(f"Rotated 270°:    {hash_270_new}")
    print(f"All same? {len(set([hash_orig_new, hash_90_new, hash_180_new, hash_270_new])) == 1}")
    
    if hash_orig_new == hash_90_new == hash_180_new == hash_270_new:
        print("✅ SUCCESS: All rotations have same hash!")
    else:
        print("❌ ISSUE: Rotations still have different hashes")

if __name__ == "__main__":
    try:
        test_rotation_invariant_hash()
    except Exception as e:
        print(f"❌ Error running test: {e}")
        print("Make sure to install dependencies: pip install pillow imagehash")