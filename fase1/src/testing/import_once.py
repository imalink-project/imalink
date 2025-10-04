"""
Import Once API endpoints - Kritisk operasjon for filkopiering
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from core.dependencies import get_import_once_service
from schemas.requests.import_once_requests import ImportOnceRequest
from schemas.responses.import_once_responses import ImportOnceResponse, ImportOnceValidationResponse
from services.import_once_service import ImportOnceService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ImportOnceResponse)
async def execute_import_once(
    request: ImportOnceRequest,
    import_once_service: ImportOnceService = Depends(get_import_once_service)
) -> ImportOnceResponse:
    """
    Utfør den kritiske import_once operasjonen: Kopier filer fra kilde til storage
    
    Dette er den mest kritiske operasjonen som MÅ gjøres først.
    Den kopierer alle bildefiler fra kilden (f.eks. SD-kort) til permanent storage.
    """
    try:
        logger.info(f"Starting import_once: session {request.import_session_id} → {request.storage_path}")
        
        # Utfør den kritiske operasjonen
        result = import_once_service.execute_import_once(
            import_session_id=request.import_session_id,
            storage_subfolder=request.storage_subfolder
        )
        
        # Konverter til response
        response = ImportOnceResponse(
            success=result.success,
            source_path=result.source_path,
            storage_path=result.storage_path,
            total_files_found=result.total_files_found,
            files_copied=result.files_copied,
            files_skipped=result.files_skipped,
            errors=result.errors,
            started_at=result.started_at,
            completed_at=result.completed_at,
            copied_files=result.copied_files
        )
        
        if result.success:
            logger.info(f"Import_once completed successfully: {result.files_copied} files copied")
        else:
            logger.warning(f"Import_once completed with errors: {len(result.errors)} errors")
            
        return response
        
    except Exception as e:
        logger.error(f"Critical error in import_once: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Kritisk feil i import_once operasjon: {str(e)}"
        )


@router.post("/validate", response_model=ImportOnceValidationResponse)
async def validate_import_once_paths(
    request: ImportOnceRequest,
    import_once_service: ImportOnceService = Depends(get_import_once_service)
) -> ImportOnceValidationResponse:
    """
    Valider stier før import_once operasjon
    
    Sjekker at kilde-sti er tilgjengelig og storage-sti er skrivbar.
    """
    try:
        # Valider kilde-sti
        source_valid, source_message = import_once_service.validate_source_path(request.source_path)
        
        if not source_valid:
            return ImportOnceValidationResponse(
                valid=False,
                message=f"Kilde-sti ugyldig: {source_message}",
                source_info={"path": request.source_path, "error": source_message}
            )
        
        # Hent storage-informasjon
        storage_info = import_once_service.get_storage_info(request.storage_subfolder)
        
        return ImportOnceValidationResponse(
            valid=True,
            message="Stier validert - klar for import_once operasjon",
            source_info={
                "path": request.source_path,
                "exists": True,
                "accessible": True
            },
            storage_info=storage_info
        )
        
    except Exception as e:
        logger.error(f"Error validating import_once paths: {str(e)}")
        return ImportOnceValidationResponse(
            valid=False,
            message=f"Valideringsfeil: {str(e)}"
        )


@router.get("/storage-info")
async def get_storage_info(
    subfolder: str = None,
    import_once_service: ImportOnceService = Depends(get_import_once_service)
) -> Dict[str, Any]:
    """
    Hent informasjon om storage-sti som vil bli brukt
    """
    try:
        return import_once_service.get_storage_info(subfolder)
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Feil ved henting av storage-informasjon: {str(e)}"
        )