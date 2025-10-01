#!/usr/bin/env python3
"""
Diagnose EXIF orientation in real images
This script checks if your images actually have EXIF orientation data
"""

import os
import sys
from PIL import Image
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_image_exif(image_path):
    """Check EXIF orientation data in an image file"""
    try:
        with Image.open(image_path) as img:
            print(f"\n📸 Analyzing: {Path(image_path).name}")
            print(f"   Dimensions: {img.size[0]}x{img.size[1]}")
            print(f"   Format: {img.format}")
            
            # Get EXIF data
            exif_data = img.getexif()
            if exif_data:
                print(f"   ✅ EXIF data found ({len(exif_data)} tags)")
                
                # Check for orientation tag (274)
                if 274 in exif_data:
                    orientation = exif_data[274]
                    orientation_names = {
                        1: "Normal",
                        2: "Mirrored horizontally", 
                        3: "Rotated 180°",
                        4: "Mirrored vertically",
                        5: "Mirrored horizontally + rotated 90° CCW",
                        6: "Rotated 90° CW (Portrait mode)",
                        7: "Mirrored horizontally + rotated 90° CW", 
                        8: "Rotated 90° CCW"
                    }
                    print(f"   🎯 EXIF Orientation: {orientation} ({orientation_names.get(orientation, 'Unknown')})")
                    
                    # Test our correction
                    from services.image_service import ImageProcessor
                    corrected = ImageProcessor._apply_exif_rotation(img)
                    print(f"   📐 After correction: {corrected.size[0]}x{corrected.size[1]}")
                    
                    if img.size != corrected.size:
                        print(f"   ✅ Size changed - rotation was applied!")
                    else:
                        print(f"   ℹ️ Size unchanged - no rotation needed or applied")
                        
                else:
                    print(f"   ⚠️ No orientation tag (274) found in EXIF")
                    
                # Show some other EXIF tags
                common_tags = {
                    271: "Camera Make",
                    272: "Camera Model", 
                    306: "DateTime",
                    36867: "DateTimeOriginal"
                }
                
                for tag_id, tag_name in common_tags.items():
                    if tag_id in exif_data:
                        print(f"   📋 {tag_name}: {exif_data[tag_id]}")
                        
            else:
                print(f"   ❌ No EXIF data found")
                
    except Exception as e:
        print(f"   ❌ Error analyzing {image_path}: {e}")

def main():
    print("🔍 EXIF Orientation Diagnostic Tool")
    print("=" * 50)
    
    # Ask user for image path or directory
    path_input = input("\n📁 Enter path to image file or directory: ").strip().strip('"')
    
    if not path_input:
        print("❌ No path provided")
        return
        
    path = Path(path_input)
    
    if not path.exists():
        print(f"❌ Path does not exist: {path}")
        return
        
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    
    if path.is_file():
        # Single file
        if path.suffix.lower() in image_extensions:
            check_image_exif(str(path))
        else:
            print(f"❌ Not a supported image file: {path}")
    elif path.is_dir():
        # Directory - check first few images
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(path.glob(f"*{ext}")))
            image_files.extend(list(path.glob(f"*{ext.upper()}")))
        
        if not image_files:
            print(f"❌ No image files found in: {path}")
            return
            
        print(f"📁 Found {len(image_files)} image files")
        print("🔍 Analyzing first 5 images:")
        
        for img_file in image_files[:5]:
            check_image_exif(str(img_file))
            
        if len(image_files) > 5:
            print(f"\n... and {len(image_files) - 5} more files")
    
    print("\n" + "=" * 50)
    print("💡 Analysis complete!")
    print("\nWhat to look for:")
    print("✅ EXIF Orientation 6 = Portrait photos that need 90° CW rotation")
    print("⚠️ No orientation tag = Image might be pre-rotated or have no EXIF")
    print("📱 Phone photos usually have orientation tags")
    print("🖥️ Screenshots/edited images often don't have EXIF data")

if __name__ == "__main__":
    main()