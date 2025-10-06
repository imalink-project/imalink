"""
Image model for storing individual file metadata
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .photo import Photo


class Image(Base, TimestampMixin):
    """
    File-level image model - represents a single physical image file
    
    This model handles individual files (JPEG, RAW, etc.) and links to 
    the Photo model which contains the shared content metadata.
    
    Key design principles:
    - One record per physical file
    - File-specific data only (filename, size, rotation, EXIF)
    - Links to Photo via photo_hash for shared content metadata
    """
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File-specific information
    filename = Column(String(255), nullable=False)  # Just name + extension, e.g. "IMG_1234.jpg"
    file_size = Column(Integer)  # Size in bytes
    
    # File-specific processing data
    exif_data = Column(LargeBinary)  # Raw EXIF data stored as binary blob
    
    # Link to shared photo content (the "concept" of this photo)
    photo_hash = Column(String(64), ForeignKey('photos.hothash'), nullable=False, index=True)
    
    # Import tracking (file-level)
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    
    # Relationships
    photo = relationship("Photo", back_populates="files")
    import_session = relationship("ImportSession", back_populates="images")
    
    def __repr__(self):
        photo_preview = getattr(self, 'photo_hash', 'Unknown')
        if isinstance(photo_preview, str) and len(photo_preview) > 8:
            photo_preview = photo_preview[:8] + '...'
        return f"<Image(id={self.id}, filename={self.filename}, photo_hash={photo_preview})>"
    
    # ===== IMAGE CREATION FACTORY METHOD =====
    
    @classmethod
    def create_from_file(cls, file_path, photo_hash: str, import_session_id: int) -> 'Image':
        """
        Enkel constructor for fil-metadata.
        Fokuserer kun på fil-spesifikke egenskaper.
        
        Args:
            file_path: Path eller string til bildefilen
            photo_hash: Hash til tilknyttet Photo record
            import_session_id: Referanse til import session
            
        Returns:
            Ferdig Image record klar for database
        """
        from pathlib import Path
        
        # Ensure we have a Path object
        file_path_obj = Path(file_path) if not isinstance(file_path, Path) else file_path
        
        # Extract file-specific metadata
        file_size = None
        if file_path_obj.exists():
            file_size = file_path_obj.stat().st_size
        
        # Extract raw EXIF data for advanced users
        exif_data = cls._extract_raw_exif(file_path_obj)
        
        return cls(
            filename=file_path_obj.name,
            file_size=file_size,
            exif_data=exif_data,
            photo_hash=photo_hash,
            import_session_id=import_session_id
        )
    
    @staticmethod
    def _extract_raw_exif(file_path) -> Optional[bytes]:
        """
        Ekstraher rå EXIF data for avanserte brukere.
        Lagrer som binary blob for full preservering.
        
        TODO: Integrer med exifread eller ImageProcessor
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            with Image.open(file_path) as img:
                exif_dict = img.getexif()
                if exif_dict:
                    # For now, convert to string and encode to bytes
                    # In production: Use proper EXIF binary serialization
                    exif_str = str(dict(exif_dict))
                    return exif_str.encode('utf-8')
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not extract EXIF from {file_path}: {e}")
            return None