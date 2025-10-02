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