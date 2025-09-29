"""
Image processing utilities
Handles EXIF extraction, thumbnail generation, and hashing
"""
import io
import os
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from pathlib import Path

from PIL import Image as PILImage
import piexif
import imagehash
from sqlalchemy.orm import Session

from ..database.models import Image


class ImageProcessor:
    """Handles all image processing operations"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    THUMBNAIL_SIZE = (200, 200)
    
    @staticmethod
    def is_supported_image(file_path: str) -> bool:
        """Check if file is a supported image format"""
        return Path(file_path).suffix.lower() in ImageProcessor.SUPPORTED_FORMATS
    
    @staticmethod
    def generate_perceptual_hash(image_path: str) -> str:
        """Generate perceptual hash for duplicate detection"""
        try:
            with PILImage.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Generate perceptual hash
                hash_value = imagehash.phash(img)
                return str(hash_value)
        except Exception as e:
            print(f"Error generating hash for {image_path}: {e}")
            raise
    
    @staticmethod
    def create_thumbnail(image_path: str) -> bytes:
        """Create thumbnail and return as bytes"""
        try:
            with PILImage.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(ImageProcessor.THUMBNAIL_SIZE, PILImage.Resampling.LANCZOS)
                
                # Save to bytes
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                return buffer.getvalue()
        except Exception as e:
            print(f"Error creating thumbnail for {image_path}: {e}")
            raise
    
    @staticmethod
    def extract_exif_data(image_path: str) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """
        Extract EXIF data and parse key information
        Returns: (raw_exif_bytes, parsed_metadata)
        """
        metadata = {}
        
        try:
            with PILImage.open(image_path) as img:
                # Get raw EXIF data
                raw_exif = img.info.get('exif')
                
                if raw_exif:
                    # Parse EXIF data
                    exif_dict = piexif.load(raw_exif)
                    
                    # Extract key metadata
                    metadata = ImageProcessor._parse_exif_dict(exif_dict)
                
                # Get basic image info
                metadata.update({
                    'width': img.width,
                    'height': img.height,
                    'format': img.format
                })
                
                return raw_exif, metadata
                
        except Exception as e:
            print(f"Error extracting EXIF from {image_path}: {e}")
            return None, metadata
    
    @staticmethod
    def _parse_exif_dict(exif_dict: Dict) -> Dict[str, Any]:
        """Parse EXIF dictionary to extract useful metadata"""
        metadata = {}
        
        try:
            # Date taken
            if "Exif" in exif_dict:
                exif_ifd = exif_dict["Exif"]
                
                # Date and time
                if piexif.ExifIFD.DateTimeOriginal in exif_ifd:
                    date_str = exif_ifd[piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                    try:
                        metadata['taken_at'] = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        pass
            
            # GPS data
            if "GPS" in exif_dict:
                gps_ifd = exif_dict["GPS"]
                lat, lon = ImageProcessor._parse_gps_data(gps_ifd)
                if lat is not None and lon is not None:
                    metadata['gps_latitude'] = lat
                    metadata['gps_longitude'] = lon
            
        except Exception as e:
            print(f"Error parsing EXIF: {e}")
        
        return metadata
    
    @staticmethod
    def _parse_gps_data(gps_ifd: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Parse GPS coordinates from EXIF GPS IFD"""
        try:
            # Get GPS coordinates
            if (piexif.GPSIFD.GPSLatitude in gps_ifd and 
                piexif.GPSIFD.GPSLatitudeRef in gps_ifd and
                piexif.GPSIFD.GPSLongitude in gps_ifd and
                piexif.GPSIFD.GPSLongitudeRef in gps_ifd):
                
                lat_tuple = gps_ifd[piexif.GPSIFD.GPSLatitude]
                lat_ref = gps_ifd[piexif.GPSIFD.GPSLatitudeRef].decode('utf-8')
                lon_tuple = gps_ifd[piexif.GPSIFD.GPSLongitude]
                lon_ref = gps_ifd[piexif.GPSIFD.GPSLongitudeRef].decode('utf-8')
                
                # Convert to decimal degrees
                def convert_to_decimal(coord_tuple):
                    d = coord_tuple[0][0] / coord_tuple[0][1]
                    m = coord_tuple[1][0] / coord_tuple[1][1]
                    s = coord_tuple[2][0] / coord_tuple[2][1]
                    return d + (m / 60.0) + (s / 3600.0)
                
                latitude = convert_to_decimal(lat_tuple)
                if lat_ref == 'S':
                    latitude = -latitude
                
                longitude = convert_to_decimal(lon_tuple)
                if lon_ref == 'W':
                    longitude = -longitude
                
                return latitude, longitude
                
        except Exception as e:
            print(f"Error parsing GPS data: {e}")
        
        return None, None


def create_image_record(
    file_path: str, 
    import_source: str = "manual",
    db: Optional[Session] = None
) -> Optional[Image]:
    """
    Process a single image file and create database record
    
    Args:
        file_path: Path to image file
        import_source: Description of import source
        db: Database session (optional)
    
    Returns:
        Image record if successful, None if failed
    """
    if not ImageProcessor.is_supported_image(file_path):
        print(f"Unsupported file format: {file_path}")
        return None
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    try:
        # Generate perceptual hash
        image_hash = ImageProcessor.generate_perceptual_hash(file_path)
        
        # Check for duplicates if database session provided
        if db:
            existing = db.query(Image).filter(Image.image_hash == image_hash).first()
            if existing:
                print(f"Duplicate image found: {file_path} (matches {existing.original_filename})")
                return None
        
        # Create thumbnail
        thumbnail_data = ImageProcessor.create_thumbnail(file_path)
        
        # Extract EXIF and metadata
        raw_exif, metadata = ImageProcessor.extract_exif_data(file_path)
        
        # Get file info
        file_stat = os.stat(file_path)
        file_path_obj = Path(file_path)
        
        # Create Image record
        image_record = Image(
            image_hash=image_hash,
            original_filename=file_path_obj.name,
            file_path=str(file_path_obj.absolute()),
            file_size=file_stat.st_size,
            file_format=file_path_obj.suffix.lower().lstrip('.'),
            taken_at=metadata.get('taken_at'),
            width=metadata.get('width'),
            height=metadata.get('height'),
            thumbnail=thumbnail_data,
            exif_data=raw_exif,
            gps_latitude=metadata.get('gps_latitude'),
            gps_longitude=metadata.get('gps_longitude'),
            import_source=import_source
        )
        
        return image_record
        
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        return None