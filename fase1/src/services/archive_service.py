"""
Archive Service - Digital Negative Storage System for ImaLink
Handles the creation and management of permanent original file archives
"""
import os
import uuid
import json
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import hashlib

from models import ImportSession


class ArchiveService:
    """
    Service for managing digital negative archives
    
    Philosophy: "Once and Only Once Import"
    - Original media → Archive → Database
    - Archive becomes authoritative source for re-imports
    - Duplicates are never archived, only reported
    """
    
    def __init__(self, base_archive_path: str):
        """
        Initialize archive service
        
        Args:
            base_archive_path: Root directory for all archives (e.g., "D:/imalink_archives")
        """
        self.base_archive_path = Path(base_archive_path)
        self.base_archive_path.mkdir(parents=True, exist_ok=True)
    
    def create_archive_session(self, import_session: ImportSession) -> str:
        """
        Create a new archive folder for an import session
        
        Returns:
            Archive UUID for tracking
        """
        # Generate UUID and folder name
        archive_uuid = str(uuid.uuid4())
        date_str = datetime.now().strftime("%Y-%m-%d")
        folder_name = f"imalink_{date_str}_{archive_uuid}"
        
        # Update import session with archive info
        import_session.archive_uuid = archive_uuid
        import_session.archive_base_path = str(self.base_archive_path)
        import_session.archive_folder_name = folder_name
        
        # Create archive directory structure
        archive_path = self.base_archive_path / folder_name
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # Create metadata file
        self._create_session_metadata(import_session, archive_path)
        
        return archive_uuid
    
    def archive_file(
        self, 
        source_file: Path, 
        archive_session_path: Path, 
        relative_source_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """
        Copy a single file to the archive, preserving directory structure
        
        Args:
            source_file: Original file path
            archive_session_path: Archive session root directory
            relative_source_path: Relative path from import root to maintain structure
            
        Returns:
            (success, error_message)
        """
        try:
            # Create target path preserving source structure
            target_dir = archive_session_path / "source_structure" / relative_source_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = target_dir / source_file.name
            
            # Copy file
            shutil.copy2(source_file, target_file)
            
            # Verify copy
            if target_file.exists() and target_file.stat().st_size == source_file.stat().st_size:
                return True, None
            else:
                return False, "File size mismatch after copy"
                
        except Exception as e:
            return False, f"Archive copy failed: {str(e)}"
    
    def create_images_manifest(
        self, 
        archive_path: Path, 
        archived_files: List[Dict]
    ) -> None:
        """
        Create images_manifest.json with metadata about all archived files
        
        Args:
            archive_path: Path to archive session folder
            archived_files: List of file metadata dictionaries
        """
        manifest = {
            "created_at": datetime.now().isoformat(),
            "total_files": len(archived_files),
            "total_size_bytes": sum(f.get("size_bytes", 0) for f in archived_files),
            "files": archived_files
        }
        
        manifest_path = archive_path / "images_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    def _create_session_metadata(self, import_session: ImportSession, archive_path: Path) -> None:
        """Create import_session.json metadata file"""
        metadata = {
            "import_session_id": import_session.id,
            "archive_uuid": import_session.archive_uuid,
            "created_at": datetime.now().isoformat(),
            "source_path": import_session.source_path,
            "source_description": import_session.source_description,
            "started_at": import_session.started_at.isoformat() if import_session.started_at else None,
            "imalink_version": "fase1",
            "archive_philosophy": "Once and Only Once Import - Original media digitized to permanent archive"
        }
        
        session_file = archive_path / "import_session.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_archive_path(self, import_session: ImportSession) -> Optional[Path]:
        """Get the full archive path for an import session"""
        if import_session.archive_folder_name:
            return self.base_archive_path / import_session.archive_folder_name
        return None
    
    def verify_archive_integrity(self, archive_path: Path) -> Dict:
        """
        Verify that an archive folder is complete and intact
        
        Returns:
            Dictionary with verification results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_count": 0,
            "total_size": 0
        }
        
        try:
            # Check required files
            session_file = archive_path / "import_session.json"
            manifest_file = archive_path / "images_manifest.json"
            source_dir = archive_path / "source_structure"
            
            if not session_file.exists():
                results["errors"].append("Missing import_session.json")
                results["valid"] = False
            
            if not manifest_file.exists():
                results["errors"].append("Missing images_manifest.json")
                results["valid"] = False
            
            if not source_dir.exists():
                results["errors"].append("Missing source_structure directory")
                results["valid"] = False
            
            # Count files and calculate size
            if source_dir.exists():
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        results["file_count"] += 1
                        results["total_size"] += file_path.stat().st_size
            
        except Exception as e:
            results["errors"].append(f"Verification failed: {str(e)}")
            results["valid"] = False
        
        return results
    
    def find_archive_by_uuid(self, archive_uuid: str) -> Optional[Path]:
        """
        Search for archive folder by UUID
        Useful for recovery scenarios
        """
        for folder in self.base_archive_path.iterdir():
            if folder.is_dir() and archive_uuid in folder.name:
                return folder
        return None
    
    def list_all_archives(self) -> List[Dict]:
        """
        List all archive folders with basic metadata
        """
        archives = []
        
        for folder in self.base_archive_path.iterdir():
            if folder.is_dir() and folder.name.startswith("imalink_"):
                try:
                    session_file = folder / "import_session.json"
                    if session_file.exists():
                        with open(session_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        archives.append({
                            "folder_name": folder.name,
                            "archive_uuid": metadata.get("archive_uuid"),
                            "created_at": metadata.get("created_at"),
                            "source_description": metadata.get("source_description"),
                            "folder_path": str(folder)
                        })
                except Exception:
                    # Skip malformed archives
                    continue
        
        return sorted(archives, key=lambda x: x.get("created_at", ""), reverse=True)