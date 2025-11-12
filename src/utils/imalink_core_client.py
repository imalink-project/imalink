"""
Client for calling imalink-core image processing service

imalink-core is a separate FastAPI server that processes images into PhotoEgg format.
This client handles communication between backend and core service.
"""
import httpx
from typing import Optional

from src.core.config import Config
from src.schemas.photoegg_schemas import PhotoEggCreate


class ImalinkCoreClient:
    """Client for imalink-core service"""
    
    def __init__(self, core_url: Optional[str] = None):
        """
        Initialize client with imalink-core URL
        
        Args:
            core_url: imalink-core service URL (default from config)
        """
        self.core_url = core_url or Config.IMALINK_CORE_URL
    
    async def process_image(
        self, 
        image_bytes: bytes, 
        filename: str,
        coldpreview_size: Optional[int] = None
    ) -> PhotoEggCreate:
        """
        Send image to imalink-core for processing
        
        imalink-core processes the image and returns PhotoEgg JSON with:
        - hothash (SHA256 of hotpreview)
        - hotpreview_base64 (150x150px thumbnail)
        - coldpreview_base64 (optional larger preview)
        - Complete EXIF metadata
        
        Args:
            image_bytes: Raw image file bytes
            filename: Original filename (for metadata)
            coldpreview_size: Optional size for coldpreview (e.g., 2560)
            
        Returns:
            PhotoEggCreate: Validated PhotoEgg data
            
        Raises:
            httpx.HTTPStatusError: If imalink-core returns error
            ValueError: If PhotoEgg validation fails
        """
        # Prepare multipart form-data
        files = {"file": (filename, image_bytes, "image/jpeg")}
        data = {}
        
        if coldpreview_size is not None:
            data["coldpreview_size"] = str(coldpreview_size)
        
        # Call imalink-core /v1/process endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.core_url}/v1/process",
                files=files,
                data=data,
                timeout=30.0  # Image processing can take time
            )
            
            # Raise on HTTP errors (400, 500, etc.)
            response.raise_for_status()
            
            # Parse and validate PhotoEgg JSON
            photoegg_dict = response.json()
            
            # Validate using Pydantic schema
            return PhotoEggCreate(**photoegg_dict)
