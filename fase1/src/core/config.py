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
    
    # Storage for imported files
    STORAGE_ROOT: str = f"{TEMP}/imalink-storage"
    
    # Note: IMAGE_POOL and frontend-related paths removed - handled by frontend
    # Image processing quality settings handled by services as needed
     
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
            cls.DATA_DIRECTORY,
            cls.STORAGE_ROOT
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_pool_config(cls) -> dict:
        """Get image pool specific configuration"""
        return {
            "quality": 85  # Default quality - can be made configurable per service if needed
        }

# Global config instance
config = Config()