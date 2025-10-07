"""
File System API for image import operations
Handles directory scanning, file detection, and JPEG/RAW pairing
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import mimetypes
import os

router = APIRouter()

# Supported file extensions
SUPPORTED_IMAGE_EXTENSIONS = {
    'jpeg': ['.jpg', '.jpeg'],
    'raw': ['.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2'],
    'other': ['.png', '.tiff', '.tif']
}

ALL_EXTENSIONS = []
for ext_list in SUPPORTED_IMAGE_EXTENSIONS.values():
    ALL_EXTENSIONS.extend(ext_list)


class DirectoryScanRequest(BaseModel):
    directory: str
    recursive: bool = True


class FileInfo(BaseModel):
    path: str
    filename: str
    size: int
    category: str  # 'jpeg', 'raw', 'other'
    extension: str
    base_name: str  # filename without extension


class PhotoPair(BaseModel):
    base_name: str
    jpeg_file: Optional[FileInfo] = None
    raw_file: Optional[FileInfo] = None
    type: str  # 'single_jpeg', 'single_raw', 'jpeg_raw_pair'


class ScanResult(BaseModel):
    directory: str
    total_files: int
    image_files: List[FileInfo]
    photo_pairs: List[PhotoPair]


def get_file_category(filename: str) -> str:
    """Determine file category based on extension"""
    ext = Path(filename).suffix.lower()
    
    if ext in SUPPORTED_IMAGE_EXTENSIONS['jpeg']:
        return 'jpeg'
    elif ext in SUPPORTED_IMAGE_EXTENSIONS['raw']:
        return 'raw'
    elif ext in SUPPORTED_IMAGE_EXTENSIONS['other']:
        return 'other'
    
    return 'unknown'


def get_base_name(filename: str) -> str:
    """Get filename without extension"""
    return Path(filename).stem


def scan_directory(directory_path: str, recursive: bool = True) -> List[FileInfo]:
    """Scan directory for image files"""
    directory = Path(directory_path)
    
    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory_path}")
    
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    image_files = []
    
    # Scan files
    pattern = "**/*" if recursive else "*"
    
    for file_path in directory.glob(pattern):
        if not file_path.is_file():
            continue
            
        ext = file_path.suffix.lower()
        if ext not in ALL_EXTENSIONS:
            continue
            
        try:
            file_info = FileInfo(
                path=str(file_path),
                filename=file_path.name,
                size=file_path.stat().st_size,
                category=get_file_category(file_path.name),
                extension=ext,
                base_name=get_base_name(file_path.name)
            )
            image_files.append(file_info)
        except Exception as e:
            print(f"Warning: Could not process file {file_path}: {e}")
            continue
    
    return image_files


def detect_photo_pairs(image_files: List[FileInfo]) -> List[PhotoPair]:
    """Detect JPEG/RAW pairs and single files"""
    # Group files by base name
    files_by_base = {}
    
    for file_info in image_files:
        base_name = file_info.base_name
        if base_name not in files_by_base:
            files_by_base[base_name] = {'jpeg': None, 'raw': None, 'other': []}
        
        if file_info.category == 'jpeg':
            files_by_base[base_name]['jpeg'] = file_info
        elif file_info.category == 'raw':
            files_by_base[base_name]['raw'] = file_info
        else:
            files_by_base[base_name]['other'].append(file_info)
    
    # Create photo pairs
    photo_pairs = []
    
    for base_name, files in files_by_base.items():
        jpeg_file = files['jpeg']
        raw_file = files['raw']
        other_files = files['other']
        
        # Determine pair type
        if jpeg_file and raw_file:
            pair_type = 'jpeg_raw_pair'
        elif jpeg_file:
            pair_type = 'single_jpeg'
        elif raw_file:
            pair_type = 'single_raw'
        else:
            pair_type = 'other'
        
        photo_pair = PhotoPair(
            base_name=base_name,
            jpeg_file=jpeg_file,
            raw_file=raw_file,
            type=pair_type
        )
        photo_pairs.append(photo_pair)
        
        # Handle other files as separate singles
        for other_file in other_files:
            other_pair = PhotoPair(
                base_name=other_file.base_name,
                jpeg_file=other_file if other_file.category == 'jpeg' else None,
                raw_file=other_file if other_file.category == 'raw' else None,
                type='single_other'
            )
            photo_pairs.append(other_pair)
    
    return photo_pairs


@router.post("/scan", response_model=ScanResult)
async def scan_directory_endpoint(request: DirectoryScanRequest):
    """Scan directory for image files and detect JPEG/RAW pairs"""
    try:
        # Scan for image files
        image_files = scan_directory(request.directory, request.recursive)
        
        # Detect photo pairs
        photo_pairs = detect_photo_pairs(image_files)
        
        result = ScanResult(
            directory=request.directory,
            total_files=len(image_files),
            image_files=image_files,
            photo_pairs=photo_pairs
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/file/{file_path:path}")
async def get_file_info(file_path: str):
    """Get information about a specific file"""
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        file_info = FileInfo(
            path=str(path),
            filename=path.name,
            size=path.stat().st_size,
            category=get_file_category(path.name),
            extension=path.suffix.lower(),
            base_name=get_base_name(path.name)
        )
        
        return {"data": file_info}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@router.get("/validate-directory")
async def validate_directory(path: str = Query(..., description="Directory path to validate")):
    """Validate if directory exists and is accessible"""
    try:
        directory = Path(path)
        
        exists = directory.exists()
        is_dir = directory.is_dir() if exists else False
        readable = os.access(path, os.R_OK) if exists else False
        
        return {
            "path": path,
            "exists": exists,
            "is_directory": is_dir,
            "readable": readable,
            "valid": exists and is_dir and readable
        }
        
    except Exception as e:
        return {
            "path": path,
            "exists": False,
            "is_directory": False,
            "readable": False,
            "valid": False,
            "error": str(e)
        }