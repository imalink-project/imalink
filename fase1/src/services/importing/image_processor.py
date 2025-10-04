"""
Image Processor Service - Centralized EXIF, GPS and metadata extraction
"""
from typing import Optional, NamedTuple
from pathlib import Path
import json
from datetime import datetime
from PIL import Image as PILImage, ImageOps, ExifTags
from PIL.ExifTags import GPSTAGS


class ImageMetadata(NamedTuple):
    """Structured image metadata container"""
    width: int
    height: int
    exif_data: Optional[bytes]  # JSON as bytes
    taken_at: Optional[datetime]
    gps_latitude: Optional[float]
    gps_longitude: Optional[float]


class ImageProcessor:
    """
    Dedicated service for image processing operations
    
    Consolidates all EXIF/GPS/metadata extraction logic in one place
    for consistency and maintainability.
    """
    
    def extract_metadata(self, image_path: Path) -> ImageMetadata:
        """
        Extract comprehensive metadata from image file
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ImageMetadata with dimensions, EXIF, GPS and timestamp data
        """
        width, height = 0, 0
        exif_data = None
        taken_at = None
        gps_latitude = None
        gps_longitude = None
        
        try:
            with PILImage.open(image_path) as img:
                # Get dimensions from properly rotated image
                img_rotated = ImageOps.exif_transpose(img)
                width, height = img_rotated.size
                
                # Extract EXIF data
                exif = img.getexif()
                if exif:
                    # Store EXIF as JSON
                    exif_dict = {}
                    for tag_id, value in exif.items():
                        try:
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            exif_dict[str(tag)] = str(value)
                        except:
                            pass  # Skip problematic EXIF tags
                    
                    if exif_dict:
                        exif_data = json.dumps(exif_dict).encode('utf-8')
                    
                    # Extract date taken
                    taken_at = self._extract_date_taken(exif)
                    
                    # Extract GPS coordinates  
                    gps_latitude, gps_longitude = self._extract_gps_coordinates(exif)
                    
        except Exception as e:
            # Log error but return partial metadata
            print(f"Error extracting metadata from {image_path.name}: {e}")
        
        return ImageMetadata(
            width=width,
            height=height,
            exif_data=exif_data,
            taken_at=taken_at,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude
        )
    
    def _extract_date_taken(self, exif) -> Optional[datetime]:
        """
        Extract date taken from EXIF data
        
        Tries DateTimeOriginal first, then DateTime as fallback
        """
        date_taken = exif.get(36867) or exif.get(306)  # DateTimeOriginal or DateTime
        if date_taken:
            try:
                return datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
            except Exception:
                pass  # Failed to parse date
        return None
    
    def _extract_gps_coordinates(self, exif) -> tuple[Optional[float], Optional[float]]:
        """
        Extract GPS coordinates from EXIF data using GPS IFD
        
        Returns:
            Tuple of (latitude, longitude) or (None, None) if no GPS data
        """
        try:
            gps_ifd = exif.get_ifd(0x8825)  # GPS IFD tag
            if gps_ifd and len(gps_ifd) > 0:
                gps_data = {}
                for key in gps_ifd.keys():
                    name = GPSTAGS.get(key, key)
                    gps_data[name] = gps_ifd[key]
                
                # Extract latitude
                gps_latitude = None
                if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                    lat = self._convert_to_degrees(gps_data['GPSLatitude'])
                    if gps_data['GPSLatitudeRef'] == 'S':
                        lat = -lat
                    gps_latitude = lat
                
                # Extract longitude  
                gps_longitude = None
                if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                    lon = self._convert_to_degrees(gps_data['GPSLongitude'])
                    if gps_data['GPSLongitudeRef'] == 'W':
                        lon = -lon
                    gps_longitude = lon
                
                return gps_latitude, gps_longitude
                
        except Exception:
            pass  # GPS extraction failed, but that's OK - not all images have GPS
            
        return None, None
    
    def _convert_to_degrees(self, value) -> float:
        """
        Convert GPS coordinates from degrees/minutes/seconds to decimal degrees
        
        Args:
            value: Tuple of (degrees, minutes, seconds)
            
        Returns:
            Decimal degrees as float
        """
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)
    
    def generate_thumbnail(self, image_path: Path, size: tuple = (300, 300)) -> Optional[bytes]:
        """
        Generate thumbnail with proper EXIF rotation
        
        Args:
            image_path: Path to source image
            size: Thumbnail dimensions (width, height)
            
        Returns:
            Thumbnail as bytes or None if generation failed
        """
        try:
            from io import BytesIO
            
            with PILImage.open(image_path) as img:
                # Apply EXIF rotation before thumbnailing
                img_rotated = ImageOps.exif_transpose(img)
                
                # Generate thumbnail
                img_rotated.thumbnail(size, PILImage.Resampling.LANCZOS)
                
                # Convert to bytes
                thumbnail_io = BytesIO()
                img_rotated.save(thumbnail_io, format='JPEG', quality=85)
                return thumbnail_io.getvalue()
                
        except Exception as e:
            print(f"Error generating thumbnail for {image_path.name}: {e}")
            return None
    
    def validate_image(self, image_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate that file is a readable image
        
        Args:
            image_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with PILImage.open(image_path) as img:
                # Try to access basic image properties
                _ = img.size
                _ = img.format
                return True, None
                
        except Exception as e:
            return False, str(e)
    
    def detect_image_type(self, image_path: Path) -> str:
        """
        Detect image format and type category
        
        Returns:
            String indicating image type: 'jpeg', 'png', 'raw', 'other'
        """
        extension = image_path.suffix.lower()
        
        if extension in {'.jpg', '.jpeg'}:
            return 'jpeg'
        elif extension in {'.png'}:
            return 'png'
        elif extension in {'.cr2', '.cr3', '.nef', '.arw', '.orf', '.dng', '.raf', '.rw2'}:
            return 'raw'
        elif extension in {'.tiff', '.tif', '.bmp', '.webp'}:
            return 'other'
        else:
            return 'unknown'