"""
Coldpreview Repository Utility
Handles filesystem operations for coldpreview images

This utility provides server-side repository for medium-size preview images (coldpreviews).
Coldpreviews are typically 800-1200px images that provide good quality for photo evaluation
without requiring full resolution downloads.

Key features:
- Configurable repository location via core.config
- Efficient 2-level directory structure for performance  
- Automatic JPEG optimization and resizing
- PIL-based image processing with error handling
- Relative path storage for database references
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image as PILImage
import io

from core.config import Config


class ColdpreviewRepository:
    """Handles coldpreview file storage and retrieval"""
    
    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            # Use configured storage directory + coldpreviews subdirectory
            config = Config()
            # Place coldpreviews alongside database in the same data directory
            self.base_path = Path(config.DATA_DIRECTORY) / "coldpreviews"
        else:
            self.base_path = Path(base_path)
            
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_file_path(self, hothash: str) -> Path:
        """
        Generate filesystem path for coldpreview from hothash
        
        Uses 2-level directory structure for performance:
        hothash "abcd1234567890ef..." → "ab/cd/abcd1234567890ef.jpg"
        """
        dir1 = hothash[:2]
        dir2 = hothash[2:4]
        filename = f"{hothash}.jpg"
        
        return self.base_path / dir1 / dir2 / filename
    
    def save_coldpreview(self, hothash: str, image_data: bytes, 
                        max_size: int = 1200, quality: int = 85) -> Tuple[str, int, int, int]:
        """
        Save coldpreview to filesystem with optional resizing
        
        Args:
            hothash: Photo hash identifier
            image_data: Raw image bytes
            max_size: Maximum dimension (pixels)
            quality: JPEG quality (1-100)
            
        Returns:
            Tuple of (path, width, height, file_size)
        """
        # Validate input
        if not image_data:
            raise ValueError("Image data is empty")
        
        # Process image
        try:
            img = PILImage.open(io.BytesIO(image_data))
            # Verify the image can be read
            img.load()
        except Exception as e:
            raise ValueError(f"Invalid image data: {str(e)}")
        
        # Convert to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if needed (maintain aspect ratio)
        original_width, original_height = img.size
        if max(original_width, original_height) > max_size:
            img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
        
        # Generate file path
        file_path = self.get_file_path(hothash)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JPEG
        img.save(file_path, format='JPEG', quality=quality, optimize=True)
        
        # Get final dimensions and file size
        width, height = img.size
        file_size = file_path.stat().st_size
        
        # Return relative path for database storage (relative to base_path)
        relative_path = str(file_path.relative_to(self.base_path))
        
        return relative_path, width, height, file_size
    
    def load_coldpreview(self, relative_path: str) -> Optional[bytes]:
        """
        Load coldpreview from filesystem
        
        Args:
            relative_path: Path relative to base_path
            
        Returns:
            Image bytes or None if not found
        """
        full_path = self.base_path / relative_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception:
            return None
    
    def resize_coldpreview(self, image_data: bytes, target_width: Optional[int] = None,
                          target_height: Optional[int] = None, target_size: Optional[int] = None,
                          quality: int = 85) -> bytes:
        """
        Resize coldpreview image on-the-fly
        
        Args:
            image_data: Original image bytes
            target_width: Target width (optional)
            target_height: Target height (optional) 
            target_size: Target max dimension (optional)
            quality: JPEG quality
            
        Returns:
            Resized image bytes
        """
        img = PILImage.open(io.BytesIO(image_data))
        original_width, original_height = img.size
        
        # Calculate target dimensions
        if target_size:
            # Resize to fit within target_size (square)
            if max(original_width, original_height) > target_size:
                img.thumbnail((target_size, target_size), PILImage.Resampling.LANCZOS)
        elif target_width and target_height:
            # Resize to specific dimensions (may change aspect ratio)
            img = img.resize((target_width, target_height), PILImage.Resampling.LANCZOS)
        elif target_width:
            # Resize to specific width, maintain aspect ratio
            ratio = target_width / original_width
            new_height = int(original_height * ratio)
            img = img.resize((target_width, new_height), PILImage.Resampling.LANCZOS)
        elif target_height:
            # Resize to specific height, maintain aspect ratio
            ratio = target_height / original_height
            new_width = int(original_width * ratio)
            img = img.resize((new_width, target_height), PILImage.Resampling.LANCZOS)
        
        # Don't upscale - return original if target is larger
        if img.size[0] > original_width or img.size[1] > original_height:
            img = PILImage.open(io.BytesIO(image_data))  # Reset to original
        
        # Convert to JPEG bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    
    def delete_coldpreview(self, relative_path: str) -> bool:
        """
        Delete coldpreview file from filesystem
        
        Args:
            relative_path: Path relative to base_path
            
        Returns:
            True if deleted successfully
        """
        full_path = self.base_path / relative_path
        
        try:
            if full_path.exists():
                full_path.unlink()
                
                # Clean up empty directories
                parent_dir = full_path.parent
                if parent_dir != self.base_path and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    
                    # Check grandparent too
                    grandparent_dir = parent_dir.parent
                    if grandparent_dir != self.base_path and not any(grandparent_dir.iterdir()):
                        grandparent_dir.rmdir()
                
                return True
        except Exception:
            pass
        
        return False
    
    def delete_coldpreview_by_hash(self, hothash: str) -> bool:
        """
        Delete coldpreview file by hothash
        
        Args:
            hothash: Photo hash identifier
            
        Returns:
            True if deleted successfully
        """
        file_path = self.get_file_path(hothash)
        
        try:
            if file_path.exists():
                file_path.unlink()
                
                # Clean up empty directories
                parent_dir = file_path.parent
                if parent_dir != self.base_path and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    
                    # Check grandparent too
                    grandparent_dir = parent_dir.parent
                    if grandparent_dir != self.base_path and not any(grandparent_dir.iterdir()):
                        grandparent_dir.rmdir()
                
                return True
        except Exception:
            pass
        
        return False
    
    def load_coldpreview_by_hash(self, hothash: str) -> Optional[bytes]:
        """
        Load coldpreview by hothash
        
        Args:
            hothash: Photo hash identifier
            
        Returns:
            Image bytes or None if not found
        """
        file_path = self.get_file_path(hothash)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception:
            return None
    
    def exists(self, relative_path: str) -> bool:
        """Check if coldpreview file exists"""
        full_path = self.base_path / relative_path
        return full_path.exists()
    
    def get_repository_stats(self) -> dict:
        """Get repository statistics"""
        total_files = 0
        total_size = 0
        
        for file_path in self.base_path.rglob("*.jpg"):
            total_files += 1
            total_size += file_path.stat().st_size
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "base_path": str(self.base_path)
        }