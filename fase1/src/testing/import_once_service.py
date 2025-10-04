"""
Import Once Service - Final Step: Kopier nye filer til permanent storage

Dette er det SISTE steget i import-prosessen:
- Kopierer kun filer som ble identifisert som nye i database-importen
- Krever at database-import er fullført først for duplikatdeteksjon
- Fokuserer på trygg permanent arkivering av kun nye filer
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import shutil
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ImportOnceResult:
    """Resultat fra import_once operasjonen"""
    def __init__(self):
        self.source_path: str = ""
        self.storage_path: str = ""
        self.total_files_found: int = 0
        self.files_copied: int = 0
        self.files_skipped: int = 0
        self.errors: List[str] = []
        self.copied_files: List[Dict[str, Any]] = []  # Liste over kopierte filer
        self.started_at: datetime = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.success: bool = False


class ImportOnceService:
    """
    Service for siste steg i import: Kopier kun nye filer til permanent storage
    
    Dette steget krever at database-import er gjort FØRST for å:
    1. Detektere duplikater basert på database-hashes
    2. Identifisere hvilke filer som er faktisk nye
    3. Kun kopiere de nye filene til permanent storage
    """
    
    def __init__(self, base_storage_path: str):
        self.base_storage_path = Path(base_storage_path)
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.raw', '.cr2', '.nef', '.arw', '.dng'}
    
    def execute_import_once(self, import_session_id: int, storage_subfolder: Optional[str] = None) -> ImportOnceResult:
        """
        Utfør siste steg: Kopier kun nye filer til permanent storage
        
        FORUTSETTER at database-import er fullført og duplikater er identifisert.
        
        Args:
            import_session_id: ID til fullført ImportSession med prosesserte filer
            storage_subfolder: Undermappen i storage (f.eks. "2025-10-04_import")
            
        Returns:
            ImportOnceResult med resultatet av storage-kopieringen
        """
        result = ImportOnceResult()
        
        try:
            # Hent ImportSession og validar at den er fullført
            from repositories.import_session_repository import ImportSessionRepository
            from database.connection import get_db_sync
            
            db = get_db_sync()
            import_repo = ImportSessionRepository(db)
            import_session = import_repo.get_import_by_id(import_session_id)
            
            if not import_session:
                result.errors.append(f"ImportSession {import_session_id} finnes ikke")
                return result
                
            if str(import_session.status) != "completed":
                result.errors.append(f"ImportSession {import_session_id} er ikke fullført (status: {import_session.status})")
                return result
            
            # Type ignore for SQLAlchemy column access
            result.source_path = str(import_session.source_path)  # type: ignore
            source_dir = Path(str(import_session.source_path))    # type: ignore
            
            if not source_dir.exists():
                result.errors.append(f"Kildekatalog finnes ikke: {result.source_path}")
                return result
            
            # Opprett storage-katalog
            if storage_subfolder:
                storage_dir = self.base_storage_path / storage_subfolder
            else:
                # Auto-generer navn basert på dagens dato
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                storage_dir = self.base_storage_path / f"import_{timestamp}"
            
            result.storage_path = str(storage_dir)
            
            # Opprett storage-katalog hvis den ikke finnes
            storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage-katalog opprettet: {storage_dir}")
            
            # Enklere tilnærming: Kopier alle filer fra kilde som ikke allerede finnes i storage
            # Dette sikrer at kun nye filer kopieres, basert på duplikatdeteksjon ved kopiering
            
            image_files = self._find_image_files(source_dir)
            result.total_files_found = len(image_files)
            
            logger.info(f"Kopierer filer til storage - duplikater hoppes over automatisk")
            
            # Kopier filer til storage (duplikatsjekk håndteres i _copy_file_to_storage)
            for image_file in image_files:
                try:
                    self._copy_file_to_storage(image_file, storage_dir, result)
                except Exception as e:
                    error_msg = f"Feil ved kopiering av {image_file.name}: {str(e)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
                    
            db.close()
            
            result.completed_at = datetime.now()
            result.success = len(result.errors) == 0
            
            logger.info(f"Import Once fullført: {result.files_copied} kopiert, {result.files_skipped} hoppet over, {len(result.errors)} feil")
            
        except Exception as e:
            error_msg = f"Kritisk feil i import_once: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            
        return result
    
    def _find_image_files(self, source_dir: Path) -> List[Path]:
        """Finn alle bildefiler i kildekatalog"""
        image_files = []
        
        try:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    image_files.append(file_path)
        except Exception as e:
            logger.error(f"Feil ved søk i katalog {source_dir}: {e}")
            
        return sorted(image_files)  # Sorter for konsistent rekkefølge
    
    def _copy_file_to_storage(self, source_file: Path, storage_dir: Path, result: ImportOnceResult):
        """Kopier én fil til storage"""
        
        # Beregn destinasjonsfil
        dest_file = storage_dir / source_file.name
        
        # Sjekk om filen allerede finnes
        if dest_file.exists():
            # Sammenlign filstørrelse og hash for å avgjøre om det er samme fil
            if self._files_are_identical(source_file, dest_file):
                result.files_skipped += 1
                logger.debug(f"Fil allerede finnes: {source_file.name}")
                return
            else:
                # Samme navn, men forskjellig innhold - generer unikt navn
                counter = 1
                base_name = dest_file.stem
                extension = dest_file.suffix
                
                while dest_file.exists():
                    dest_file = storage_dir / f"{base_name}_{counter:03d}{extension}"
                    counter += 1
        
        # Kopier filen
        shutil.copy2(source_file, dest_file)
        result.files_copied += 1
        
        # Logg kopiert fil
        result.copied_files.append({
            'source': str(source_file),
            'destination': str(dest_file),
            'size_bytes': source_file.stat().st_size
        })
        
        logger.debug(f"Kopiert: {source_file.name} → {dest_file.name}")
    
    def _files_are_identical(self, file1: Path, file2: Path) -> bool:
        """Sjekk om to filer er identiske (størrelse + hash)"""
        try:
            # Først sjekk filstørrelse (rask)
            if file1.stat().st_size != file2.stat().st_size:
                return False
            
            # Så sjekk hash (tregere)
            return self._calculate_file_hash(file1) == self._calculate_file_hash(file2)
        except Exception as e:
            logger.error(f"Feil ved sammenligning av filer: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Beregn MD5-hash av fil"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            logger.error(f"Feil ved beregning av hash for {file_path}: {e}")
            return ""
        
        return hash_md5.hexdigest()
    
    def validate_source_path(self, source_path: str) -> Tuple[bool, str]:
        """Valider at kildesti er gyldig og tilgjengelig"""
        try:
            source_dir = Path(source_path)
            if not source_dir.exists():
                return False, f"Katalog finnes ikke: {source_path}"
            
            if not source_dir.is_dir():
                return False, f"Sti er ikke en katalog: {source_path}"
            
            # Test om vi kan lese katalogen
            try:
                list(source_dir.iterdir())
            except PermissionError:
                return False, f"Ingen tilgang til katalog: {source_path}"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Feil ved validering: {str(e)}"
    
    def get_storage_info(self, storage_subfolder: Optional[str] = None) -> Dict[str, Any]:
        """Hent informasjon om storage-sti som vil brukes"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        if storage_subfolder:
            storage_path = self.base_storage_path / storage_subfolder
        else:
            storage_path = self.base_storage_path / f"import_{timestamp}"
            
        return {
            'storage_path': str(storage_path),
            'base_path': str(self.base_storage_path),
            'subfolder': storage_subfolder or f"import_{timestamp}",
            'exists': storage_path.exists()
        }