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
    - Links to Photo via hothash for shared content metadata
    """
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File-specific information
    filename = Column(String(255), nullable=False)  # Just name + extension, e.g. "IMG_1234.jpg"
    file_size = Column(Integer)  # Size in bytes
    
    # File-specific processing data
    exif_data = Column(LargeBinary)  # Raw EXIF data stored as binary blob
    
    # Link to shared photo content (the "concept" of this photo)
    hothash = Column(String(64), ForeignKey('photos.hothash'), nullable=False, index=True)
    
    # Import tracking (file-level)
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    
    # Relationships
    photo = relationship("Photo", back_populates="files")
    import_session = relationship("ImportSession", back_populates="images")
    
    def __repr__(self):
        photo_preview = getattr(self, 'hothash', 'Unknown')
        if isinstance(photo_preview, str) and len(photo_preview) > 8:
            photo_preview = photo_preview[:8] + '...'
        return f"<Image(id={self.id}, filename={self.filename}, hothash={photo_preview})>"
    
    # ===== CONVENIENCE PROPERTIES =====
    
    @property
    def hotpreview(self) -> Optional[bytes]:
        """
        Get hotpreview from associated Photo.
        Convenient access to preview without needing to load Photo explicitly.
        
        Returns:
            Binary hotpreview data from Photo, or None if no Photo loaded
        """
        return self.photo.hotpreview if self.photo else None
    
    @property 
    def photo_metadata(self) -> dict:
        """
        Get key metadata from associated Photo for quick access.
        
        Returns:
            Dictionary with commonly needed Photo metadata
        """
        if not self.photo:
            return {}
        
        return {
            'title': self.photo.title,
            'width': self.photo.width,
            'height': self.photo.height,
            'taken_at': self.photo.taken_at,
            'has_gps': self.photo.has_gps,
            'rating': self.photo.rating,
        }
    
    # ===== IMAGE CREATION FACTORY METHOD =====
    
    @classmethod
    def create_from_file(cls, file_path, hothash: str, import_session_id: int) -> 'Image':
        """
        Enkel constructor for fil-metadata.
        Fokuserer kun på fil-spesifikke egenskaper.
        
        Args:
            file_path: Path eller string til bildefilen
            hothash: Hash til tilknyttet Photo record
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
            hothash=hothash,
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