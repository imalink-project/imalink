#!/usr/bin/env python3
"""
Configuration management for ImaLink
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

class Config:
    """Application configuration loaded from environment variables"""
    
    # Database - Read from environment or default to SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////mnt/c/temp/00imalink_data/imalink.db")
    
    # Storage paths - all configurable via environment variables
    # Default to /tmp for production Linux servers
    DATA_DIRECTORY: str = os.getenv("DATA_DIRECTORY", "/tmp/imalink_data")
    STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "/tmp/imalink_storage")
    COLDPREVIEW_ROOT: str = os.getenv("COLDPREVIEW_ROOT", "/tmp/imalink_coldpreviews")
    
    COLDPREVIEW_MAX_SIZE: int = 1200  # Max width/height in pixels
    COLDPREVIEW_QUALITY: int = 85  # JPEG quality (1-100)
    
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
    
    # Testing - Disable authentication for easier testing
    DISABLE_AUTH: bool = os.getenv("DISABLE_AUTH", "False").lower() in ("true", "1", "yes")
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        directories = [
            self.DATA_DIRECTORY,
            self.STORAGE_ROOT,
            self.COLDPREVIEW_ROOT
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

# Global config instance
config = Config()