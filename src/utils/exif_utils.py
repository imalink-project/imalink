"""
EXIF parsing utilities for Photo Corrections

These utilities extract datetime and GPS data from EXIF dictionaries
that are stored in Photo.exif_dict (provided by PhotoEgg from imalink-core server).
"""
from typing import Optional, Dict, Any
from datetime import datetime
import tempfile
import json
from pathlib import Path


def parse_exif_datetime(exif_dict: Optional[Dict[str, Any]]) -> Optional[datetime]:
    """
    Extract datetime from EXIF dictionary
    
    Uses imalink-core's ExifExtractor for consistent parsing.
    
    Args:
        exif_dict: EXIF metadata dictionary from frontend
    
    Returns:
        Parsed datetime or None if not found/invalid
    """
    if not exif_dict:
        return None
    
    # Try common EXIF datetime fields directly
    datetime_fields = ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']
    
    for field in datetime_fields:
        datetime_str = exif_dict.get(field)
        if datetime_str:
            try:
                # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError):
                # Try ISO 8601 format (if frontend already converted)
                try:
                    # Handle ISO format with timezone
                    if isinstance(datetime_str, str):
                        clean_str = datetime_str.replace('Z', '+00:00')
                        return datetime.fromisoformat(clean_str)
                except (ValueError, TypeError, AttributeError):
                    continue
    
    return None


def parse_exif_gps_latitude(exif_dict: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Extract GPS latitude from EXIF dictionary
    
    Expects either:
    - Direct decimal degrees: exif_dict['GPSLatitude'] = 59.9139
    - Or composite format with GPSLatitudeRef
    
    Args:
        exif_dict: EXIF metadata dictionary from frontend
    
    Returns:
        Latitude in decimal degrees or None if not found
    """
    if not exif_dict:
        return None
    
    # Try direct decimal degrees first
    lat = exif_dict.get('GPSLatitude')
    if lat is not None and isinstance(lat, (int, float)):
        # Check if we need to apply hemisphere (N/S)
        lat_ref = exif_dict.get('GPSLatitudeRef', 'N')
        if lat_ref == 'S':
            return -abs(float(lat))
        return float(lat)
    
    return None


def parse_exif_gps_longitude(exif_dict: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Extract GPS longitude from EXIF dictionary
    
    Expects either:
    - Direct decimal degrees: exif_dict['GPSLongitude'] = 10.7522
    - Or composite format with GPSLongitudeRef
    
    Args:
        exif_dict: EXIF metadata dictionary from frontend
    
    Returns:
        Longitude in decimal degrees or None if not found
    """
    if not exif_dict:
        return None
    
    # Try direct decimal degrees first
    lon = exif_dict.get('GPSLongitude')
    if lon is not None and isinstance(lon, (int, float)):
        # Check if we need to apply hemisphere (E/W)
        lon_ref = exif_dict.get('GPSLongitudeRef', 'E')
        if lon_ref == 'W':
            return -abs(float(lon))
        return float(lon)
    
    return None
