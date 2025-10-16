"""
Image utilities for hotpreview generation
"""
from PIL import Image, ImageOps
import io
import base64
import hashlib
from pathlib import Path
from typing import Optional, Tuple


def generate_hotpreview(image_path: str, size: Tuple[int, int] = (150, 150)) -> Optional[str]:
    """
    Generate hotpreview from image file
    
    Process:
    1. Open image
    2. Apply EXIF rotation (exif_transpose)
    3. Resize to 150x150 using thumbnail method
    4. Strip all EXIF metadata
    5. Convert to JPEG
    6. Base64 encode
    
    Args:
        image_path: Path to image file
        size: Tuple of (width, height) for hotpreview
    
    Returns:
        Base64-encoded JPEG string, or None if failed
    """
    try:
        if not Path(image_path).exists():
            return None
        
        # Open image
        with Image.open(image_path) as img:
            # CRITICAL: Apply EXIF rotation before processing
            img_fixed = ImageOps.exif_transpose(img.copy())
            
            if img_fixed is None:
                img_fixed = img.copy()
            
            # Convert to RGB if needed (handles RGBA, P, etc.)
            if img_fixed.mode not in ('RGB', 'L'):
                img_fixed = img_fixed.convert('RGB')
            
            # Resize to hotpreview size
            # thumbnail() maintains aspect ratio and fits within size
            img_fixed.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save as JPEG without EXIF metadata
            buffer = io.BytesIO()
            img_fixed.save(
                buffer,
                format='JPEG',
                quality=85,
                optimize=True,
                exif=b''  # Strip all EXIF
            )
            
            # Get bytes and base64 encode
            jpeg_bytes = buffer.getvalue()
            base64_string = base64.b64encode(jpeg_bytes).decode('utf-8')
            
            return base64_string
            
    except Exception as e:
        print(f"Error generating hotpreview for {image_path}: {e}")
        return None


def generate_hothash(hotpreview_base64: str) -> str:
    """
    Generate hothash from base64-encoded hotpreview
    Uses SHA256 like the backend
    
    Args:
        hotpreview_base64: Base64-encoded hotpreview JPEG
    
    Returns:
        Hex string of SHA256 hash
    """
    # Decode base64 to bytes
    hotpreview_bytes = base64.b64decode(hotpreview_base64)
    
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(hotpreview_bytes)
    return hash_obj.hexdigest()


def get_image_info(image_path: str) -> dict:
    """
    Get basic image information
    
    Returns:
        Dictionary with filename, file_size, dimensions, format
    """
    path = Path(image_path)
    
    try:
        with Image.open(image_path) as img:
            return {
                "filename": path.name,
                "file_size": path.stat().st_size,
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode
            }
    except Exception as e:
        return {
            "filename": path.name,
            "file_size": path.stat().st_size if path.exists() else 0,
            "error": str(e)
        }
