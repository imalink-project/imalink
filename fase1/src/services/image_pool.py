#!/usr/bin/env python3
"""
Image Pool Service for ImaLink

Provides optimized, cached versions of images in multiple sizes.
Uses algorithmically generated file paths based on image hash.

Features:
- Cascading scaling optimization (large -> medium -> small)
- Anti-upscaling protection
- EXIF rotation baked in, EXIF data stripped
- Hash-based directory structure for performance
"""

from pathlib import Path
from PIL import Image, ImageOps
import logging
from typing import Dict, Tuple, Optional, List
import time

logger = logging.getLogger(__name__)

class ImagePoolService:
    """
    Service for managing a pool of optimized image versions
    
    File structure: pool/{hash[:2]}/{hash[2:4]}/{hash}_{size}.jpg
    Example: pool/ab/cd/abcd1234ef567890_medium.jpg
    """
    
    def __init__(self, pool_root: str):
        self.pool_root = Path(pool_root)
        self.pool_root.mkdir(parents=True, exist_ok=True)
        
        # Pool sizes in descending order for cascading optimization
        self.sizes = {
            "large": (1200, 1200),   # High quality viewing
            "medium": (800, 800),    # Standard web viewing  
            "small": (400, 400)      # Gallery thumbnails (larger than DB thumbnail)
        }
        
        # Processing order for cascading (largest first)
        self.cascade_order = ["large", "medium", "small"]
        
        logger.info(f"Image pool initialized at: {self.pool_root}")
    
    def _get_pool_path(self, image_hash: str, size: str) -> Path:
        """
        Generate algorithmically determined pool file path
        
        Args:
            image_hash: Hash of the original image
            size: Size name (large, medium, small)
            
        Returns:
            Relative path within pool: ab/cd/abcd1234_{size}.jpg
        """
        if size not in self.sizes:
            raise ValueError(f"Invalid size '{size}'. Valid: {list(self.sizes.keys())}")
        
        # Use first 4 chars of hash for 2-level directory structure
        level1 = image_hash[:2]   # 256 directories (00-ff)
        level2 = image_hash[2:4]  # 256 subdirectories per level1
        
        filename = f"{image_hash}_{size}.jpg"
        return Path(level1) / level2 / filename
    
    def get_full_path(self, image_hash: str, size: str) -> Path:
        """Get full filesystem path to pool file"""
        return self.pool_root / self._get_pool_path(image_hash, size)
    
    def exists(self, image_hash: str, size: str) -> bool:
        """Check if pool version exists"""
        return self.get_full_path(image_hash, size).exists()
    
    def _calculate_target_size(self, original_size: Tuple[int, int], max_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculate target size without upscaling
        
        Args:
            original_size: (width, height) of source image
            max_size: (max_width, max_height) constraints
            
        Returns:
            (target_width, target_height) - never larger than original
        """
        orig_width, orig_height = original_size
        max_width, max_height = max_size
        
        # If original is smaller than max on both axes, keep original size
        if orig_width <= max_width and orig_height <= max_height:
            return original_size
        
        # Calculate aspect ratio and scale down
        aspect_ratio = orig_width / orig_height
        
        if orig_width > orig_height:
            # Landscape: constrain width
            target_width = min(orig_width, max_width)
            target_height = int(target_width / aspect_ratio)
            
            # Ensure height doesn't exceed limit
            if target_height > max_height:
                target_height = min(orig_height, max_height)
                target_width = int(target_height * aspect_ratio)
        else:
            # Portrait: constrain height
            target_height = min(orig_height, max_height)
            target_width = int(target_height * aspect_ratio)
            
            # Ensure width doesn't exceed limit
            if target_width > max_width:
                target_width = min(orig_width, max_width)
                target_height = int(target_width / aspect_ratio)
        
        return (target_width, target_height)
    
    def create_pool_version(
        self,
        source_image: Image.Image,
        image_hash: str,
        size: str,
        quality: int = 85
    ) -> Path:
        """
        Create single pool version from PIL Image
        
        Args:
            source_image: PIL Image object (already EXIF-corrected)
            image_hash: Hash of original image
            size: Target size name
            quality: JPEG quality (1-100)
            
        Returns:
            Path to created pool file
        """
        if size not in self.sizes:
            raise ValueError(f"Invalid size: {size}")
        
        pool_path = self.get_full_path(image_hash, size)
        
        # Skip if already exists
        if pool_path.exists():
            logger.debug(f"Pool version already exists: {pool_path}")
            return pool_path
        
        # Ensure directory exists
        pool_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate target size without upscaling
        max_size = self.sizes[size]
        current_size = source_image.size
        target_size = self._calculate_target_size(current_size, max_size)
        
        logger.debug(f"Creating {size}: {current_size} -> {target_size} (max: {max_size})")
        
        # Create working copy
        working_image = source_image.copy()
        
        # Scale only if necessary
        if target_size != current_size:
            working_image.thumbnail(target_size, Image.Resampling.LANCZOS)
            logger.debug(f"Scaled {size} to {working_image.size}")
        else:
            logger.debug(f"No scaling needed for {size}")
        
        # Save as JPEG without EXIF data
        working_image.save(
            pool_path,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True
            # Explicitly no exif parameter - strips all EXIF data
        )
        
        file_size_kb = pool_path.stat().st_size / 1024
        logger.info(f"Created pool {size}: {pool_path} ({file_size_kb:.1f} KB)")
        
        return pool_path
    
    def create_all_sizes_optimized(
        self,
        original_path: Path,
        image_hash: str,
        quality: int = 85
    ) -> Dict[str, Path]:
        """
        Create all pool sizes using cascading optimization
        
        Process:
        1. Load original once and apply EXIF rotation
        2. Strip all EXIF data
        3. Create large version
        4. Use large to create medium (faster than from original)
        5. Use medium to create small (fastest)
        
        Args:
            original_path: Path to original image file
            image_hash: Hash of original image
            quality: JPEG quality for all versions
            
        Returns:
            Dict mapping size names to created file paths
        """
        start_time = time.time()
        created_paths = {}
        current_image = None
        current_size = None
        
        try:
            # Load original and fix EXIF rotation ONCE
            with Image.open(original_path) as original:
                # CRITICAL: Apply EXIF rotation before any processing
                original_fixed = ImageOps.exif_transpose(original.copy())
                
                # Strip EXIF data (not needed in pool files)
                if hasattr(original_fixed, '_getexif') and hasattr(original_fixed, 'info'):
                    original_fixed.info.pop('exif', None)
                
                original_size = original_fixed.size
                current_image = original_fixed
                current_size = original_size
            
            logger.info(f"Processing {image_hash}: original size {original_size[0]}x{original_size[1]} (post-EXIF)")
            
            # Process sizes in descending order for cascading
            for size_name in self.cascade_order:
                try:
                    # Create from current image (cascading optimization)
                    pool_path = self.create_pool_version(
                        current_image, 
                        image_hash, 
                        size_name, 
                        quality
                    )
                    
                    created_paths[size_name] = pool_path
                    
                    # Load created image as source for next size (cascading)
                    # This is more memory efficient than keeping all in RAM
                    if size_name != self.cascade_order[-1]:  # Not the last size
                        with Image.open(pool_path) as next_source:
                            current_image = next_source.copy()
                            current_size = current_image.size
                        
                        logger.debug(f"Loaded {size_name} as source for next size: {current_size}")
                    
                except Exception as e:
                    logger.error(f"Failed to create {size_name} for {image_hash}: {e}")
                    # Continue with other sizes
            
            elapsed = time.time() - start_time
            logger.info(f"Created {len(created_paths)} pool versions in {elapsed:.2f}s: {list(created_paths.keys())}")
            
        except Exception as e:
            logger.error(f"Error creating pool sizes for {image_hash}: {e}")
            
            # Cleanup any partially created files
            for created_path in created_paths.values():
                if created_path.exists():
                    try:
                        created_path.unlink()
                        logger.debug(f"Cleaned up partial file: {created_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup {created_path}: {cleanup_error}")
            
            raise
        
        return created_paths
    
    def get_or_create(
        self,
        original_path: Path,
        image_hash: str,
        size: str,
        quality: int = 85
    ) -> Path:
        """
        Get existing pool version or create on-demand
        
        Args:
            original_path: Path to original image
            image_hash: Hash of original image  
            size: Requested size name
            quality: JPEG quality if creating new
            
        Returns:
            Path to pool file (existing or newly created)
        """
        pool_path = self.get_full_path(image_hash, size)
        
        if pool_path.exists():
            logger.debug(f"Using existing pool file: {pool_path}")
            return pool_path
        
        logger.info(f"Creating on-demand pool version: {size} for {image_hash}")
        
        # Create single version on-demand
        with Image.open(original_path) as original:
            original_fixed = ImageOps.exif_transpose(original.copy())
            if hasattr(original_fixed, '_getexif') and hasattr(original_fixed, 'info'):
                original_fixed.info.pop('exif', None)
            
            return self.create_pool_version(original_fixed, image_hash, size, quality)
    
    def analyze_original_requirements(self, original_path: Path) -> Dict:
        """
        Analyze original image to determine which pool sizes are needed
        
        Returns:
            Analysis dict with size requirements
        """
        with Image.open(original_path) as img:
            img_fixed = ImageOps.exif_transpose(img.copy())
            original_size = img_fixed.size
            orig_width, orig_height = original_size
        
        analysis = {
            "original_size": original_size,
            "original_megapixels": (orig_width * orig_height) / 1_000_000,
            "size_analysis": {},
            "recommended_sizes": [],
            "skippable_sizes": []
        }
        
        for size_name, max_size in self.sizes.items():
            target_size = self._calculate_target_size(original_size, max_size)
            needs_scaling = target_size != original_size
            
            analysis["size_analysis"][size_name] = {
                "max_size": max_size,
                "target_size": target_size,
                "needs_scaling": needs_scaling,
                "size_reduction": (original_size[0] * original_size[1]) / (target_size[0] * target_size[1]) if needs_scaling else 1.0
            }
            
            if needs_scaling:
                analysis["recommended_sizes"].append(size_name)
            else:
                analysis["skippable_sizes"].append(size_name)
        
        return analysis
    
    def get_pool_stats(self) -> Dict:
        """Get statistics about the image pool"""
        stats = {
            "total_files": 0,
            "total_size_mb": 0.0,
            "size_distribution": {},
            "directory_count": 0,
            "average_file_size_kb": 0.0
        }
        
        if not self.pool_root.exists():
            return stats
        
        total_size_bytes = 0
        
        # Count files by size
        for size_name in self.sizes:
            stats["size_distribution"][size_name] = 0
        
        # Walk through all pool files
        for pool_file in self.pool_root.rglob("*.jpg"):
            stats["total_files"] += 1
            file_size = pool_file.stat().st_size
            total_size_bytes += file_size
            
            # Extract size from filename
            if "_" in pool_file.stem:
                size_part = pool_file.stem.split("_")[-1]
                if size_part in stats["size_distribution"]:
                    stats["size_distribution"][size_part] += 1
        
        # Count directories
        stats["directory_count"] = len(list(self.pool_root.rglob("*/")))
        
        # Calculate derived stats
        stats["total_size_mb"] = total_size_bytes / (1024 * 1024)
        if stats["total_files"] > 0:
            stats["average_file_size_kb"] = (total_size_bytes / stats["total_files"]) / 1024
        
        return stats
    
    def cleanup_orphaned_files(self, valid_hashes: List[str]) -> int:
        """
        Remove pool files that don't have corresponding database entries
        
        Args:
            valid_hashes: List of image hashes that should exist
            
        Returns:
            Number of files deleted
        """
        valid_hash_set = set(valid_hashes)
        deleted_count = 0
        
        for pool_file in self.pool_root.rglob("*.jpg"):
            # Extract hash from filename: abcd1234_medium.jpg -> abcd1234
            filename_parts = pool_file.stem.split("_")
            if len(filename_parts) >= 2:
                file_hash = "_".join(filename_parts[:-1])  # Everything except last part (size)
                
                if file_hash not in valid_hash_set:
                    try:
                        pool_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted orphaned pool file: {pool_file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete orphaned file {pool_file}: {e}")
        
        # Clean up empty directories
        for directory in sorted(self.pool_root.rglob("*/"), reverse=True):
            try:
                if not any(directory.iterdir()):  # Empty directory
                    directory.rmdir()
                    logger.debug(f"Removed empty directory: {directory}")
            except Exception as e:
                logger.debug(f"Could not remove directory {directory}: {e}")
        
        logger.info(f"Cleanup complete: deleted {deleted_count} orphaned pool files")
        return deleted_count