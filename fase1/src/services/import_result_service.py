"""
Simplified Import Result Service
Generates user-friendly messages based on import results without complex fingerprinting
"""
from typing import Dict
from models import ImportSession
from enum import Enum


class ImportResultType(Enum):
    """Classification of import results for user feedback"""
    ALL_NEW = "all_new"           # All files were successfully imported (new to system)
    ALL_DUPLICATES = "all_duplicates"  # All files were duplicates (memory card empty/already imported)
    MIXED = "mixed"               # Some new files, some duplicates (memory card wasn't empty)


class ImportResultService:
    """
    Service for analyzing import results and generating appropriate user feedback
    Simple, result-based approach without complex source tracking
    """
    
    @staticmethod
    def classify_import_result(import_session: ImportSession) -> ImportResultType:
        """
        Classify the import result based on statistics
        
        Args:
            import_session: Completed import session with statistics
            
        Returns:
            ImportResultType enum indicating the type of result
        """
        images_imported = getattr(import_session, 'images_imported', 0) or 0
        duplicates_skipped = getattr(import_session, 'duplicates_skipped', 0) or 0
        total_processed = images_imported + duplicates_skipped
        
        if total_processed == 0:
            # No files processed - probably an error case
            return ImportResultType.ALL_NEW  # Default fallback
        
        if images_imported == 0 and duplicates_skipped > 0:
            # Only duplicates found
            return ImportResultType.ALL_DUPLICATES
        
        elif duplicates_skipped == 0 and images_imported > 0:
            # Only new files found
            return ImportResultType.ALL_NEW
        
        else:
            # Mix of new and duplicate files
            return ImportResultType.MIXED
    
    @staticmethod
    def generate_user_message(import_session: ImportSession) -> str:
        """
        Generate user-friendly message based on import results
        
        Args:
            import_session: Completed import session
            
        Returns:
            User-friendly message string
        """
        result_type = ImportResultService.classify_import_result(import_session)
        
        images_imported = getattr(import_session, 'images_imported', 0) or 0
        duplicates_skipped = getattr(import_session, 'duplicates_skipped', 0) or 0
        errors_count = getattr(import_session, 'errors_count', 0) or 0
        
        if result_type == ImportResultType.ALL_NEW:
            if images_imported == 0:
                return "📂 Ingen bildefiler funnet på minnekortet"
            elif images_imported == 1:
                return "✅ 1 bilde er lagret i arkivet"
            else:
                return f"✅ Alle {images_imported} bilder er lagret i arkivet"
        
        elif result_type == ImportResultType.ALL_DUPLICATES:
            if duplicates_skipped == 1:
                return "💿 Minnekortet er tomt eller allerede importert (1 bilde var allerede lagret)"
            else:
                return f"💿 Minnekortet er tomt eller allerede importert ({duplicates_skipped} bilder var allerede lagret)"
        
        elif result_type == ImportResultType.MIXED:
            base_msg = f"⚠️ Minnekortet var ikke tomt - {images_imported} nye bilder importert, {duplicates_skipped} var allerede lagret"
            
            if errors_count > 0:
                base_msg += f" ({errors_count} filer hadde feil)"
            
            return base_msg
        
        # Fallback
        return f"Import fullført: {images_imported} nye, {duplicates_skipped} duplikater"
    
    @staticmethod
    def get_recommendation(import_session: ImportSession) -> str:
        """
        Get recommendation for user based on import result
        
        Args:
            import_session: Completed import session
            
        Returns:
            Recommendation text for user
        """
        result_type = ImportResultService.classify_import_result(import_session)
        
        if result_type == ImportResultType.ALL_NEW:
            return "💡 Anbefaling: Du kan nå trygt slette bildene fra minnekortet"
        
        elif result_type == ImportResultType.ALL_DUPLICATES:
            return "💡 Anbefaling: Disse bildene er allerede sikret. Slett dem fra minnekortet"
        
        elif result_type == ImportResultType.MIXED:
            return "💡 Anbefaling: De nye bildene er sikret. Du kan slette alle bilder fra minnekortet"
        
        return "💡 Kontroller resultatet og slett minnekortet når du er fornøyd"
    
    @staticmethod
    def update_import_session_feedback(import_session: ImportSession) -> None:
        """
        Update import session with classification and user message
        
        Args:
            import_session: Import session to update
        """
        result_type = ImportResultService.classify_import_result(import_session)
        message = ImportResultService.generate_user_message(import_session)
        
        # Update session with results
        setattr(import_session, 'import_result_type', result_type.value)
        setattr(import_session, 'user_feedback_message', message)
    
    @staticmethod
    def get_complete_summary(import_session: ImportSession) -> Dict[str, str]:
        """
        Get complete summary for display to user
        
        Returns:
            Dictionary with message, recommendation, and technical details
        """
        result_type = ImportResultService.classify_import_result(import_session)
        
        summary = {
            "result_type": result_type.value,
            "primary_message": ImportResultService.generate_user_message(import_session),
            "recommendation": ImportResultService.get_recommendation(import_session),
            "technical_summary": ImportResultService._get_technical_summary(import_session)
        }
        
        return summary
    
    @staticmethod
    def _get_technical_summary(import_session: ImportSession) -> str:
        """Generate technical summary for advanced users or logging"""
        images_imported = getattr(import_session, 'images_imported', 0) or 0
        duplicates_skipped = getattr(import_session, 'duplicates_skipped', 0) or 0
        raw_files_skipped = getattr(import_session, 'raw_files_skipped', 0) or 0
        errors_count = getattr(import_session, 'errors_count', 0) or 0
        total_files_found = getattr(import_session, 'total_files_found', 0) or 0
        
        return (f"Tekniske detaljer: {total_files_found} filer funnet, "
                f"{images_imported} importert, {duplicates_skipped} duplikater, "
                f"{raw_files_skipped} RAW-filer hoppet over, {errors_count} feil")


# Example usage
def example_usage():
    """Examples of different import scenarios and their messages"""
    
    scenarios = [
        # Scenario 1: Perfect import - all new files
        {"images_imported": 247, "duplicates_skipped": 0, "errors_count": 0},
        
        # Scenario 2: All duplicates - card already imported
        {"images_imported": 0, "duplicates_skipped": 203, "errors_count": 0},
        
        # Scenario 3: Mixed - card wasn't empty when used
        {"images_imported": 45, "duplicates_skipped": 203, "errors_count": 2},
        
        # Scenario 4: Single file scenarios
        {"images_imported": 1, "duplicates_skipped": 0, "errors_count": 0},
        {"images_imported": 0, "duplicates_skipped": 1, "errors_count": 0},
    ]
    
    print("📝 Import Result Examples:\n")
    
    for i, stats in enumerate(scenarios, 1):
        # Create mock session
        session = type('MockSession', (), stats)()
        
        summary = ImportResultService.get_complete_summary(session)
        
        print(f"Scenario {i}:")
        print(f"  Stats: {stats}")
        print(f"  Message: {summary['primary_message']}")
        print(f"  Recommendation: {summary['recommendation']}")
        print(f"  Technical: {summary['technical_summary']}")
        print()


if __name__ == "__main__":
    example_usage()