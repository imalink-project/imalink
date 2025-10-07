"""
ImaLink Import Processing Service - MAIN IMPORT LOGIC

🎯 OVERVIEW:
This is the CORE of ImaLink's import functionality. All comprehensive import 
logic and sequential tasks are orchestrated here.

🔍 QUICK NAVIGATION:
- process_directory_import()     ← MAIN WORKFLOW (sekvensielle oppgaver)
- _find_image_files()           ← Filskanning og type-deteksjon  
- _group_raw_jpeg_pairs()       ← Grupperer RAW/JPEG par
- _process_photo_group()        ← Photo-centric behandling (bruker Photo.create_from_file_group)
- _copy_files_to_storage()      ← Filarkivering og struktur-preservering

📋 PHOTO-CENTRIC IMPORT SEQUENCE:
1. Valider import session og oppdater status
2. Skann katalog for bildefiler (rekursivt)
3. Grupper filer etter basename (RAW/JPEG pairing)
4. For hver photo-gruppe: Photo.create_from_file_group() → hash → duplikatsjekk → metadata → database
5. Kopier filer til permanent arkiv med mappestruktur
6. Generer rapport og marker som ferdig

🛠️ MAINTENANCE:
- Ny filtype: _find_image_files() → image_extensions
- Photo-logikk: Photo.create_from_file_group() og relaterte metoder
- Performance: _process_photo_group() (kjører per photo-gruppe)
- Storage: _copy_files_to_storage() (filkopiering og organisering)

📁 RELATED FILES:
- src/services/importing/image_processor.py (metadata extraction)
- src/repositories/ (database operations)  
- python_demos/import_session/ (testing and demos)
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
from core.config import Config
from models import ImportSession, Image, Photo

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
        🎯 MAIN IMPORT WORKFLOW - All sequential import tasks are orchestrated here
        
        This is the CORE METHOD that handles the complete import process:
        1. Validate and setup import session
        2. Discover all image files in source directory  
        3. Process each image (hash, duplicate check, metadata, database)
        4. Copy files to permanent storage with directory structure
        5. Generate completion report and update status
        
        Args:
            import_id: Database ID of the ImportSession to process
            source_path: Directory path containing images to import
            
        Returns:
            bool: True if import completed successfully, False if errors occurred
            
        🔧 MAINTENANCE NOTES:
        - This method orchestrates the entire import pipeline
        - Each step is in a separate private method for maintainability
        - Database transactions are handled at the repository level
        - File operations preserve original directory structure
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
            
            # Group files by basename for RAW/JPEG pairing
            file_groups = self._group_raw_jpeg_pairs(image_files)
            
            # Update total files found (count all individual files)
            self.import_repo.update_import(import_id, {"total_files_found": len(image_files)})
            
            # Process each photo group using Photo-centric approach
            processed_count = 0
            for basename, file_list in file_groups.items():
                # Check if import was cancelled
                import_session = self.import_repo.get_import_by_id(import_id)
                if import_session and getattr(import_session, 'is_cancelled', False):
                    self.import_repo.update_import(import_id, {"status": "cancelled"})
                    return False
                
                # Update progress with current file
                current_file = str(file_list[0]) if file_list else ""
                self.import_repo.update_import(import_id, {
                    "current_file": current_file,
                    "files_processed": processed_count
                })
                
                success = self._process_photo_group(file_list, import_id)
                if not success:
                    self.import_repo.increment_errors(import_id)
                
                processed_count += len(file_list)  # Count individual files processed
            
            # Get updated import session
            import_session = self.import_repo.get_import_by_id(import_id)
            if not import_session:
                raise ValueError(f"Import session {import_id} not found after processing")
            
        # Copy files to storage if enabled (integrated from import_once)
        # TODO: Fix file copying - disabled temporarily due to Image model changes
        # if getattr(import_session, 'copy_files', True):
        #     self._copy_files_to_storage(import_id, source_path)
            
            # Generate user feedback and complete import
            self._generate_import_feedback(import_session)
            self.import_repo.complete_import(import_id)
            
            # Clean up temporary upload directory if this was an upload
            self._cleanup_temp_directory(source_path)
            
            return True
            
        except Exception as e:
            # Mark as failed
            self.import_repo.fail_import(import_id, str(e))
            
            # Clean up temporary upload directory even on failure
            self._cleanup_temp_directory(source_path)
            
            return False
    
    def _find_image_files(self, source_path: str) -> list[Path]:
        """Find all image files in the source directory"""
        source_dir = Path(source_path)
        if not source_dir.exists() or not source_dir.is_dir():
            raise ValueError(f"Invalid source directory: {source_path}")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp', '.dng', '.raw', '.cr2', '.nef', '.arw'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(source_dir.rglob(f'*{ext}'))
            image_files.extend(source_dir.rglob(f'*{ext.upper()}'))
        
        return image_files
    
    def _group_raw_jpeg_pairs(self, image_files: list[Path]) -> dict[str, list[Path]]:
        """
        Group image files by their basename for RAW/JPEG pairing.
        
        Args:
            image_files: List of image file paths
            
        Returns:
            Dict mapping basename to list of files with that basename
            
        Examples:
            IMG_1234.jpg + IMG_1234.RAW -> {"IMG_1234": [Path("IMG_1234.jpg"), Path("IMG_1234.RAW")]}
            IMG_5678.jpg (standalone) -> {"IMG_5678": [Path("IMG_5678.jpg")]}
        """
        file_groups: dict[str, list[Path]] = {}
        
        for file_path in image_files:
            # Get basename without extension
            basename = file_path.stem
            
            # Add file to group
            if basename not in file_groups:
                file_groups[basename] = []
            file_groups[basename].append(file_path)
        
        return file_groups
    
    def _process_photo_group(self, file_list: list[Path], import_id: int) -> bool:
        """
        Process a group of files that represent a single photo (e.g., RAW + JPEG pair).
        Uses Photo-centric approach with factory methods.
        
        Args:
            file_list: List of file paths that belong to the same photo
            import_id: ID of the import session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use Photo factory method to create Photo and associated Images
            # Convert Path objects to strings as expected by factory method
            file_group_str = [str(f) for f in file_list]
            photo = Photo.create_from_file_group(
                file_group=file_group_str,
                import_session_id=import_id,
                db_session=self.db
            )
            
            # Add Photo and its Images to database session
            self.db.add(photo)
            # Images are automatically added via relationship
            
            # Commit to database
            self.db.commit()
            
            # Successfully created photo - increment counter
            self.import_repo.increment_images_imported(import_id)
            return True
            
        except Exception as e:
            # Handle duplicates specifically (check by name since importing specific exception classes can be complex)
            if "DuplicateImageError" in str(type(e)) or "already exists" in str(e) or "duplicate" in str(e).lower():
                self.import_repo.increment_duplicates_skipped(import_id)
                return True
            else:
                # Actual error in processing
                print(f"Error processing photo group {[f.name for f in file_list]}: {e}")
                return False
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
                archive_base_path = Config.TEST_STORAGE_ROOT  # Use config path
            
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
                    # Reconstruct source file path from source_directory and filename
                    # Note: Image model now only has filename, not full file_path
                    source_file = source_directory / image.filename
                    if not source_file.exists():
                        storage_errors.append(f"Source file not found: {source_file}")
                        continue
                    
                    # Recreate the original directory structure relative to source
                    try:
                        relative_path = source_file.relative_to(source_directory)
                    except ValueError:
                        # Fallback if file is not under source directory
                        relative_path = Path(image.filename)
                    
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
                        "hothash": image.hothash,
                        "size_bytes": dest_file.stat().st_size,
                        "width": image.width,
                        "height": image.height,
                        "taken_at": image.taken_at.isoformat() if image.taken_at else None
                    })
                    
                    logger.debug(f"Copied {source_file} -> {dest_file}")
                    
                except Exception as e:
                    error_msg = f"Error copying {image.filename}: {str(e)}"
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
    
    def _cleanup_temp_directory(self, source_path: str) -> None:
        """
        Clean up temporary upload directory if it's a temp directory.
        Only removes directories that match temp upload pattern for safety.
        """
        try:
            source_dir = Path(source_path)
            
            # Only clean up if this looks like our temp upload directory
            if (source_dir.exists() and 
                source_dir.is_dir() and 
                source_dir.name.startswith('imalink_upload_') and
                str(source_dir).startswith('/tmp/')):
                
                logger.info(f"Cleaning up temporary upload directory: {source_dir}")
                shutil.rmtree(source_dir, ignore_errors=True)
                logger.info(f"Successfully cleaned up temp directory: {source_dir}")
            else:
                logger.debug(f"Skipping cleanup - not a temp upload directory: {source_dir}")
                
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {source_path}: {str(e)}")
            # Don't fail the entire import just because cleanup failed