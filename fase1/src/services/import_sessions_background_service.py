"""
Background Import Processing Service - Service Layer for ImportSession Background Tasks
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import hashlib
import shutil
import logging
import uuid

from sqlalchemy.orm import Session
from repositories.import_session_repository import ImportSessionRepository
from repositories.image_repository import ImageRepository
from services.importing.image_processor import ImageProcessor
from models import ImportSession, Image

logger = logging.getLogger(__name__)


class ImportSessionsBackgroundService:
    """Service for handling background ImportSession processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.import_repo = ImportSessionRepository(db)
        self.image_repo = ImageRepository(db)
        self.image_processor = ImageProcessor()
    
    def process_directory_import(self, import_id: int, source_path: str) -> bool:
        """
        Process a directory ImportSession in the background
        Returns True if successful, False otherwise
        """
        try:
            # Get ImportSession session
            import_session = self.import_repo.get_import_by_id(import_id)
            if not import_session:
                raise ValueError(f"ImportSession session {import_id} not found")
            
            # Update status to processing
            self.import_repo.update_import(import_id, {"status": "processing"})
            
            # Find image files
            image_files = self._find_image_files(source_path)
            
            # Update total files found
            self.import_repo.update_import(import_id, {"total_files_found": len(image_files)})
            
            # Process each image
            for image_file in image_files:
                success = self._process_single_image(image_file, import_id)
                if not success:
                    self.import_repo.increment_errors(import_id)
            
            # Get updated import session
            import_session = self.import_repo.get_import_by_id(import_id)
            if not import_session:
                raise ValueError(f"Import session {import_id} not found after processing")
            
            # Copy files to storage if enabled (integrated from import_once)
            if getattr(import_session, 'copy_files', True):
                self._copy_files_to_storage(import_id, source_path)
            
            # Generate user feedback and complete import
            self._generate_import_feedback(import_session)
            self.import_repo.complete_import(import_id)
            return True
            
        except Exception as e:
            # Mark as failed
            self.import_repo.fail_import(import_id, str(e))
            return False
    
    def _find_image_files(self, source_path: str) -> list[Path]:
        """Find all image files in the source directory"""
        source_dir = Path(source_path)
        if not source_dir.exists() or not source_dir.is_dir():
            raise ValueError(f"Invalid source directory: {source_path}")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(source_dir.rglob(f'*{ext}'))
            image_files.extend(source_dir.rglob(f'*{ext.upper()}'))
        
        return image_files
    
    def _process_single_image(self, image_file: Path, import_id: int) -> bool:
        """
        Process a single image file
        Returns True if successful, False otherwise
        """
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(image_file)
            
            # Check if image already exists
            if self.image_repo.exists_by_hash(file_hash):
                self.import_repo.increment_duplicates_skipped(import_id)
                return True
            
            # Check for RAW files (skip processing but count)
            if self._is_raw_file(image_file):
                self.import_repo.increment_raw_files_skipped(import_id)
                return True
            
            # Extract metadata using ImageProcessor
            metadata = self.image_processor.extract_metadata(image_file)
            
            # Create image record
            image_data = {
                "image_hash": file_hash,
                "original_filename": image_file.name,
                "file_path": str(image_file),
                "file_size": image_file.stat().st_size,
                "import_source": f"ImportSession {import_id}",
                "import_session_id": import_id,  # Link to import session
                "width": metadata.width,
                "height": metadata.height,
                "exif_data": metadata.exif_data,
                "taken_at": metadata.taken_at,
                "gps_latitude": metadata.gps_latitude,
                "gps_longitude": metadata.gps_longitude
            }
            
            # Use repository to create image (would need to adapt image_repo.create method)
            new_image = Image(**image_data)
            self.db.add(new_image)
            self.db.commit()
            
            self.import_repo.increment_images_imported(import_id)
            return True
            
        except Exception as e:
            print(f"Error processing {image_file}: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.md5(file_content).hexdigest()
    
    def _is_raw_file(self, file_path: Path) -> bool:
        """Check if file is a RAW format"""
        raw_extensions = {'.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2'}
        return file_path.suffix.lower() in raw_extensions
    
    def _generate_import_feedback(self, import_session: ImportSession) -> None:
        """Generate user feedback based on import results"""
        from .import_result_service import ImportResultService
        
        result_service = ImportResultService()
        
        # Classify the import result and generate user message
        result_type = result_service.classify_import_result(import_session)
        user_message = result_service.generate_user_message(import_session)
        
        # Update via repository to ensure proper SQLAlchemy handling
        self.import_repo.update_feedback(import_session.id, result_type.value, user_message)  # type: ignore
    
    def _copy_files_to_storage(self, import_id: int, source_path: str) -> None:
        """
        Copy new files to permanent storage (integrated from import_once)
        Only copies files that were successfully imported to database
        """
        try:
            logger.info(f"Starting file copy to storage for import {import_id}")
            
            # Get import session to check storage settings
            import_session = self.import_repo.get_import_by_id(import_id)
            if not import_session:
                logger.error(f"Import session {import_id} not found for file copying")
                return
            
            # Generate unique storage name and determine full path
            archive_base_path = getattr(import_session, 'archive_base_path', None)
            storage_name = getattr(import_session, 'storage_name', None)
            
            if not storage_name:
                # Generate unique storage name: imalink_YYYYMMDD_uuid
                storage_name = self._generate_storage_name(import_session)
                
            if not archive_base_path:
                # Use default base path
                archive_base_path = "C:/ImaLink/Storage"  # TODO: Make this configurable
            
            # Update import session with storage identifiers
            update_data = {
                "storage_name": storage_name,
                "archive_base_path": archive_base_path
            }
            self.import_repo.update_import(import_id, update_data)
            
            # Create full storage directory path
            storage_dir = Path(archive_base_path) / storage_name
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created unique storage directory for import {import_id}: {storage_dir}")
            
            # Get all successfully imported images from this session
            imported_images = self.image_repo.get_images_by_import_session(import_id)
            logger.info(f"Found {len(imported_images)} imported images for session {import_id}")
            
            files_copied = 0
            files_skipped = 0
            storage_errors = []
            
            # Get source directory to recreate structure
            source_directory = Path(import_session.source_path)
            
            # Collect file metadata for manifest
            archived_files = []
            
            for image in imported_images:
                try:
                    source_file = Path(image.file_path)
                    if not source_file.exists():
                        storage_errors.append(f"Source file not found: {source_file}")
                        continue
                    
                    # Recreate the original directory structure relative to source
                    try:
                        relative_path = source_file.relative_to(source_directory)
                    except ValueError:
                        # Fallback if file is not under source directory
                        relative_path = Path(image.original_filename)
                    
                    dest_file = storage_dir / relative_path
                    
                    # Create parent directories if needed
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    if dest_file.exists():
                        files_skipped += 1
                        continue
                    
                    # Copy file preserving structure
                    shutil.copy2(source_file, dest_file)
                    files_copied += 1
                    
                    # Add to manifest
                    archived_files.append({
                        "original_path": str(source_file),
                        "relative_path": str(relative_path),
                        "archive_path": str(dest_file),
                        "image_hash": image.image_hash,
                        "size_bytes": dest_file.stat().st_size,
                        "width": image.width,
                        "height": image.height,
                        "taken_at": image.taken_at.isoformat() if image.taken_at else None
                    })
                    
                    logger.debug(f"Copied {source_file} -> {dest_file}")
                    
                except Exception as e:
                    error_msg = f"Error copying {image.file_path}: {str(e)}"
                    storage_errors.append(error_msg)
                    logger.error(error_msg)
            
            # Create JSON metadata files
            self._create_images_manifest(storage_dir, archived_files)
            self._create_session_metadata(import_session, storage_dir)
            
            # Update import session with copy results
            update_data = {
                "files_copied": files_copied,
                "files_copy_skipped": files_skipped,
                "storage_errors_count": len(storage_errors)
            }
            self.import_repo.update_import(import_id, update_data)
            
            logger.info(f"File copy completed for import {import_id}: {files_copied} copied, {files_skipped} skipped, {len(storage_errors)} errors")
            
        except Exception as e:
            logger.error(f"Critical error in file copy for import {import_id}: {str(e)}")
            self.import_repo.update_import(import_id, {"storage_errors_count": 1})
    
    def _generate_storage_name(self, import_session: ImportSession) -> str:
        """Generate a unique storage name: imalink_YYYYMMDD_uuid"""
        date_part = datetime.now().strftime("%Y%m%d")
        uuid_part = str(uuid.uuid4())[:8]  # First 8 characters of UUID
        storage_name = f"imalink_{date_part}_{uuid_part}"
        
        return storage_name
    

    
    def _create_images_manifest(self, storage_dir: Path, archived_files: List[Dict]) -> None:
        """Create images_manifest.json with metadata about all copied files"""
        manifest = {
            "created_at": datetime.now().isoformat(),
            "total_files": len(archived_files),
            "total_size_bytes": sum(f.get("size_bytes", 0) for f in archived_files),
            "files": archived_files
        }
        
        manifest_path = storage_dir / "images_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    def _create_session_metadata(self, import_session: ImportSession, storage_dir: Path) -> None:
        """Create import_session.json metadata file"""
        metadata = {
            "import_session_id": import_session.id,
            "storage_name": getattr(import_session, 'storage_name', None),
            "archive_base_path": getattr(import_session, 'archive_base_path', None),
            "created_at": datetime.now().isoformat(),
            "source_path": import_session.source_path,
            "source_description": import_session.source_description,
            "started_at": import_session.started_at.isoformat() if import_session.started_at else None,
            "imalink_version": "fase1",
            "storage_philosophy": "Unique archive naming with imalink_YYYYMMDD_uuid format for easy discovery and portability"
        }
        
        session_file = storage_dir / "import_session.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(metadata, f, indent=2, ensure_ascii=False)