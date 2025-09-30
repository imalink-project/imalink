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

from database.models import Image


class ImageProcessor:
    """Handles all image processing operations"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    RAW_FORMATS = {'.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.rw2', '.dng'}
    ALL_FORMATS = SUPPORTED_FORMATS | RAW_FORMATS
    THUMBNAIL_SIZE = (150, 150)  # Optimized for speed and quality balance
    
    @staticmethod
    def is_supported_image(file_path: str) -> bool:
        """Check if file is a supported image format (JPEG/PNG for processing)"""
        return Path(file_path).suffix.lower() in ImageProcessor.SUPPORTED_FORMATS
    
    @staticmethod
    def is_raw_format(file_path: str) -> bool:
        """Check if file is a RAW format"""
        return Path(file_path).suffix.lower() in ImageProcessor.RAW_FORMATS
    
    @staticmethod
    def is_any_supported_format(file_path: str) -> bool:
        """Check if file is any supported format (JPEG, PNG, or RAW)"""
        return Path(file_path).suffix.lower() in ImageProcessor.ALL_FORMATS
    
    @staticmethod
    def generate_perceptual_hash_from_thumbnail(thumbnail_bytes: bytes) -> str:
        """Generate rotation-invariant perceptual hash from thumbnail bytes"""
        try:
            # Load thumbnail from bytes
            thumbnail_img = PILImage.open(io.BytesIO(thumbnail_bytes))
            
            # Generate multiple hashes for different rotations
            hash_0 = imagehash.phash(thumbnail_img)
            hash_90 = imagehash.phash(thumbnail_img.rotate(90, expand=True))
            hash_180 = imagehash.phash(thumbnail_img.rotate(180, expand=True))
            hash_270 = imagehash.phash(thumbnail_img.rotate(270, expand=True))
            
            # Use the lexicographically smallest hash as canonical
            # This ensures same image gets same hash regardless of rotation
            hashes = [str(hash_0), str(hash_90), str(hash_180), str(hash_270)]
            canonical_hash = min(hashes)
            
            return canonical_hash
        except Exception as e:
            print(f"Error generating hash from thumbnail: {e}")
            raise
    
    @staticmethod
    def create_thumbnail_and_hash(image_path: str) -> Tuple[bytes, str]:
        """Create thumbnail and generate hash from it - ensures consistency"""
        try:
            with PILImage.open(image_path) as img:
                # Apply EXIF rotation to correct orientation
                img = ImageProcessor._apply_exif_rotation(img)
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail with exact same parameters every time
                img.thumbnail(ImageProcessor.THUMBNAIL_SIZE, PILImage.Resampling.LANCZOS)
                
                # Save to bytes with consistent settings
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                thumbnail_bytes = buffer.getvalue()
                
                # Generate hash from the thumbnail (not original!)
                hash_value = ImageProcessor.generate_perceptual_hash_from_thumbnail(thumbnail_bytes)
                
                return thumbnail_bytes, hash_value
                
        except Exception as e:
            print(f"Error creating thumbnail and hash for {image_path}: {e}")
            raise
    
    @staticmethod
    def create_thumbnail(image_path: str) -> bytes:
        """Create thumbnail and return as bytes (legacy method - use create_thumbnail_and_hash)"""
        thumbnail_bytes, _ = ImageProcessor.create_thumbnail_and_hash(image_path)
        return thumbnail_bytes
    
    @staticmethod
    def extract_exif_data(image_path: str) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """
        Extract and strip EXIF data, keeping only essential metadata
        Removes: thumbnails, maker notes, large proprietary blocks to save space
        Returns: (stripped_exif_bytes, parsed_metadata)
        """
        metadata = {}
        
        try:
            with PILImage.open(image_path) as img:
                # Get raw EXIF data
                raw_exif = img.info.get('exif')
                
                if raw_exif:
                    # Parse EXIF data
                    exif_dict = piexif.load(raw_exif)
                    
                    # Extract key metadata BEFORE stripping (we need all data for parsing)
                    metadata = ImageProcessor._parse_exif_dict(exif_dict)
                    
                    # Create stripped version keeping only essential tags
                    stripped_exif = ImageProcessor._strip_exif_data(exif_dict)
                    
                    # Convert stripped EXIF back to bytes
                    if stripped_exif:
                        raw_exif = piexif.dump(stripped_exif)
                    else:
                        raw_exif = None
                
                # Get basic image info - apply EXIF rotation to get correct dimensions
                img_rotated = ImageProcessor._apply_exif_rotation(img)
                metadata.update({
                    'width': img_rotated.width,
                    'height': img_rotated.height, 
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

    @staticmethod
    def _apply_exif_rotation(img: PILImage.Image) -> PILImage.Image:
        """
        Apply EXIF orientation to correct image rotation
        This fixes the common problem where portraits show as landscape
        """
        try:
            from PIL import ImageOps
            # Use PIL's built-in EXIF transpose - handles all orientation cases
            rotated_img = ImageOps.exif_transpose(img)
            return rotated_img if rotated_img is not None else img
        except (AttributeError, KeyError, TypeError, Exception):
            # If EXIF processing fails, return original image
            return img

    @staticmethod
    def _strip_exif_data(exif_dict: Dict) -> Dict:
        """
        Strip EXIF data to keep only essential metadata and save space
        Removes: thumbnails, maker notes, proprietary data, large arrays
        """
        # Define essential EXIF tags to keep
        essential_tags = {
            # 0th IFD (main image)
            "0th": {
                271,  # Make (camera manufacturer)
                272,  # Model (camera model)
                274,  # Orientation (CRITICAL for display)
                306,  # DateTime
                315,  # Artist
                33432, # Copyright
                # Remove large/unnecessary: 270 (ImageDescription can be huge)
            },
            # Exif IFD (camera settings)  
            "Exif": {
                33434, # ExposureTime
                33437, # FNumber
                34855, # ISO
                36867, # DateTimeOriginal (when photo was taken)
                36868, # DateTimeDigitized
                37377, # ShutterSpeedValue
                37378, # ApertureValue
                37380, # ExposureBiasValue
                37385, # Flash
                37386, # FocalLength
                41728, # FileSource
                # Remove: 37500 (MakerNote - can be 50KB+)
                # Remove: 40960, 40961, 40962 (FlashPix versions)
            },
            # GPS IFD (location data - keep minimal)
            "GPS": {
                1, 2, 3, 4,  # GPS coordinates (lat/lon + refs)
                5, 6, 7,     # GPS altitude
                29,          # GPS date
                # Remove: detailed GPS tracking data
            }
            # Completely remove: "1st" (thumbnail data - we have our own!)
            # Completely remove: "Interop" (rarely needed)
        }
        
        stripped = {}
        
        for ifd_name, tags in essential_tags.items():
            if ifd_name in exif_dict and exif_dict[ifd_name]:
                stripped[ifd_name] = {}
                for tag_id in tags:
                    if tag_id in exif_dict[ifd_name]:
                        value = exif_dict[ifd_name][tag_id]
                        # Skip extremely large values (>1KB) except orientation
                        if tag_id == 274 or (isinstance(value, (str, bytes)) and len(str(value)) < 1000) or not isinstance(value, (str, bytes)):
                            stripped[ifd_name][tag_id] = value
        
        return stripped

    @staticmethod  
    def rotate_thumbnail_in_db(db: Session, image_id: int) -> Optional[Image]:
        """
        Rotate thumbnail 90 degrees clockwise and update user_rotation field
        Only makes TWO database changes as requested:
        1. Rotate the thumbnail data
        2. Update user_rotation field
        """
        try:
            # Get image record
            image = db.query(Image).filter(Image.id == image_id).first()
            if not image or not image.thumbnail:
                return None
            
            # Load current thumbnail
            thumbnail_img = PILImage.open(io.BytesIO(image.thumbnail))
            
            # Rotate 90 degrees clockwise
            rotated_thumbnail = thumbnail_img.rotate(-90, expand=True)
            
            # Convert back to bytes
            buffer = io.BytesIO()
            rotated_thumbnail.save(buffer, format='JPEG', quality=90, optimize=True)
            new_thumbnail_data = buffer.getvalue()
            
            # Update only TWO fields as requested:
            # 1. Rotate thumbnail
            image.thumbnail = new_thumbnail_data
            # 2. Update user_rotation (0->1->2->3->0)
            image.user_rotation = (image.user_rotation + 1) % 4
            
            db.commit()
            db.refresh(image)
            
            return image
            
        except Exception as e:
            print(f"Error rotating thumbnail for image {image_id}: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return None

    @staticmethod
    def find_raw_companion(jpeg_path: str) -> Optional[str]:
        """
        Find companion RAW file for a JPEG file
        Looks in same directory for files with same base name but RAW extension
        
        Args:
            jpeg_path: Path to JPEG file
            
        Returns:
            Path to RAW file if found, None otherwise
        """
        jpeg_path_obj = Path(jpeg_path)
        base_name = jpeg_path_obj.stem
        directory = jpeg_path_obj.parent
        
        # Check each RAW format
        for raw_ext in ImageProcessor.RAW_FORMATS:
            potential_raw = directory / f"{base_name}{raw_ext}"
            if potential_raw.exists():
                return str(potential_raw)
            
            # Also check uppercase extension  
            potential_raw_upper = directory / f"{base_name}{raw_ext.upper()}"
            if potential_raw_upper.exists():
                return str(potential_raw_upper)
        
        return None

    @staticmethod
    def find_jpeg_companion(raw_path: str) -> Optional[str]:
        """
        Find companion JPEG file for a RAW file
        Looks in same directory for files with same base name but JPEG extension
        
        Args:
            raw_path: Path to RAW file
            
        Returns:
            Path to JPEG file if found, None otherwise
        """
        raw_path_obj = Path(raw_path)
        base_name = raw_path_obj.stem
        directory = raw_path_obj.parent
        
        # Check common JPEG extensions
        for jpeg_ext in ['.jpg', '.jpeg']:
            potential_jpeg = directory / f"{base_name}{jpeg_ext}"
            if potential_jpeg.exists():
                return str(potential_jpeg)
            
            # Also check uppercase extension
            potential_jpeg_upper = directory / f"{base_name}{jpeg_ext.upper()}"
            if potential_jpeg_upper.exists():
                return str(potential_jpeg_upper)
        
        return None


def create_image_record(
    file_path: str, 
    import_source: str = "manual",
    db: Optional[Session] = None
) -> Optional[Image]:
    """
    Process a single image file and create database record
    
    RAW+JPEG Strategy:
    - If file is RAW: Look for JPEG companion, skip if found (JPEG will represent both)
    - If file is JPEG: Process normally, check for RAW companion and link it
    
    Args:
        file_path: Path to image file
        import_source: Description of import source
        db: Database session (optional)
    
    Returns:
        Image record if successful, None if failed or skipped
    """
    # Check if file is supported at all
    if not ImageProcessor.is_any_supported_format(file_path):
        print(f"Unsupported file format: {file_path}")
        return None
    
    # RAW+JPEG strategy: Skip RAW files if JPEG companion exists
    if ImageProcessor.is_raw_format(file_path):
        jpeg_companion = ImageProcessor.find_jpeg_companion(file_path)
        if jpeg_companion:
            print(f"Skipping RAW file {file_path} - JPEG companion found: {jpeg_companion}")
            return None
        else:
            print(f"RAW file without JPEG companion: {file_path} - cannot process (no thumbnail generation)")
            return None
    
    # From here on, we're dealing with processable formats (JPEG, PNG, etc.)
    if not ImageProcessor.is_supported_image(file_path):
        print(f"File format not supported for processing: {file_path}")
        return None
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    try:
        # Create thumbnail and generate hash from it (ensures consistency)
        thumbnail_data, image_hash = ImageProcessor.create_thumbnail_and_hash(file_path)
        
        # Check for duplicates if database session provided
        if db:
            existing = db.query(Image).filter(Image.image_hash == image_hash).first()
            if existing:
                print(f"Duplicate image found: {file_path} (matches {existing.original_filename})")
                return None
        
        # Extract EXIF and metadata
        raw_exif, metadata = ImageProcessor.extract_exif_data(file_path)
        
        # Get file info
        file_stat = os.stat(file_path)
        file_path_obj = Path(file_path)
        
        # Log RAW companion detection for info (not stored in DB)
        if ImageProcessor.is_supported_image(file_path):  # JPEG, PNG, etc.
            raw_companion_path = ImageProcessor.find_raw_companion(file_path)
            if raw_companion_path:
                print(f"Found RAW companion for {file_path}: {raw_companion_path}")
        
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