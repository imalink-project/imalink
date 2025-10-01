#!/usr/bin/env python3
"""
Test EXIF stripping functionality - show size reduction
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_exif_stripping():
    """Test EXIF stripping and show size reduction"""
    print("🧹 EXIF Stripping Test")
    print("=" * 50)
    
    # Ask for image path or directory
    path_input = input("📁 Enter path to an image file OR directory: ").strip().strip('"')
    
    if not path_input or not Path(path_input).exists():
        print("❌ Invalid path or file not found")
        return
    
    path = Path(path_input)
    
    # If it's a directory, find the first image file
    if path.is_dir():
        print(f"📁 Directory provided, looking for image files...")
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
        
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(path.glob(f"*{ext}")))
            image_files.extend(list(path.glob(f"*{ext.upper()}")))
        
        if not image_files:
            print(f"❌ No image files found in {path}")
            return
            
        # Use the first image file found
        path_input = str(image_files[0])
        print(f"🎯 Using first image found: {image_files[0].name}")
    
    elif not path.is_file():
        print("❌ Path must be a file or directory")
        return
    
    try:
        from services.image_service import ImageProcessor
        import piexif
        from PIL import Image
        
        # Test original EXIF extraction  
        print(f"\n📸 Analyzing: {Path(path_input).name}")
        
        with Image.open(path_input) as img:
            raw_exif = img.info.get('exif')
            
            if not raw_exif:
                print("❌ No EXIF data found in this image")
                return
            
            print(f"📊 Original EXIF size: {len(raw_exif):,} bytes")
            
            # Parse EXIF
            exif_dict = piexif.load(raw_exif)
            
            print("\n🏷️ EXIF sections found:")
            for section, data in exif_dict.items():
                if data:
                    if section == "thumbnail":
                        thumb_size = len(data) if isinstance(data, bytes) else 0
                        print(f"   📎 {section}: {thumb_size:,} bytes (WILL BE REMOVED)")
                    else:
                        tag_count = len(data) if isinstance(data, dict) else 0
                        print(f"   📋 {section}: {tag_count} tags")
            
            # Test our stripping
            stripped_exif = ImageProcessor._strip_exif_data(exif_dict)
            
            if stripped_exif:
                stripped_bytes = piexif.dump(stripped_exif)
                print(f"\n✂️ Stripped EXIF size: {len(stripped_bytes):,} bytes")
                
                reduction = len(raw_exif) - len(stripped_bytes)
                reduction_pct = (reduction / len(raw_exif)) * 100
                
                print(f"💾 Space saved: {reduction:,} bytes ({reduction_pct:.1f}% reduction)")
                
                print(f"\n🏷️ Kept sections:")
                for section, data in stripped_exif.items():
                    if data:
                        print(f"   ✅ {section}: {len(data)} essential tags")
                        
                # Show what was kept vs removed
                print(f"\n📋 What was removed:")
                removed_items = []
                
                if "thumbnail" in exif_dict and exif_dict["thumbnail"]:
                    thumb_size = len(exif_dict["thumbnail"]) if isinstance(exif_dict["thumbnail"], bytes) else 0
                    removed_items.append(f"Embedded thumbnail ({thumb_size:,} bytes)")
                
                if "1st" in exif_dict and exif_dict["1st"]:
                    removed_items.append(f"Thumbnail metadata ({len(exif_dict['1st'])} tags)")
                    
                for section in ["Interop"]:
                    if section in exif_dict and exif_dict[section]:
                        removed_items.append(f"{section} data")
                
                # Check for maker notes
                if "Exif" in exif_dict and 37500 in exif_dict["Exif"]:
                    maker_note = exif_dict["Exif"][37500]
                    maker_size = len(maker_note) if isinstance(maker_note, bytes) else 0
                    removed_items.append(f"MakerNote ({maker_size:,} bytes)")
                
                if removed_items:
                    for item in removed_items:
                        print(f"   🗑️ {item}")
                else:
                    print("   ℹ️ Minimal EXIF - little to remove")
                
            else:
                print("⚠️ No essential EXIF data found to keep")
                
    except Exception as e:
        print(f"❌ Error testing EXIF stripping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exif_stripping()