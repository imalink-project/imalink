"""
Test Photo Fixtures - Self-contained photo create schemas for testing.

Provides a serializable format for test photos that can be:
- Stored as JSON/YAML files
- Loaded directly into test database
- Used across multiple test files
- Version controlled alongside tests

Each PhotoCreateSchema contains all data needed to create a complete Photo instance
with associated ImageFile, without requiring actual image files on disk.
"""
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field
import base64

if TYPE_CHECKING:
    from src.models.photo import Photo


class ImageFileEgg(BaseModel):
    """
    Minimal ImageFile data needed for testing.
    
    Contains just the filename - other fields will use sensible defaults.
    The actual file doesn't need to exist on disk for most tests.
    """
    filename: str = Field(..., description="Primary image filename (e.g. IMG_1234.jpg)")
    file_format: Optional[str] = Field(default=None, description="File format (jpeg, raw) - auto-detected if not provided")
    file_size: int = Field(default=1048576, description="File size in bytes - defaults to 1MB if not provided")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "IMG_1234.jpg",
                "file_format": "jpeg",
                "file_size": 1048576
            }
        }


class PhotoCreateSchema(BaseModel):
    """
    Self-contained photo fixture for testing.
    
    Contains all data needed to create a Photo + primary ImageFile without
    requiring actual image files on disk. Designed for easy serialization
    to JSON/YAML for test fixture files.
    
    Usage:
        # Load from JSON
        with open('tests/fixtures/photos/sunset.json') as f:
            schema = PhotoCreateSchema.model_validate_json(f.read())
        
        # Create Photo instance
        photo = Photo(
            hothash=schema.hothash,
            hotpreview=base64.b64decode(schema.hotpreview_base64),
            user_id=test_user.id,
            taken_at=schema.taken_at,
            rating=schema.rating,
            visibility=schema.visibility
        )
        
        # Create ImageFile instance
        image_file = ImageFile(
            filename=schema.primary_file.filename,
            photo=photo
        )
    """
    # Identity
    hothash: str = Field(..., description="Content-based hash identifier (64 chars)")
    
    # Visual data (required for Photo)
    hotpreview_base64: str = Field(
        ..., 
        description="Base64-encoded hotpreview image (150x150px JPEG thumbnail)"
    )
    
    # Primary ImageFile (required - every Photo has at least one ImageFile)
    primary_file: ImageFileEgg = Field(..., description="Primary image file metadata")
    
    # Image dimensions
    width: Optional[int] = Field(None, description="Original image width in pixels")
    height: Optional[int] = Field(None, description="Original image height in pixels")
    
    # Temporal metadata
    taken_at: Optional[datetime] = Field(None, description="When photo was taken")
    
    # GPS metadata
    gps_latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    
    # User metadata
    rating: int = Field(0, ge=0, le=5, description="Star rating (0-5)")
    visibility: str = Field("private", description="Visibility level (private/authenticated/public)")
    
    # Optional EXIF data
    exif_dict: Optional[Dict[str, Any]] = Field(None, description="EXIF metadata dictionary")
    
    # Test metadata (not stored in Photo - used by test helpers)
    description: Optional[str] = Field(
        None, 
        description="Human-readable description of this test photo (for documentation)"
    )
    tags: Optional[list[str]] = Field(
        default_factory=list,
        description="Suggested tags for this test photo"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "hothash": "a" * 64,
                "hotpreview_base64": "base64_encoded_150x150_jpeg_data_here...",
                "primary_file": {
                    "filename": "IMG_1234.jpg",
                    "file_format": "jpeg",
                    "file_size": 1048576
                },
                "width": 4000,
                "height": 3000,
                "taken_at": "2024-06-15T14:30:00Z",
                "gps_latitude": 59.9139,
                "gps_longitude": 10.7522,
                "rating": 4,
                "visibility": "private",
                "description": "Oslo harbor sunset - test photo with GPS",
                "tags": ["sunset", "harbor", "oslo"]
            }
        }
    
    def to_photo_kwargs(self, user_id: int) -> dict:
        """
        Convert PhotoCreateSchema to kwargs for Photo() constructor.
        
        Args:
            user_id: ID of user who will own this photo
            
        Returns:
            Dictionary of kwargs for Photo(**kwargs)
        """
        return {
            "hothash": self.hothash,
            "hotpreview": base64.b64decode(self.hotpreview_base64),
            "user_id": user_id,
            "width": self.width,
            "height": self.height,
            "taken_at": self.taken_at,
            "gps_latitude": self.gps_latitude,
            "gps_longitude": self.gps_longitude,
            "rating": self.rating,
            "visibility": self.visibility,
            "exif_dict": self.exif_dict
        }
    
    def to_image_file_kwargs(self, photo_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert PhotoCreateSchema to kwargs for ImageFile() constructor.
        
        Args:
            photo_id: Optional photo ID if already created
            
        Returns:
            Dictionary of kwargs for ImageFile(**kwargs)
        """
        kwargs: Dict[str, Any] = {
            "filename": self.primary_file.filename,
        }
        
        if photo_id is not None:
            kwargs["photo_id"] = photo_id
        
        if self.primary_file.file_size is not None:
            kwargs["file_size"] = self.primary_file.file_size
        
        return kwargs


class PhotoCreateCollection(BaseModel):
    """
    Collection of PhotoCreateSchemas for organized test fixtures.
    
    Allows grouping related test photos together with metadata about
    the collection itself. Can be serialized to a single JSON/YAML file.
    
    Example structure:
        tests/fixtures/photos/
            scenic.json          - Collection of landscape photos
            portraits.json       - Collection of portrait photos
            technical.json       - Photos for testing edge cases
            timeline.json        - Photos spanning different dates
    
    Usage:
        # Load collection
        with open('tests/fixtures/photos/scenic.json') as f:
            collection = PhotoCreateCollection.model_validate_json(f.read())
        
        # Create all photos for a user
        for name, schema in collection.photos.items():
            photo = Photo(**schema.to_photo_kwargs(test_user.id))
            db.add(photo)
    """
    name: str = Field(..., description="Collection name (e.g. 'scenic', 'portraits')")
    description: Optional[str] = Field(None, description="What this collection contains")
    version: str = Field("1.0", description="Collection version for compatibility tracking")
    
    photos: Dict[str, PhotoCreateSchema] = Field(
        ...,
        description="Named photo fixtures (key = fixture name for easy reference)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "timeline_test_photos",
                "description": "Photos spanning different years/months for timeline testing",
                "version": "1.0",
                "photos": {
                    "summer_2024": {
                        "hothash": "a" * 64,
                        "hotpreview_base64": "...",
                        "primary_file": {"filename": "summer.jpg"},
                        "taken_at": "2024-06-15T14:00:00Z",
                        "description": "Summer 2024 photo"
                    },
                    "winter_2023": {
                        "hothash": "b" * 64,
                        "hotpreview_base64": "...",
                        "primary_file": {"filename": "winter.jpg"},
                        "taken_at": "2023-12-20T10:00:00Z",
                        "description": "Winter 2023 photo"
                    }
                }
            }
        }
    
    def get(self, name: str) -> Optional[PhotoCreateSchema]:
        """Get a named photo from the collection."""
        return self.photos.get(name)
    
    def create_all(self, db_session, user_id: int) -> Dict[str, "Photo"]:
        """
        Create all photos in this collection for a specific user.
        
        Args:
            db_session: SQLAlchemy session
            user_id: User ID to own these photos
            
        Returns:
            Dictionary mapping fixture names to created Photo instances
        """
        from src.models.photo import Photo
        from src.models.image_file import ImageFile
        
        created = {}
        
        for name, schema in self.photos.items():
            # Create Photo
            photo = Photo(**egg.to_photo_kwargs(user_id))
            db_session.add(photo)
            db_session.flush()  # Get photo.id
            
            # Create primary ImageFile  
            # Type ignore needed because photo.id is Column[int] but becomes int after flush
            image_file = ImageFile(**egg.to_image_file_kwargs(int(photo.id)))  # type: ignore
            db_session.add(image_file)
            
            created[name] = photo
        
        db_session.commit()
        return created


# Convenience function for creating minimal test photos
def create_test_photo_create_schema(
    hothash: str,
    filename: str = "test.jpg",
    taken_at: Optional[datetime] = None,
    rating: int = 0,
    visibility: str = "private",
    **kwargs
) -> PhotoCreateSchema:
    """
    Create a minimal PhotoCreateSchema for testing with fake hotpreview data.
    
    Generates a tiny 1x1 pixel JPEG as hotpreview (base64 encoded).
    Useful for quick test photo creation without needing real image data.
    
    Args:
        hothash: Content hash (must be unique)
        filename: Primary image filename
        taken_at: When photo was taken
        rating: Star rating (0-5)
        visibility: Visibility level
        **kwargs: Additional PhotoCreateSchema fields
    
    Returns:
        PhotoCreateSchema instance with minimal valid data
    """
    # Minimal 1x1 red pixel JPEG (base64 encoded)
    # This is a valid JPEG that can be decoded but takes minimal space
    MINIMAL_JPEG_BASE64 = (
        "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
        "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
        "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
        "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
        "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAB//2Q=="
    )
    
    return PhotoCreateSchema(
        hothash=hothash,
        hotpreview_base64=MINIMAL_JPEG_BASE64,
        primary_file=ImageFileEgg(filename=filename),
        taken_at=taken_at,
        rating=rating,
        visibility=visibility,
        **kwargs
    )
