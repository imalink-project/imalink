#!/usr/bin/env python3
"""
Test EXIF extraction on multiple images
"""
from PIL import Image, ImageOps, ExifTags
from PIL.ExifTags import GPSTAGS
import json
from datetime import datetime

def convert_to_degrees(value):
    """Convert GPS coordinates to decimal degrees"""
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)

def test_exif_extraction():
    image_files = [
        r"C:\temp\PHOTOS_SRC_TEST_MICRO\2024_04_27_taipei_beitou\20240427_234934.JPG",
        r"C:\temp\PHOTOS_SRC_TEST_MICRO\2024_04_27_taipei_beitou\IMG_20240427_145518.jpg",
        r"C:\temp\PHOTOS_SRC_TEST_MICRO\oman\20250112_171126.JPG"
    ]
    
    for image_file in image_files:
        print(f"\n{'='*60}")
        print(f"Testing: {image_file}")
        print(f"{'='*60}")
        
        try:
            with Image.open(image_file) as img:
                # Get dimensions from properly rotated image
                img_rotated = ImageOps.exif_transpose(img)
                width, height = img_rotated.size
                print(f"Dimensions: {width} x {height}")
                
                # Extract EXIF data
                exif = img.getexif()
                print(f"EXIF keys found: {len(exif)}")
                
                if exif:
                    # Show key EXIF values
                    print(f"DateTime (306): {exif.get(306)}")
                    print(f"DateTimeOriginal (36867): {exif.get(36867)}")
                    print(f"GPS Info (34853): {exif.get(34853)}")
                    print(f"ExifOffset (34665): {exif.get(34665)}")
                    
                    # Try to extract date taken
                    date_taken = exif.get(36867) or exif.get(306)
                    taken_at = None
                    if date_taken:
                        try:
                            taken_at = datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
                            print(f"Parsed taken_at: {taken_at}")
                        except Exception as e:
                            print(f"Date parsing error: {e}")
                    
                    # Try multiple GPS extraction methods
                    print("\n--- GPS Extraction Attempts ---")
                    
                    # Method 1: Try to get GPS IFD
                    try:
                        gps_ifd = exif.get_ifd(0x8825)  # GPS IFD tag
                        if gps_ifd and len(gps_ifd) > 0:
                            print(f"GPS IFD found: {len(gps_ifd)} entries")
                            gps_data = {}
                            for key in gps_ifd.keys():
                                name = GPSTAGS.get(key, key)
                                gps_data[name] = gps_ifd[key]
                                print(f"  {name}: {gps_ifd[key]}")
                            
                            # Extract coordinates
                            if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                                lat = convert_to_degrees(gps_data['GPSLatitude'])
                                if gps_data['GPSLatitudeRef'] == 'S':
                                    lat = -lat
                                print(f"Latitude: {lat}")
                            
                            if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                                lon = convert_to_degrees(gps_data['GPSLongitude'])
                                if gps_data['GPSLongitudeRef'] == 'W':
                                    lon = -lon
                                print(f"Longitude: {lon}")
                        else:
                            print("No GPS IFD data found")
                    except Exception as e:
                        print(f"GPS IFD extraction failed: {e}")
                    
                    # Method 2: Check if there's an EXIF sub-IFD
                    try:
                        exif_ifd = exif.get_ifd(0x8769)  # EXIF IFD tag  
                        if exif_ifd:
                            print(f"\nEXIF IFD found: {len(exif_ifd)} entries")
                            for key, value in exif_ifd.items():
                                tag_name = ExifTags.TAGS.get(key, key)
                                if 'GPS' in str(tag_name) or key == 34853:
                                    print(f"  EXIF IFD GPS-related: {tag_name} ({key}): {value}")
                    except Exception as e:
                        print(f"EXIF IFD extraction failed: {e}")
                    
                else:
                    print("No EXIF data found")
                    
        except Exception as e:
            print(f"Error opening image: {e}")

if __name__ == "__main__":
    test_exif_extraction()