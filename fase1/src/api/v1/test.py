"""
Test endpoints for frontend-backend synchronization validation
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
import hashlib
import base64
from pathlib import Path

router = APIRouter(prefix="/v1/test", tags=["testing"])

# Hardcoded pilot image data for consistency testing
PILOT_IMAGE_DATA = {
    "filename": "pilot_test.jpg",
    "width": 1920,
    "height": 1080,
    "file_size": 2458762,
    "expected_hothash": "pilot_test_consistent_hash_v1",
    "expected_hotpreview_spec": {
        "width": 300,
        "height": 300,
        "format": "JPEG",
        "quality": 85,
        "crop": "center",
        "color_space": "sRGB"
    }
}

@router.get("/pilot-hash")
async def get_pilot_hash() -> Dict[str, Any]:
    """
    Get the pilot image hash and specifications for frontend testing.
    Frontends should use this to validate their hash generation logic.
    """
    return {
        "pilot_image": PILOT_IMAGE_DATA,
        "hotpreview_spec": PILOT_IMAGE_DATA["expected_hotpreview_spec"],
        "hash_algorithm": "deterministic_content_based",
        "version": "v1"
    }

@router.post("/validate-frontend")
async def validate_frontend_hash(
    filename: str,
    file_size: int,
    width: int,
    height: int,
    frontend_hash: str
) -> Dict[str, Any]:
    """
    Validate that frontend generates the same hash as backend for given parameters.
    This ensures hash consistency across different frontend implementations.
    """
    # Generate backend hash using the same logic
    backend_hash = generate_deterministic_hash(filename, file_size, width, height)
    
    is_valid = frontend_hash == backend_hash
    
    return {
        "valid": is_valid,
        "frontend_hash": frontend_hash,
        "backend_hash": backend_hash,
        "message": "Hash validation successful" if is_valid else "Hash mismatch detected",
        "algorithm_version": "v1"
    }

@router.post("/generate-hash")
async def generate_hash_from_metadata(
    filename: str,
    file_size: int,
    width: int = None,
    height: int = None
) -> Dict[str, str]:
    """
    Generate a consistent hothash from image metadata.
    This is the authoritative hash generation method that frontends should match.
    """
    hothash = generate_deterministic_hash(filename, file_size, width, height)
    
    return {
        "hothash": hothash,
        "algorithm": "deterministic_metadata_based_v1",
        "input": {
            "filename": filename,
            "file_size": file_size,
            "width": width,
            "height": height
        }
    }

def generate_deterministic_hash(filename: str, file_size: int, width: int = None, height: int = None) -> str:
    """
    Generate a deterministic hash based on image metadata.
    This ensures the same image will always get the same hash.
    
    Algorithm:
    1. Normalize filename (remove path, lowercase extension)
    2. Combine filename base, file_size, and dimensions
    3. Generate MD5 hash of combined string
    4. Return first 32 characters
    """
    # Normalize filename - use base name without path, consistent casing
    base_name = Path(filename).stem.lower()
    extension = Path(filename).suffix.lower()
    normalized_filename = f"{base_name}{extension}"
    
    # Create consistent hash input
    hash_input_parts = [
        normalized_filename,
        str(file_size),
    ]
    
    # Add dimensions if available (for more precise deduplication)
    if width and height:
        hash_input_parts.extend([str(width), str(height)])
    
    # Join with consistent separator
    hash_input = "|".join(hash_input_parts)
    
    # Generate MD5 hash
    hash_bytes = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    # Return first 32 characters (standard hothash length)
    return hash_bytes[:32]

@router.get("/health")
async def test_health() -> Dict[str, str]:
    """Health check for test endpoints"""
    return {"status": "ok", "service": "test-validation"}