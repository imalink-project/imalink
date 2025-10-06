"""
File system utilities for handling images and file operations
"""
import os
from pathlib import Path
from typing import List, Optional, Tuple


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(file_path)


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase"""
    return Path(filename).suffix.lower()


def is_image_file(filename: str) -> bool:
    """Check if file is a supported image format"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.raw', '.cr2', '.nef', '.arw'}
    return get_file_extension(filename) in image_extensions


def find_image_files(directory: str, recursive: bool = True) -> List[str]:
    """Find all image files in directory"""
    image_files = []
    path = Path(directory)
    
    if recursive:
        for file_path in path.rglob('*'):
            if file_path.is_file() and is_image_file(file_path.name):
                image_files.append(str(file_path))
    else:
        for file_path in path.iterdir():
            if file_path.is_file() and is_image_file(file_path.name):
                image_files.append(str(file_path))
    
    return sorted(image_files)


def ensure_directory_exists(directory: str) -> None:
    """Create directory if it doesn't exist"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_file_format(filename: str) -> Optional[str]:
    """
    Extract file format from filename extension (without dot).
    
    Args:
        filename: File name with extension (e.g. "IMG_1234.jpg")
        
    Returns:
        File format in lowercase (e.g. "jpg", "cr2", "dng") or None if no extension
    """
    if not filename or '.' not in filename:
        return None
    
    extension = Path(filename).suffix.lower()
    if not extension:
        return None
        
    # Remove the dot
    return extension[1:]


def is_raw_format(filename: str) -> bool:
    """Check if filename represents a RAW format"""
    format_type = get_file_format(filename)
    if not format_type:
        return False
        
    raw_formats = {'cr2', 'nef', 'arw', 'dng', 'orf', 'rw2', 'raw'}
    return format_type in raw_formats


def normalize_filename(filename: str) -> str:
    """
    Normalize filename by ensuring it's just the filename without path.
    
    Args:
        filename: Potentially full path or just filename
        
    Returns:
        Just the filename part
    """
    return Path(filename).name