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
    
    def extract_metadata_from_raw_exif(self, raw_exif_bytes: bytes, width: int, height: int) -> ImageMetadata:
        """
        Extract metadata from raw EXIF bytes (sent from frontend)
        
        Args:
            raw_exif_bytes: Raw EXIF binary data
            width: Image width (from frontend)
            height: Image height (from frontend)
            
        Returns:
            ImageMetadata with EXIF, GPS and timestamp data
        """
        exif_data = None
        taken_at = None
        gps_latitude = None
        gps_longitude = None
        
        try:
            # Parse raw EXIF bytes using piexif
            import piexif
            
            exif_dict = piexif.load(raw_exif_bytes)
            
            # Convert to our JSON format for storage
            json_exif = {}
            for ifd_name, ifd in exif_dict.items():
                if ifd_name == "thumbnail":
                    continue  # Skip thumbnail data
                    
                if isinstance(ifd, dict):
                    for tag_id, value in ifd.items():
                        tag_name = piexif.TAGS[ifd_name].get(tag_id, {}).get("name", str(tag_id))
                        try:
                            # Convert bytes to string for JSON serialization
                            if isinstance(value, bytes):
                                json_exif[f"{ifd_name}.{tag_name}"] = value.decode('utf-8', errors='ignore')
                            else:
                                json_exif[f"{ifd_name}.{tag_name}"] = str(value)
                        except:
                            pass  # Skip problematic tags
            
            if json_exif:
                exif_data = json.dumps(json_exif).encode('utf-8')
            
            # Extract date taken from EXIF dict
            taken_at = self._extract_date_from_exif_dict(exif_dict)
            
            # Extract GPS coordinates from EXIF dict  
            gps_latitude, gps_longitude = self._extract_gps_from_exif_dict(exif_dict)
                    
        except Exception as e:
            print(f"Error extracting metadata from raw EXIF: {e}")
            # Fallback: just store the raw EXIF bytes
            try:
                # Store raw bytes as base64 encoded JSON
                import base64
                exif_data = json.dumps({"raw_exif": base64.b64encode(raw_exif_bytes).decode('ascii')}).encode('utf-8')
            except:
                pass
        
        return ImageMetadata(
            width=width,
            height=height,
            exif_data=exif_data,
            taken_at=taken_at,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude
        )
    
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
    
    def _extract_date_from_exif_dict(self, exif_dict: dict) -> Optional[datetime]:
        """
        Extract date taken from parsed EXIF dictionary (piexif format)
        """
        try:
            # Check Exif IFD for DateTimeOriginal (tag 36867)
            if "Exif" in exif_dict and 36867 in exif_dict["Exif"]:
                date_str = exif_dict["Exif"][36867].decode('ascii')
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            
            # Fallback to DateTime (tag 306) in 0th IFD
            if "0th" in exif_dict and 306 in exif_dict["0th"]:
                date_str = exif_dict["0th"][306].decode('ascii')  
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                
        except Exception:
            pass  # Date parsing failed
            
        return None
    
    def _extract_gps_from_exif_dict(self, exif_dict: dict) -> tuple[Optional[float], Optional[float]]:
        """
        Extract GPS coordinates from parsed EXIF dictionary (piexif format)
        """
        try:
            if "GPS" not in exif_dict:
                return None, None
                
            gps_info = exif_dict["GPS"]
            
            # Extract latitude
            gps_latitude = None
            if 2 in gps_info and 1 in gps_info:  # GPSLatitude and GPSLatitudeRef
                lat_dms = gps_info[2]  # Degrees, minutes, seconds
                lat_ref = gps_info[1].decode('ascii')  # N or S
                
                # Convert to decimal degrees
                lat = self._convert_dms_to_decimal(lat_dms)
                if lat_ref == 'S':
                    lat = -lat
                gps_latitude = lat
            
            # Extract longitude
            gps_longitude = None  
            if 4 in gps_info and 3 in gps_info:  # GPSLongitude and GPSLongitudeRef
                lon_dms = gps_info[4]  # Degrees, minutes, seconds
                lon_ref = gps_info[3].decode('ascii')  # E or W
                
                # Convert to decimal degrees
                lon = self._convert_dms_to_decimal(lon_dms)
                if lon_ref == 'W':
                    lon = -lon
                gps_longitude = lon
                
            return gps_latitude, gps_longitude
            
        except Exception:
            pass  # GPS extraction failed
            
        return None, None
    
    def _convert_dms_to_decimal(self, dms_tuple) -> float:
        """
        Convert degrees/minutes/seconds tuple to decimal degrees
        
        Args:
            dms_tuple: Tuple of ((deg_num, deg_den), (min_num, min_den), (sec_num, sec_den))
            
        Returns:
            Decimal degrees as float
        """
        try:
            # Each coordinate is a tuple of (numerator, denominator)
            degrees = dms_tuple[0][0] / dms_tuple[0][1] if dms_tuple[0][1] != 0 else 0
            minutes = dms_tuple[1][0] / dms_tuple[1][1] if dms_tuple[1][1] != 0 else 0  
            seconds = dms_tuple[2][0] / dms_tuple[2][1] if dms_tuple[2][1] != 0 else 0
            
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        except:
            return 0.0
    
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