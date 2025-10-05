#!/usr/bin/env python3
"""
Configuration management for ImaLink
"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Application configuration loaded from environment variables"""
    
    # Database
#    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///C:/temp/imalink_data/imalink.db")
#    DATABASE_URL: str = "sqlite:///C:/temp/00imalink_data/imalink.db"
    TEMP: str = "/mnt/c/temp"
    DATA_DIRECTORY: str = f"{TEMP}/00imalink_data"
    DATABASE_URL: str = f"sqlite:///{DATA_DIRECTORY}/imalink.db"
    
    # File directories
#    IMAGE_POOL_DIRECTORY: str = os.getenv("IMAGE_POOL_DIRECTORY", "C:/temp/imalink_data/imalink_pool")
    IMAGE_POOL_DIRECTORY: str = f"{DATA_DIRECTORY}/imalink_pool"
    
#    TEST_IMPORT_DIRECTORY: str = os.getenv("TEST_IMPORT_DIRECTORY", "/mnt/c/temp/00imalink_import")
    TEST_IMPORT_DIRECTORY: str = f"{TEMP}/PHOTOS_SRC_TEST_MICRO"
    TEST_STORAGE_ROOT: str = f"{TEMP}/storage"
     
    # Image processing
    POOL_QUALITY: int = int(os.getenv("POOL_QUALITY", "85"))
    
    # Optional cloud storage
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY") 
    AWS_S3_BUCKET: Optional[str] = os.getenv("AWS_S3_BUCKET")
    
    # Optional email
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # Optional external APIs
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist"""
        directories = [
            cls.IMAGE_POOL_DIRECTORY
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_pool_config(cls) -> dict:
        """Get image pool specific configuration"""
        return {
            "pool_root": cls.IMAGE_POOL_DIRECTORY,
            "quality": cls.POOL_QUALITY
        }

# Global config instance
config = Config()