"""
File location service for finding files via ImportSession storage system
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models.photo import Photo
from ..models.image import Image
from ..models.import_session import ImportSession
from ..core.config import Config


@dataclass
class FileLocation:
    """Location information for an image file"""
    found: bool
    full_path: Optional[str] = None
    directory_name: Optional[str] = None
    import_session_id: Optional[int] = None
    storage_root: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class StorageStatus:
    """Overall storage status for a photo or import session"""
    accessible: bool
    total_files: int
    found_files: int
    missing_files: int
    storage_root: Optional[str] = None
    directory_name: Optional[str] = None
    error_message: Optional[str] = None


class FileLocationService:
    """Service for finding files via ImportSession storage system"""
    
    def __init__(self, db: Session, storage_root: Optional[str] = None):
        self.db = db
        # No default storage root - must be provided by frontend/user
        if storage_root is None:
            raise ValueError("storage_root must be provided - no default backend storage root")
        self.storage_root = storage_root
    
    def set_storage_root(self, storage_root: str) -> bool:
        """Set storage root path (e.g., 'X:', 'X:\\my photo storage')"""
        try:
            root_path = Path(storage_root)
            if not root_path.exists():
                return False
            self.storage_root = str(root_path)
            return True
        except Exception:
            return False
    
    def get_storage_root(self) -> str:
        """Get current storage root path"""
        return self.storage_root
    
    def find_image_file(self, image: Image) -> FileLocation:
        """
        Find an image file by going through Photo -> ImportSession -> Storage directory
        
        Args:
            image: Image record to locate
            
        Returns:
            FileLocation with found status and path information
        """
        try:
            # Get the Photo associated with this Image
            photo = self.db.query(Photo).filter(Photo.hothash == image.hothash).first()
            if not photo:
                return FileLocation(
                    found=False,
                    error_message=f"No Photo found for image {image.filename}"
                )
            
            # Get ImportSession from the Image
            if not image.import_session_id:
                return FileLocation(
                    found=False,
                    error_message=f"Image {image.filename} has no import session reference"
                )
            
            import_session = self.db.query(ImportSession).filter(
                ImportSession.id == image.import_session_id
            ).first()
            
            if not import_session:
                return FileLocation(
                    found=False,
                    error_message=f"ImportSession {image.import_session_id} not found"
                )
            
            # Check if ImportSession has storage directory
            if not import_session.storage_directory_name:
                return FileLocation(
                    found=False,
                    import_session_id=import_session.id,
                    error_message=f"ImportSession {import_session.id} has no storage directory configured"
                )
            
            # Look for storage directory in storage root
            storage_dir_path = self._find_storage_directory(import_session.storage_directory_name)
            if not storage_dir_path:
                return FileLocation(
                    found=False,
                    directory_name=import_session.storage_directory_name,
                    import_session_id=import_session.id,
                    storage_root=self.storage_root,
                    error_message=f"Storage directory '{import_session.storage_directory_name}' not found in {self.storage_root}"
                )
            
            # Look for the specific image file
            image_file_path = storage_dir_path / "files" / image.filename
            if image_file_path.exists():
                return FileLocation(
                    found=True,
                    full_path=str(image_file_path),
                    directory_name=import_session.storage_directory_name,
                    import_session_id=import_session.id,
                    storage_root=self.storage_root
                )
            else:
                return FileLocation(
                    found=False,
                    directory_name=import_session.storage_directory_name,
                    import_session_id=import_session.id,
                    storage_root=self.storage_root,
                    error_message=f"Image file '{image.filename}' not found in storage directory"
                )
                
        except Exception as e:
            return FileLocation(
                found=False,
                error_message=f"Error locating image {image.filename}: {str(e)}"
            )
    
    def get_photo_storage_status(self, photo: Photo) -> StorageStatus:
        """
        Get storage status for all files associated with a photo
        
        Args:
            photo: Photo to check storage status for
            
        Returns:
            StorageStatus with overall accessibility information
        """
        try:
            # Get all images for this photo
            images = self.db.query(Image).filter(Image.hothash == photo.hothash).all()
            
            if not images:
                return StorageStatus(
                    accessible=False,
                    total_files=0,
                    found_files=0,
                    missing_files=0,
                    error_message="No image files found for this photo"
                )
            
            found_files = 0
            missing_files = 0
            directory_name = None
            storage_root = self.storage_root
            errors = []
            
            for image in images:
                location = self.find_image_file(image)
                if location.found:
                    found_files += 1
                    if directory_name is None:
                        directory_name = location.directory_name
                else:
                    missing_files += 1
                    if location.error_message:
                        errors.append(f"{image.filename}: {location.error_message}")
            
            return StorageStatus(
                accessible=found_files > 0,
                total_files=len(images),
                found_files=found_files,
                missing_files=missing_files,
                storage_root=storage_root,
                directory_name=directory_name,
                error_message="; ".join(errors) if errors else None
            )
            
        except Exception as e:
            return StorageStatus(
                accessible=False,
                total_files=0,
                found_files=0,
                missing_files=0,
                error_message=f"Error checking photo storage status: {str(e)}"
            )
    
    def get_import_session_storage_status(self, import_session: ImportSession) -> StorageStatus:
        """
        Get storage status for an entire import session
        
        Args:
            import_session: ImportSession to check
            
        Returns:
            StorageStatus with directory accessibility information
        """
        try:
            if not import_session.storage_directory_name:
                return StorageStatus(
                    accessible=False,
                    total_files=0,
                    found_files=0,
                    missing_files=0,
                    error_message="ImportSession has no storage directory configured"
                )
            
            # Find storage directory
            storage_dir_path = self._find_storage_directory(import_session.storage_directory_name)
            if not storage_dir_path:
                return StorageStatus(
                    accessible=False,
                    total_files=0,
                    found_files=0,
                    missing_files=0,
                    storage_root=self.storage_root,
                    directory_name=import_session.storage_directory_name,
                    error_message=f"Storage directory '{import_session.storage_directory_name}' not found in {self.storage_root}"
                )
            
            # Count files in storage directory
            files_dir = storage_dir_path / "files"
            if not files_dir.exists():
                return StorageStatus(
                    accessible=False,
                    total_files=0,
                    found_files=0,
                    missing_files=0,
                    storage_root=self.storage_root,
                    directory_name=import_session.storage_directory_name,
                    error_message="Files subdirectory not found in storage directory"
                )
            
            # Count actual files
            found_files = len([f for f in files_dir.rglob("*") if f.is_file()])
            expected_files = import_session.total_files_found or 0
            
            return StorageStatus(
                accessible=True,
                total_files=expected_files,
                found_files=found_files,
                missing_files=max(0, expected_files - found_files),
                storage_root=self.storage_root,
                directory_name=import_session.storage_directory_name
            )
            
        except Exception as e:
            return StorageStatus(
                accessible=False,
                total_files=0,
                found_files=0,
                missing_files=0,
                error_message=f"Error checking import session storage: {str(e)}"
            )
    
    def _find_storage_directory(self, directory_name: str) -> Optional[Path]:
        """
        Find storage directory by name in storage root
        
        Args:
            directory_name: Name of the storage directory to find
            
        Returns:
            Path to directory if found, None otherwise
        """
        try:
            storage_root = Path(self.storage_root)
            if not storage_root.exists():
                return None
            
            # Search for directory in storage root
            for item in storage_root.iterdir():
                if item.is_dir() and item.name == directory_name:
                    return item
            
            return None
            
        except Exception:
            return None
    
    def list_available_storage_directories(self) -> List[Dict[str, Any]]:
        """
        List all storage directories found in storage root
        
        Returns:
            List of directory information dictionaries
        """
        try:
            storage_root = Path(self.storage_root)
            if not storage_root.exists():
                return []
            
            directories = []
            for item in storage_root.iterdir():
                if item.is_dir():
                    # Check if it looks like an ImportSession storage directory
                    files_dir = item / "files"
                    metadata_file = item / "metadata.json"
                    
                    directories.append({
                        "name": item.name,
                        "full_path": str(item),
                        "has_files_dir": files_dir.exists(),
                        "has_metadata": metadata_file.exists(),
                        "file_count": len([f for f in files_dir.rglob("*") if f.is_file()]) if files_dir.exists() else 0,
                        "size_mb": sum(f.stat().st_size for f in item.rglob("*") if f.is_file()) // (1024 * 1024)
                    })
            
            # Sort by name (which includes date prefix)
            directories.sort(key=lambda x: x["name"])
            return directories
            
        except Exception as e:
            return []


# Export singleton-like function
def get_file_location_service(db: Session, storage_root: Optional[str] = None) -> FileLocationService:
    """Get FileLocationService instance"""
    return FileLocationService(db, storage_root)