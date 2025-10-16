"""
Photo model - Primary display model for photo galleries and browsing
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .author import Author
    from .image import Image
    from .import_session import ImportSession


class Photo(Base, TimestampMixin):
    """
    Primary photo model - aggregated view for galleries and browsing
    
    This is the main table for photo display, search, and user interaction.
    Represents the "concept" of a photo - multiple Image files (JPEG/RAW) 
    can reference the same Photo record via hothash.
    
    Key design principles:
    - hothash as primary key (content-based, shared between JPEG/RAW)
    - Contains all user-facing metadata (title, tags, rating)
    - Contains visual presentation data (hotpreview, dimensions)
    - Optimized for gallery queries and photo browsing
    """
    __tablename__ = "photos"
    
    # Primary key = content-based hash (same for JPEG/RAW pairs)
    hothash = Column(String(64), primary_key=True, index=True)
    
    # Visual presentation data (critical for galleries)
    hotpreview = Column(LargeBinary)  # Fast cached preview for UI
    width = Column(Integer)           # Original image dimensions
    height = Column(Integer)
    user_rotation = Column(Integer, default=0, nullable=False)  # User rotation (0=0°, 1=90°, 2=180°, 3=270°)
    
    # Content metadata (extracted from EXIF)
    taken_at = Column(DateTime)       # When photo was actually taken
    gps_latitude = Column(Float)      # GPS coordinates (if available)
    gps_longitude = Column(Float)
    
    # User metadata (editable by users)
    title = Column(String(255))       # User-assigned title
    description = Column(Text)        # User description/notes
    tags = Column(JSON)               # List of tags ["nature", "landscape"]
    rating = Column(Integer, default=0)  # 1-5 star rating
    
    # Authorship and import tracking
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    
    # Relationships
    files = relationship("Image", back_populates="photo", cascade="all, delete-orphan")
    author = relationship("Author", back_populates="photos")
    # Note: No back_populates to ImportSession - access photos via ImportSession.images[].photo
    
    def __repr__(self):
        return f"<Photo(hash={self.hothash[:8]}..., title='{self.title or 'Untitled'}', files={len(self.files) if self.files else 0})>"
    
    @property
    def has_gps(self) -> bool:
        """Check if photo has GPS coordinates"""
        return self.gps_latitude is not None and self.gps_longitude is not None
    
    @property  
    def jpeg_file(self) -> Optional["Image"]:
        """Get the JPEG file for this photo (if any)"""
        if not self.files:
            return None
        for file in self.files:
            if file.filename.lower().endswith(('.jpg', '.jpeg')):
                return file
        return None
    
    @property
    def raw_file(self) -> Optional["Image"]: 
        """Get the RAW file for this photo (if any)"""
        if not self.files:
            return None
        for file in self.files:
            if file.filename.lower().endswith(('.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.raw')):
                return file
        return None
    
    @property
    def has_raw_companion(self) -> bool:
        """Check if photo has both JPEG and RAW files"""
        return self.jpeg_file is not None and self.raw_file is not None
    
    @property
    def primary_filename(self) -> str:
        """Get the primary filename (prefer JPEG over RAW for display)"""
        jpeg = self.jpeg_file
        if jpeg:
            return getattr(jpeg, 'filename', 'Unknown')
        if self.files:
            return getattr(self.files[0], 'filename', 'Unknown')
        return "Unknown"
    
    # ===== PHOTO CREATION FACTORY METHODS =====
    
    @classmethod
    def create_from_file_group(cls, file_group: List[str], import_session_id: int, db_session=None) -> 'Photo':
        """
        Smart constructor - hovedinngangen for Photo-opprettelse fra filgruppe.
        Håndterer all content-analyse og generering.
        
        Args:
            file_group: Liste med filpaths som tilhører samme foto (1-2 filer)
            import_session_id: Referanse til import session
            db_session: Database session (hvis None, brukes default)
            
        Returns:
            Ferdig Photo med tilknyttede Image records
            
        Raises:
            DuplicatePhotoError: Hvis foto allerede eksisterer
            PhotoCreationError: Ved feil i prosessering
        """
        from pathlib import Path
        
        # Validate file group is not empty
        if not file_group:
            raise ValueError("File group cannot be empty")
        
        # Convert strings to Path objects for easier handling
        file_paths = [Path(f) for f in file_group]
        
        # 1. Analyser filgruppe og velg primær fil
        primary_file = cls._choose_primary_file(file_paths)
        
        # 2. Generer content-basert hash (blir primary key)
        hothash = cls._generate_content_hash(primary_file)
        
        # 3. Duplikatsjekk på photo-nivå
        if cls._exists_by_hash(hothash, db_session):
            from core.exceptions import DuplicateImageError
            raise DuplicateImageError(f"Photo already exists with hash: {hothash}")
        
        # 4. Ekstraher metadata fra primær fil
        metadata = cls._extract_photo_metadata(primary_file)
        
        # 5. Generer hotpreview for galleries
        hotpreview = cls._generate_hotpreview(primary_file)
        
        # 6. Opprett Photo record
        photo = cls(
            hothash=hothash,
            hotpreview=hotpreview,
            width=metadata.get('width'),
            height=metadata.get('height'),
            taken_at=metadata.get('taken_at'),
            gps_latitude=metadata.get('gps_latitude'),
            gps_longitude=metadata.get('gps_longitude'),
            import_session_id=import_session_id
        )
        
        # 7. Opprett Image records for alle filer i gruppen
        from .image import Image
        from pathlib import Path
        for file_path in file_paths:
            # Legacy support - direct Image creation for old background service
            file_path_obj = Path(file_path)
            file_size = file_path_obj.stat().st_size if file_path_obj.exists() else None
            
            image = Image(
                filename=file_path_obj.name,
                file_size=file_size,
                exif_data=None,  # Old method doesn't extract EXIF
                hothash=hothash,
                import_session_id=import_session_id
            )
            photo.files.append(image)
        
        return photo
    
    @staticmethod
    def _choose_primary_file(files: List) -> Optional[str]:
        """
        Velg beste fil for metadata-ekstrahering.
        Prioritering: JPEG > RAW (JPEG er enklere å prosessere)
        
        Args:
            files: Liste med Path objekter
            
        Returns:
            Path til primær fil for prosessering
        """
        from pathlib import Path
        
        # Ensure we have Path objects
        file_paths = [Path(f) if not isinstance(f, Path) else f for f in files]
        
        # Find JPEG files first (preferred for processing)
        jpeg_extensions = {'.jpg', '.jpeg', '.jpe'}
        jpeg_files = [f for f in file_paths if f.suffix.lower() in jpeg_extensions]
        
        if jpeg_files:
            return str(jpeg_files[0])  # Use first JPEG found
        
        # If no JPEG, use first file (probably RAW)
        return str(file_paths[0]) if file_paths else None
    
    @staticmethod
    def _generate_content_hash(file_path) -> str:
        """
        Generer perceptual hash av bildeinnhold.
        Dette blir Photo sin primary key og deles mellom RAW/JPEG.
        
        For now: Bruker fil-hash som placeholder.
        TODO: Implementer ekte perceptual hashing
        """
        import hashlib
        from pathlib import Path
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Placeholder: Use file content hash 
        # In production: Use perceptual hash of image content
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.md5(content).hexdigest()
    
    @staticmethod
    def _extract_photo_metadata(file_path) -> dict:
        """
        Ekstraher EXIF, GPS, dimensjoner fra bildefil.
        Returnerer dictionary med metadata.
        
        Implementerer full EXIF-ekstrahering med PIL og ExifRead
        """
        from pathlib import Path
        from datetime import datetime
        from PIL import Image, ExifTags
        from PIL.ExifTags import TAGS, GPSTAGS
        
        try:
            with Image.open(file_path) as img:
                # Grunnleggende dimensjoner
                width, height = img.size
                
                # Initialiser metadata med default-verdier
                metadata = {
                    'width': width,
                    'height': height,
                    'taken_at': None,
                    'gps_latitude': None,
                    'gps_longitude': None,
                }
                
                # Hent EXIF-data
                exif_dict = img.getexif()
                if exif_dict:
                    
                    # Parse EXIF-tags
                    for tag_id, value in exif_dict.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        # DateTime tatt (prioriter DateTimeOriginal)
                        if tag == 'DateTimeOriginal' or (tag == 'DateTime' and metadata['taken_at'] is None):
                            try:
                                metadata['taken_at'] = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            except (ValueError, TypeError):
                                pass
                        
                        # GPS-data
                        elif tag == 'GPSInfo':
                            # Check if GPSInfo contains actual GPS data (dict) or just an offset (int)
                            if isinstance(value, dict) and hasattr(value, 'items'):
                                gps_data = {}
                                for gps_tag_id, gps_value in value.items():
                                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                    gps_data[gps_tag] = gps_value
                                
                                # Konverter GPS-koordinater til desimalgrader
                                lat = Photo._convert_gps_to_decimal(
                                    gps_data.get('GPSLatitude'),
                                    gps_data.get('GPSLatitudeRef')
                                )
                                lon = Photo._convert_gps_to_decimal(
                                    gps_data.get('GPSLongitude'), 
                                    gps_data.get('GPSLongitudeRef')
                                )
                                
                                if lat is not None and lon is not None:
                                    metadata['gps_latitude'] = lat
                                    metadata['gps_longitude'] = lon
                            else:
                                # GPSInfo contains an offset/reference, not actual GPS data
                                # This is common when GPS data is not present or corrupted
                                pass
                
                return metadata
                
        except Exception as e:
            print(f"Warning: Could not extract metadata from {file_path}: {e}")
            # Fallback for unsupported formats
            return {
                'width': None,
                'height': None,
                'taken_at': None,
                'gps_latitude': None,
                'gps_longitude': None,
            }
    
    @staticmethod
    def _convert_gps_to_decimal(coordinate, direction):
        """
        Konverter GPS-koordinater fra EXIF-format til desimalgrader
        
        Args:
            coordinate: Tuple med (grader, minutter, sekunder)
            direction: 'N', 'S', 'E', eller 'W'
            
        Returns:
            float: Koordinat i desimalgrader, eller None hvis ugyldig
        """
        if not coordinate or not direction:
            return None
            
        try:
            # Konverter fra rasjonelle tall til float
            degrees = float(coordinate[0])
            minutes = float(coordinate[1]) if len(coordinate) > 1 else 0
            seconds = float(coordinate[2]) if len(coordinate) > 2 else 0
            
            # Beregn desimalgrader
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            # Juster for retning (sør og vest er negative)
            if direction in ['S', 'W']:
                decimal = -decimal
                
            return decimal
            
        except (ValueError, TypeError, IndexError):
            return None
    
    @staticmethod
    def _generate_hotpreview(file_path) -> Optional[bytes]:
        """
        Generer ren optimalisert thumbnail for gallery-visning.
        Fast cached version for UI performance.
        
        VIKTIG: Dette er et RENT bilde uten manipulering siden hothash 
        kan genereres fra hotpreview. Branding/ramme må legges til i UI-laget.
        
        - Korrekt EXIF-rotasjon anvendt
        - Ingen ramme eller logo (bevarer bildeinnhold for hashing)
        - Optimalisert størrelse for gallery-visning
        """
        try:
            from PIL import Image, ImageOps
            from io import BytesIO
            
            with Image.open(file_path) as img:
                # Apply EXIF rotation before creating thumbnail
                # This ensures hotpreview shows correct orientation
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail (max 300x300, maintain aspect ratio)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # Convert to RGB for consistent output
                img = img.convert('RGB')
                
                # Convert to JPEG bytes (no manipulation - clean image)
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                return buffer.getvalue()
                
        except Exception as e:
            print(f"Warning: Could not generate hotpreview for {file_path}: {e}")
            return None
    
    @classmethod
    def _exists_by_hash(cls, hothash: str, db_session=None) -> bool:
        """
        Sjekk om Photo allerede eksisterer med denne hashen.
        """
        if db_session is None:
            return False
        
        existing = db_session.query(cls).filter_by(hothash=hothash).first()
        return existing is not None