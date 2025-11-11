# Pillow Removal Plan - Move Validation to imalink-core

> **STATUS: COMPLETED ✅**  
> Date: 2024  
> All changes described in this document have been implemented:
> - ✅ Pillow removed from production (moved to dev dependencies)
> - ✅ Image validation moved to imalink-core server
> - ✅ PhotoEgg v2.0 includes: `is_valid_image`, `image_format`, `file_size_bytes`
> - ✅ Perceptual hash removed completely (dead code - Photo model never had this field)
> - ✅ imagehash dependency removed
> - ✅ coldpreview_repository.py deleted (~300 lines)
> 
> This document remains as historical reference for the migration process.

---

## Current State

### Backend uses Pillow for:
1. **Image validation** (coldpreview upload) - 6 lines
2. **Perceptual hash** (duplicate detection) - 4 lines  
3. **Coldpreview generation** (deprecated) - 300 lines
4. **Test fixtures** (dummy images) - 3 files

---

## Proposed imalink-core Enhancement

### New PhotoEgg Fields

Add to PhotoEgg JSON response:

```python
# In imalink-core PhotoEgg class
class PhotoEgg:
    # Existing fields
    hothash: str
    hotpreview_base64: str
    coldpreview_base64: Optional[str]
    width: int
    height: int
    metadata: BasicMetadata
    
    # NEW FIELDS for validation
    is_valid_image: bool = True  # Always True if PhotoEgg created successfully
    image_format: str  # "JPEG", "PNG", "HEIC", etc.
    perceptual_hash: Optional[str] = None  # For advanced duplicate detection
    file_size_bytes: int  # Original file size
```

### imalink-core API Enhancement

```python
# In imalink-core server endpoint
@router.post("/api/v1/process")
async def process_image(
    file: UploadFile,
    generate_coldpreview: bool = True,
    calculate_perceptual_hash: bool = False  # NEW: Optional feature
) -> PhotoEgg:
    """
    Process image and return PhotoEgg
    
    NEW BEHAVIOR:
    - Always validates image format (JPEG, PNG, HEIC, etc.)
    - Returns PhotoEgg only if valid
    - Optionally calculates perceptual hash for duplicate detection
    - Returns error if image invalid/corrupted
    """
    try:
        # Read file
        image_bytes = await file.read()
        
        # Validate image (already done internally)
        img = Image.open(io.BytesIO(image_bytes))
        image_format = img.format  # "JPEG", "PNG", etc.
        
        # Generate previews (existing code)
        hotpreview = generate_hotpreview(img)
        coldpreview = generate_coldpreview(img) if generate_coldpreview else None
        
        # NEW: Optional perceptual hash
        perceptual_hash = None
        if calculate_perceptual_hash:
            perceptual_hash = str(imagehash.phash(img))
        
        # Extract metadata (existing code)
        metadata = extract_metadata(img)
        
        return PhotoEgg(
            hothash=calculate_hash(hotpreview),
            hotpreview_base64=base64.b64encode(hotpreview).decode(),
            coldpreview_base64=base64.b64encode(coldpreview).decode() if coldpreview else None,
            width=img.width,
            height=img.height,
            metadata=metadata,
            # NEW FIELDS
            is_valid_image=True,  # Implicit - if we got here, it's valid
            image_format=image_format,
            perceptual_hash=perceptual_hash,
            file_size_bytes=len(image_bytes)
        )
        
    except Exception as e:
        # Image invalid or corrupted
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file: {str(e)}"
        )
```

---

## Backend Changes

### 1. Update PhotoEgg Schema

```python
# src/schemas/photoegg_schemas.py

class PhotoEggMetadata(BaseModel):
    """Metadata section of PhotoEgg from imalink-core"""
    # Existing fields...
    taken_at: Optional[datetime] = None
    camera_make: Optional[str] = None
    # ... etc
    

class PhotoEggCreate(BaseModel):
    """
    PhotoEgg from imalink-core server
    
    Complete JSON package with all image processing results.
    """
    hothash: str
    hotpreview_base64: str
    coldpreview_base64: Optional[str] = None
    width: int
    height: int
    metadata: PhotoEggMetadata
    
    # NEW FIELDS (imalink-core v2.0+)
    is_valid_image: bool = True
    image_format: str  # "JPEG", "PNG", "HEIC"
    perceptual_hash: Optional[str] = None
    file_size_bytes: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "hothash": "a3f2c1d4e5b6...",
                "hotpreview_base64": "/9j/4AAQSkZJRg...",
                "coldpreview_base64": "/9j/4AAQSkZJRg...",
                "width": 4000,
                "height": 3000,
                "metadata": {
                    "taken_at": "2024-01-15T14:30:00",
                    "camera_make": "Canon"
                },
                "is_valid_image": True,
                "image_format": "JPEG",
                "perceptual_hash": "abc123def456",
                "file_size_bytes": 2485760
            }
        }
```

### 2. Remove Image Validation (photos.py)

```python
# src/api/v1/photos.py

# BEFORE (with Pillow validation):
@router.post("/{hothash}/coldpreview")
async def upload_coldpreview(
    hothash: str,
    file: UploadFile = File(...),
    photo_service: PhotoService = Depends(get_photo_service),
    current_user: User = Depends(get_current_active_user)
):
    """Upload or update coldpreview for photo"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_content = await file.read()
    
    if not file_content:
        raise HTTPException(status_code=400, detail="File is empty")
    
    # OLD: Pillow validation (REMOVE THIS)
    from PIL import Image as PILImage
    import io
    try:
        test_img = PILImage.open(io.BytesIO(file_content))
        test_img.verify()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    
    result = photo_service.upload_coldpreview(hothash, file_content, current_user.id)
    return create_success_response(message="Coldpreview uploaded successfully", data=result)


# AFTER (trust imalink-core validation):
@router.post("/{hothash}/coldpreview")
async def upload_coldpreview(
    hothash: str,
    file: UploadFile = File(...),
    photo_service: PhotoService = Depends(get_photo_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload or update coldpreview for photo
    
    DEPRECATED: PhotoEgg from imalink-core already provides coldpreview.
    This endpoint exists for legacy support only.
    
    Recommendation: Use POST /photoegg instead.
    """
    # Basic validation only
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_content = await file.read()
    
    if not file_content:
        raise HTTPException(status_code=400, detail="File is empty")
    
    # NO Pillow validation - trust client or imalink-core
    # If file is corrupted, database will handle it gracefully
    
    result = photo_service.upload_coldpreview(hothash, file_content, current_user.id)
    return create_success_response(message="Coldpreview uploaded successfully", data=result)
```

### 3. Remove Perceptual Hash Generation (image_file_service.py)

```python
# src/services/image_file_service.py

# BEFORE (with Pillow):
def _generate_perceptual_hash_if_needed(
    self, 
    provided_hash: Optional[str], 
    hotpreview_bytes: bytes
) -> Optional[str]:
    """Generate perceptual hash from hotpreview if not provided"""
    if provided_hash:
        return provided_hash
    
    try:
        from PIL import Image as PILImage
        import io
        img = PILImage.open(io.BytesIO(hotpreview_bytes))
        phash = imagehash.phash(img)
        return str(phash)
    except Exception:
        return None


# AFTER (from PhotoEgg):
def _generate_perceptual_hash_if_needed(
    self, 
    provided_hash: Optional[str], 
    hotpreview_bytes: bytes  # Not used anymore
) -> Optional[str]:
    """
    Get perceptual hash (now provided in PhotoEgg)
    
    DEPRECATED: Perceptual hash should come from PhotoEgg.
    This method kept for backwards compatibility with old endpoints.
    """
    # Simply return provided hash or None
    # PhotoEgg should provide this during photo creation
    return provided_hash
```

### 4. Update Photo Service (photo_service.py)

```python
# src/services/photo_service.py

def create_photo_from_photoegg(
    self, 
    photoegg_request: PhotoEggRequest, 
    user_id: int
) -> Photo:
    """
    Create Photo from PhotoEgg JSON
    
    PhotoEgg comes from imalink-core server and contains all image processing results.
    """
    # Decode base64 previews to bytes
    hotpreview_bytes = base64.b64decode(photoegg_request.hotpreview_base64)
    coldpreview_bytes = None
    if photoegg_request.coldpreview_base64:
        coldpreview_bytes = base64.b64decode(photoegg_request.coldpreview_base64)
    
    # Create Photo directly
    photo = Photo(
        user_id=user_id,
        hothash=photoegg_request.hothash,
        hotpreview=hotpreview_bytes,
        coldpreview=coldpreview_bytes,
        width=photoegg_request.width,
        height=photoegg_request.height,
        
        # User metadata
        title=photoegg_request.title,
        description=photoegg_request.description,
        rating=photoegg_request.rating or 0,
        visibility=photoegg_request.visibility or "private",
        
        # Map PhotoEgg metadata to Photo fields
        taken_at=photoegg_request.metadata.taken_at,
        camera_make=photoegg_request.metadata.camera_make,
        camera_model=photoegg_request.metadata.camera_model,
        lens_model=photoegg_request.metadata.lens_model,
        focal_length=photoegg_request.metadata.focal_length,
        f_number=photoegg_request.metadata.f_number,
        iso=photoegg_request.metadata.iso,
        exposure_time=photoegg_request.metadata.exposure_time,
        gps_latitude=photoegg_request.metadata.gps_latitude,
        gps_longitude=photoegg_request.metadata.gps_longitude,
        gps_altitude=photoegg_request.metadata.gps_altitude,
        
        # NEW: Store perceptual hash if provided
        # perceptual_hash=photoegg_request.perceptual_hash,  # If Photo model has this field
    )
    
    self.db.add(photo)
    self.db.commit()
    self.db.refresh(photo)
    
    # TODO: Handle tag association
    
    return photo
```

### 5. Delete Deprecated File

```bash
# Remove coldpreview_repository.py entirely
rm src/utils/coldpreview_repository.py
```

### 6. Remove Pillow from pyproject.toml

```toml
# pyproject.toml

[project]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.23",
    "pydantic>=2.5.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "slowapi>=0.1.9",
    # "pillow>=11.3.0",  # REMOVED - not needed anymore
    "imagehash>=4.3.1",  # KEEP - for perceptual hash if not from PhotoEgg
    "alembic>=1.13.0",
]
```

### 7. Update Test Fixtures

Replace Pillow-generated images with base64 constants:

```python
# tests/conftest.py or tests/fixtures/test_images.py

# BEFORE (with Pillow):
from PIL import Image
def create_test_image():
    img = Image.new('RGB', (150, 150), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


# AFTER (with base64 constants):
import base64

# Pre-generated 150x150 red JPEG (2KB)
TEST_HOTPREVIEW_BASE64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCABkAGQDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlbaWmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD+..."

TEST_COLDPREVIEW_BASE64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAGQAZADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL..."

def get_test_hotpreview_bytes() -> bytes:
    """Get decoded test hotpreview (150x150 red JPEG)"""
    return base64.b64decode(TEST_HOTPREVIEW_BASE64)

def get_test_coldpreview_bytes() -> bytes:
    """Get decoded test coldpreview (larger preview)"""
    return base64.b64decode(TEST_COLDPREVIEW_BASE64)
```

---

## Migration Checklist

### imalink-core Updates (v2.0)
- [ ] Add `is_valid_image` field to PhotoEgg (always True)
- [ ] Add `image_format` field to PhotoEgg (JPEG, PNG, etc.)
- [ ] Add `perceptual_hash` optional field to PhotoEgg
- [ ] Add `file_size_bytes` field to PhotoEgg
- [ ] Add query parameter `calculate_perceptual_hash: bool = False`
- [ ] Update API documentation
- [ ] Increment version to 2.0.0 (breaking change)

### Backend Updates
- [ ] Update `PhotoEggCreate` schema with new fields
- [ ] Remove Pillow validation from `upload_coldpreview()` endpoint
- [ ] Simplify `_generate_perceptual_hash_if_needed()` (just return provided hash)
- [ ] Remove `from PIL import ...` from `src/api/v1/photos.py`
- [ ] Remove `from PIL import ...` from `src/services/image_file_service.py`
- [ ] Delete `src/utils/coldpreview_repository.py` entirely
- [ ] Remove `pillow>=11.3.0` from `pyproject.toml`
- [ ] Update test fixtures with base64 constants
- [ ] Run full test suite
- [ ] Update CONTRACTS.md with new PhotoEgg fields

### Testing
- [ ] Test PhotoEgg creation with new fields
- [ ] Test backwards compatibility (old PhotoEgg without new fields)
- [ ] Test coldpreview upload without Pillow validation
- [ ] Verify Docker image size reduction (~50MB smaller)
- [ ] Performance test (should be same or faster)

---

## Backwards Compatibility

### PhotoEgg v1.x (without new fields)
Backend should tolerate missing fields:

```python
class PhotoEggCreate(BaseModel):
    # Required fields (v1.x)
    hothash: str
    hotpreview_base64: str
    width: int
    height: int
    
    # Optional fields (v1.x)
    coldpreview_base64: Optional[str] = None
    metadata: PhotoEggMetadata
    
    # NEW fields (v2.0+) - with defaults for backwards compat
    is_valid_image: bool = True  # Default: assume valid
    image_format: str = "JPEG"  # Default: JPEG
    perceptual_hash: Optional[str] = None  # Default: None
    file_size_bytes: int = 0  # Default: 0 (unknown)
```

This allows:
- ✅ Old imalink-core (v1.x) → Backend works (defaults used)
- ✅ New imalink-core (v2.0+) → Backend gets enhanced data

---

## Benefits Summary

### Before (with Pillow):
- **Dependencies**: Pillow + imagehash
- **Docker image**: ~200MB
- **Validation**: Duplicated (imalink-core + backend)
- **Performance**: +1-5ms per upload (validation)
- **Code**: 310 lines Pillow-related code

### After (without Pillow):
- **Dependencies**: imagehash only (optional)
- **Docker image**: ~150MB (-50MB)
- **Validation**: Single source of truth (imalink-core)
- **Performance**: Same or faster
- **Code**: ~10 lines Pillow-related (tests only)

---

## Alternative: Keep Pillow in Dev Dependencies Only

If you want to keep test fixture generation simple:

```toml
[project]
dependencies = [
    # ... no pillow
]

[project.optional-dependencies]
dev = [
    "pillow>=11.3.0",  # For test fixtures only
    "pytest>=7.4.0",
]
```

Then generate fixtures once and commit as base64 constants.
