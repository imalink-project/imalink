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
    
    # Storage for imported files
    TEMP: str = os.getenv("TEMP", "/mnt/c/temp")
    
    @property
    def _temp(self) -> str:
        return os.getenv("TEMP", "/mnt/c/temp")
    
    @property  
    def DATA_DIRECTORY(self) -> str:
        return os.getenv("DATA_DIRECTORY", f"{self._temp}/00imalink_data")
    
    @property
    def STORAGE_ROOT(self) -> str:
        return os.getenv("STORAGE_ROOT", f"{self._temp}/imalink-storage")
    
    # Coldpreview storage (filesystem) - read from environment or default
    @property
    def COLDPREVIEW_ROOT(self) -> str:
        return os.getenv("COLDPREVIEW_ROOT", f"{self.DATA_DIRECTORY}/coldpreviews")
    
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
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist"""
        directories = [
            cls.DATA_DIRECTORY,
            cls.STORAGE_ROOT,
            cls.COLDPREVIEW_ROOT
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

# Global config instance
config = Config()