#!/usr/bin/env python3
"""
Test thumbnail EXIF rotation functionality
"""
import sys
import os
import requests
from PIL import Image
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_thumbnail_rotation():
    """Test if thumbnails are correctly rotated based on EXIF"""
    print("🧪 Testing thumbnail EXIF rotation...")
    
    # Test server is running
    try:
        response = requests.get("http://localhost:8000/api/images/")
        if response.status_code != 200:
            print("❌ Server not running or API error")
            return False
        
        images = response.json()
        if not images:
            print("❌ No images found in database")
            return False
        
        print(f"✅ Found {len(images)} images in database")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:8000")
        return False
    
    # Test first few images
    for i, image in enumerate(images[:3]):
        image_id = image['id']
        filename = image['filename']
        
        print(f"\n📸 Testing image {i+1}: {filename}")
        print(f"   Database dimensions: {image.get('width', 'N/A')}x{image.get('height', 'N/A')}")
        
        # Get thumbnail
        try:
            response = requests.get(f"http://localhost:8000/api/images/{image_id}/thumbnail")
            if response.status_code == 200:
                # Check thumbnail dimensions
                thumbnail_data = response.content
                thumbnail_img = Image.open(io.BytesIO(thumbnail_data))
                
                print(f"   Thumbnail dimensions: {thumbnail_img.size[0]}x{thumbnail_img.size[1]}")
                
                # Analyze orientation
                is_portrait_in_db = image.get('height', 0) > image.get('width', 0)
                is_portrait_thumbnail = thumbnail_img.size[1] > thumbnail_img.size[0]
                
                print(f"   DB says portrait: {is_portrait_in_db}")
                print(f"   Thumbnail is portrait: {is_portrait_thumbnail}")
                
                if is_portrait_in_db and not is_portrait_thumbnail:
                    print("   ⚠️ PROBLEM: Database says portrait, but thumbnail is landscape")
                elif not is_portrait_in_db and is_portrait_thumbnail:
                    print("   ⚠️ PROBLEM: Database says landscape, but thumbnail is portrait")
                else:
                    print("   ✅ Orientation matches between DB and thumbnail")
                    
            else:
                print(f"   ❌ Failed to get thumbnail: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error getting thumbnail: {e}")
    
    return True

if __name__ == "__main__":
    success = test_thumbnail_rotation()
    if success:
        print("\n🎯 Test completed!")
        print("\n💡 If you see orientation mismatches:")
        print("  1. The original images have EXIF orientation data")
        print("  2. But thumbnails in database were not created with EXIF rotation")
        print("  3. Need to re-import or regenerate thumbnails")
    else:
        print("\n💥 Test failed - check server and database")