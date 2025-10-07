#!/usr/bin/env python3
"""
Test EXIF extraction directly
"""
from PIL import Image, ImageOps, ExifTags
from PIL.ExifTags import GPSTAGS
import json
from datetime import datetime

def test_exif_extraction():
    image_files = [
        "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO/2024_04_27_taipei_beitou/20240427_234934.JPG",
        "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO/2024_04_27_taipei_beitou/IMG_20240427_145518.jpg",
        "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO/oman/20250112_171126.JPG"
    ]
    
    for image_file in image_files:
        print(f"\n{'='*60}")
        print(f"Testing EXIF extraction on: {image_file}")
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
                # Show ALL EXIF data to debug
                print("\nAll EXIF data:")
                for key, value in exif.items():
                    tag_name = ExifTags.TAGS.get(key, key)
                    print(f"  {tag_name} ({key}): {value}")
                
                # Show some key EXIF values
                print(f"\nDateTime (306): {exif.get(306)}")
                print(f"DateTimeOriginal (36867): {exif.get(36867)}")
                
                # Try to extract date taken
                date_taken = exif.get(36867) or exif.get(306)
                taken_at = None
                if date_taken:
                    try:
                        taken_at = datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
                        print(f"Parsed taken_at: {taken_at}")
                    except Exception as e:
                        print(f"Date parsing error: {e}")
                
                # Extract GPS coordinates - need to get GPS IFD properly
                gps_info = exif.get(34853)  # GPSInfo tag
                print(f"\nGPS Info (34853): {gps_info} (type: {type(gps_info)})")
                
                # Try to get GPS IFD (Image File Directory) data 
                try:
                    gps_ifd = exif.get_ifd(0x8825)  # GPS IFD tag
                    print(f"GPS IFD: {gps_ifd} (type: {type(gps_ifd)})")
                except Exception as e:
                    print(f"Error getting GPS IFD: {e}")
                    gps_ifd = None
                
                if gps_ifd and len(gps_ifd) > 0:
                    try:
                        # GPS coordinates are stored in the GPS IFD
                        gps_data = {}
                        for key in gps_ifd.keys():
                            name = GPSTAGS.get(key, key)
                            gps_data[name] = gps_ifd[key]
                        
                        print(f"GPS Data: {gps_data}")
                        
                        # Convert GPS coordinates to decimal degrees
                        def convert_to_degrees(value):
                            d, m, s = value
                            return d + (m / 60.0) + (s / 3600.0)
                        
                        gps_latitude = None
                        gps_longitude = None
                        
                        if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                            lat = convert_to_degrees(gps_data['GPSLatitude'])
                            if gps_data['GPSLatitudeRef'] == 'S':
                                lat = -lat
                            gps_latitude = lat
                            print(f"Latitude: {gps_latitude}")
                        
                        if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                            lon = convert_to_degrees(gps_data['GPSLongitude'])
                            if gps_data['GPSLongitudeRef'] == 'W':
                                lon = -lon
                            gps_longitude = lon
                            print(f"Longitude: {gps_longitude}")
                            
                    except Exception as gps_error:
                        print(f"GPS extraction error: {gps_error}")
                else:
                    print("No GPS IFD data found or GPS IFD is empty")
                
            else:
                print("No EXIF data found")
                
    except Exception as e:
        print(f"Error opening image: {e}")

if __name__ == "__main__":
    test_exif_extraction()