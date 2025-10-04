"""
Import Once request schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class ImportOnceRequest(BaseModel):
    """Request for import once operation"""
    import_session_id: int = Field(..., description="ID of completed import session")
    storage_path: str = Field(..., description="Base path for permanent storage")
    storage_subfolder: Optional[str] = Field(None, description="Subfolder in storage (auto-generated if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "import_session_id": 1,
                "storage_path": "C:/ImaLink/Storage",
                "storage_subfolder": "2025-10-04_wedding"
            }
        }