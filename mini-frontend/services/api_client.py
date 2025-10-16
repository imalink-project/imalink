"""
API Client for ImaLink Backend
Handles all HTTP communication with FastAPI backend
"""
import httpx
from typing import Optional, Dict, Any, List
import base64


class APIClient:
    """HTTP client for ImaLink API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request"""
        response = self.client.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request"""
        response = self.client.post(f"{self.base_url}{endpoint}", json=json_data)
        response.raise_for_status()
        return response.json()
    
    def _delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        response = self.client.delete(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()
    
    # ===== Photos API =====
    
    def get_photos(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get paginated list of photos"""
        return self._get("/photos/", params={"offset": offset, "limit": limit})
    
    def get_photo(self, hothash: str) -> Dict[str, Any]:
        """Get photo by hothash"""
        return self._get(f"/photos/{hothash}")
    
    def get_photo_hotpreview(self, hothash: str) -> bytes:
        """Get hotpreview image data"""
        response = self.client.get(f"{self.base_url}/photos/{hothash}/hotpreview")
        response.raise_for_status()
        return response.content
    
    def delete_photo(self, hothash: str) -> Dict[str, Any]:
        """Delete photo and all associated image files"""
        return self._delete(f"/photos/{hothash}")
    
    # ===== Image Files API =====
    
    def create_image_file(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new image file with automatic photo creation
        
        Args:
            image_data: Dictionary with:
                - filename: str
                - file_size: int
                - file_path: str
                - hotpreview: str (base64-encoded JPEG)
                - exif_data: dict (optional)
                - import_session_id: int (optional)
        """
        return self._post("/image-files/", json_data=image_data)
    
    def get_image_files(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get paginated list of image files"""
        return self._get("/image-files/", params={"offset": offset, "limit": limit})
    
    def get_image_file(self, image_id: int) -> Dict[str, Any]:
        """Get image file by ID"""
        return self._get(f"/image-files/{image_id}")
    
    def get_image_hotpreview(self, image_id: int) -> bytes:
        """Get hotpreview from image file"""
        response = self.client.get(f"{self.base_url}/image-files/{image_id}/hotpreview")
        response.raise_for_status()
        return response.content
    
    # ===== Authors API =====
    
    def get_authors(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get paginated list of authors"""
        return self._get("/authors/", params={"offset": offset, "limit": limit})
    
    def create_author(self, name: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Create new author"""
        data = {"name": name}
        if email:
            data["email"] = email
        return self._post("/authors/", json_data=data)
    
    # ===== Import Sessions API =====
    
    def create_import_session(self, source_path: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create new import session"""
        data = {"source_path": source_path}
        if description:
            data["description"] = description
        return self._post("/import-sessions/", json_data=data)
    
    def get_import_sessions(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get paginated list of import sessions"""
        return self._get("/import-sessions/", params={"offset": offset, "limit": limit})
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
