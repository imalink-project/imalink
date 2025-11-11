# Module Contracts - imalink Backend

## External Dependencies

### imalink-core FastAPI Server

**Repository**: https://github.com/kjelkols/imalink-core  
**Type**: Separate FastAPI server (NOT a pip library)  
**Deployment**: Runs on localhost (same machine as backend)  
**Default Port**: 8001 (configurable)  
**Communication**: HTTP REST API

**What it does**:
- Receives images from frontend
- Processes images (EXIF extraction, preview generation, hashing)
- Returns PhotoEgg JSON (complete metadata package)
- Stateless - no storage, no database

**Backend does NOT import imalink-core** - it's a separate service!

---

## imalink-core HTTP API

### 1. POST /api/v1/process

**Purpose**: Process image file and return PhotoEgg JSON

**Request**:
```http
POST http://localhost:8001/api/v1/process
Content-Type: multipart/form-data

file: <image_binary>
generate_coldpreview: true|false (optional, default: true)
```

**Response**: PhotoEgg JSON
```json
{
  "hothash": "a3f2c1d4e5b6...",
  "hotpreview_base64": "/9j/4AAQSkZJRg...",
  "coldpreview_base64": "/9j/4AAQSkZJRg..." | null,
  "width": 4000,
  "height": 3000,
  "metadata": {
    "taken_at": "2024-01-15T14:30:00",
    "camera_make": "Canon",
    "camera_model": "EOS R5",
    "lens_model": "RF 24-70mm F2.8 L IS USM",
    "focal_length": 50.0,
    "f_number": 2.8,
    "iso": 400,
    "exposure_time": "1/250",
    "gps_latitude": 59.9139,
    "gps_longitude": 10.7522,
    "gps_altitude": 12.5
  },
  "exif_dict": { ... },
  
  // NEW: Validation & Extended Info (v2.0+)
  "is_valid_image": true,
  "image_format": "JPEG",
  "file_size_bytes": 2485760
}
```

**PhotoEgg Fields**:
- `hothash`: SHA256 hash of hotpreview (64 hex chars)
- `hotpreview_base64`: Base64-encoded JPEG thumbnail (~5-15KB, 150x150px)
- `coldpreview_base64`: Base64-encoded JPEG preview (~50-200KB) - OPTIONAL
- `width`: Original image width in pixels
- `height`: Original image height in pixels
- `metadata`: Core EXIF metadata (BasicMetadata structure)
- `exif_dict`: Complete raw EXIF data (for advanced users)
- `is_valid_image`: Validation status (always true if PhotoEgg created) - v2.0+
- `image_format`: Image format (JPEG, PNG, HEIC, etc.) - v2.0+
- `file_size_bytes`: Original file size in bytes - v2.0+

**Error Response**:
```json
{
  "detail": "Unsupported image format",
  "status_code": 400
}
```

---

## Backend API Consuming PhotoEgg

### POST /api/v1/photos/photoegg

**Purpose**: Create Photo from PhotoEgg JSON (received from frontend)

**Request**:
```json
{
  "hothash": "a3f2c1d4e5b6...",
  "hotpreview_base64": "/9j/4AAQSkZJRg...",
  "coldpreview_base64": "/9j/4AAQSkZJRg..." | null,
  "width": 4000,
  "height": 3000,
  "metadata": {
    "taken_at": "2024-01-15T14:30:00",
    "camera_make": "Canon",
    ...
  },
  
  // User-provided metadata
  "title": "Sunset at the beach",
  "description": "Beautiful golden hour",
  "rating": 4,
  "visibility": "private",
  "tags": ["vacation", "beach", "sunset"]
}
```

**Response**:
```json
{
  "id": 123,
  "is_duplicate": false
}
```

**Implementation**:
```python
# In photo_service.py
def create_photo_from_photoegg(
    self, 
    photoegg_request: PhotoEggRequest, 
    user_id: int
) -> Photo:
    # Decode base64 to bytes for database storage
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
    )
    
    self.db.add(photo)
    self.db.commit()
    self.db.refresh(photo)
    
    return photo
```

---

## Data Flow Architecture

```
┌──────────┐                    ┌─────────────────┐                    ┌──────────┐
│          │  1. Upload Image   │                 │  2. PhotoEgg JSON  │          │
│ Frontend ├───────────────────►│  imalink-core   ├───────────────────►│ Frontend │
│          │                    │  FastAPI Server │                    │          │
└──────────┘                    └─────────────────┘                    └─────┬────┘
     ▲                                                                        │
     │                                                                        │ 3. Send PhotoEgg
     │                                                                        │    + user metadata
     │                                                                        ▼
     │                          ┌─────────────────┐                    ┌──────────┐
     │  5. Photo Response       │                 │  4. Store in DB    │          │
     └──────────────────────────┤  imalink        │◄───────────────────┤ Backend  │
                                │  Backend        │                    │  API     │
                                └─────────────────┘                    └──────────┘
```

**Step-by-Step**:
1. Frontend sends image file to imalink-core server (localhost:8001)
2. imalink-core processes image → returns PhotoEgg JSON
3. Frontend sends PhotoEgg + user metadata to Backend (localhost:8000)
4. Backend stores metadata + previews in database
5. Backend returns Photo ID + duplicate flag

---

## Backend Internal Services (NO imalink-core imports)

### 1. HothashCalculator (Replaced)

**OLD CODE** ❌:
```python
from imalink_core import HothashCalculator

calculator = HothashCalculator()
hothash = calculator.calculate_from_bytes(hotpreview_bytes)
```

**NEW CODE** ✅:
```python
import hashlib

hothash = hashlib.sha256(hotpreview_bytes).hexdigest()
```

### 2. ExifExtractor (Removed)

**Backend NO LONGER extracts EXIF** - all metadata comes from PhotoEgg

**OLD CODE** ❌:
```python
from imalink_core import ExifExtractor

metadata = ExifExtractor.extract_basic(image_path)
```

**NEW CODE** ✅:
```python
# EXIF comes from PhotoEgg metadata field
taken_at = photoegg_request.metadata.taken_at
camera_make = photoegg_request.metadata.camera_make
# ... etc
```

### 3. PreviewGenerator (Deprecated)

**Backend NO LONGER generates previews** - all previews come from PhotoEgg

**OLD CODE** ❌:
```python
from imalink_core import PreviewGenerator

generator = PreviewGenerator()
coldpreview = generator.generate(image_path, max_size=1920)
```

**NEW CODE** ✅:
```python
# Coldpreview comes pre-generated in PhotoEgg
if photoegg_request.coldpreview_base64:
    coldpreview_bytes = base64.b64decode(photoegg_request.coldpreview_base64)
```

**src/utils/coldpreview_repository.py**: Marked as DEPRECATED (legacy support only)

---

## Testing Strategy

### Unit Tests (Backend)
- Mock imalink-core HTTP responses
- Test PhotoEgg → Photo conversion
- Test duplicate detection via hothash
- Test base64 decoding errors
- Test incomplete PhotoEgg data

### Integration Tests
- Require imalink-core server running on localhost:8001
- Test full workflow: Image upload → PhotoEgg → Photo creation
- Test error handling when imalink-core unavailable
- Test coldpreview presence/absence

### Contract Tests
**NO LONGER library contract tests** - HTTP API contract tests instead:

```python
# Test imalink-core HTTP API contract
def test_imalink_core_process_endpoint():
    """Verify PhotoEgg structure from imalink-core server"""
    response = requests.post(
        "http://localhost:8001/api/v1/process",
        files={"file": open("test_image.jpg", "rb")}
    )
    
    assert response.status_code == 200
    photoegg = response.json()
    
    # Verify required fields
    assert "hothash" in photoegg
    assert "hotpreview_base64" in photoegg
    assert "width" in photoegg
    assert "height" in photoegg
    assert "metadata" in photoegg
```

---

## Breaking Change Protocol

### imalink-core Server API Changes

**When PhotoEgg structure changes**:
1. imalink-core team updates PhotoEgg schema
2. imalink-core increments version (semver)
3. Backend team updates `PhotoEggMetadata` schema in `src/schemas/photoegg_schemas.py`
4. Update mapping code in `create_photo_from_photoegg()`
5. Run full test suite
6. Deploy backend after imalink-core server updated

**Backwards compatibility strategy**:
- PhotoEgg additions: Backend ignores unknown fields (forward-compatible)
- PhotoEgg removals: Backend must update (breaking change)
- PhotoEgg renames: Breaking change - requires migration

**Version compatibility matrix**:
```
Backend v1.x → imalink-core server v1.x ✅
Backend v1.x → imalink-core server v2.x ❌ (requires backend update)
```

---

## Migration from Library to Server (COMPLETED)

### What Changed ✅

**REMOVED**:
- ❌ `pyproject.toml`: Removed `imalink-core` from dependencies
- ❌ All `from imalink_core import` statements (5 files)
- ❌ `tests/contracts/` directory (library contract tests)

**REPLACED**:
- ✅ `HothashCalculator` → `hashlib.sha256()`
- ✅ `ExifExtractor` → PhotoEgg metadata field
- ✅ `PreviewGenerator` → PhotoEgg base64 previews

**ADDED**:
- ✅ `src/schemas/photoegg_schemas.py` (PhotoEgg request/response schemas)
- ✅ `POST /api/v1/photos/photoegg` endpoint
- ✅ `PhotoService.create_photo_from_photoegg()` method
- ✅ `PhotoService.get_photo_by_hothash()` method

### Migration Checklist

Backend migration completed:
- [x] Remove imalink-core from pyproject.toml
- [x] Remove all imalink-core imports
- [x] Implement PhotoEgg schemas
- [x] Implement POST /photoegg endpoint
- [x] Replace HothashCalculator with hashlib
- [x] Update documentation (.github/copilot-instructions.md)
- [x] Update CONTRACTS.md (this file)
- [ ] Add deprecation notices to old endpoints
- [ ] Implement tag association in create_photo_from_photoegg
- [ ] Create HTTP API tests for imalink-core server

Frontend migration required:
- [ ] Update image upload to send to imalink-core server first
- [ ] Receive PhotoEgg JSON from imalink-core
- [ ] Send PhotoEgg to backend POST /photoegg endpoint
- [ ] Handle duplicate detection (is_duplicate flag)

imalink-core server setup:
- [ ] Deploy imalink-core as FastAPI server
- [ ] Configure port (default: 8001)
- [ ] Document POST /api/v1/process endpoint
- [ ] Add health check endpoint
- [ ] Add CORS configuration for frontend

---

## Future Enhancements

### Planned Features
- **Tag association**: Complete TODO in `create_photo_from_photoegg()`
- **Batch upload**: Process multiple images via imalink-core server
- **Async processing**: Background jobs for large imports
- **Coldpreview caching**: S3/object storage for large previews
- **PhotoEgg validation**: Stricter schema validation with error details

### API Stability
- **Stable**: PhotoEgg structure (hothash, hotpreview_base64, metadata)
- **Evolving**: User metadata fields (title, description, tags)
- **Experimental**: coldpreview_base64 (may become optional or removed)

---

## Questions & Support

**Before making changes**:
1. Check imalink-core server version compatibility
2. Verify PhotoEgg structure hasn't changed
3. Test with imalink-core server running locally
4. Coordinate with frontend team on PhotoEgg workflow
5. Update both copilot-instructions.md and CONTRACTS.md

**When in doubt**:
- PhotoEgg = Complete package from imalink-core server
- Backend = Metadata storage + user organization only
- No image processing in backend - all from imalink-core server
- Previews stored as bytes (decoded from base64)
- Duplicate detection via hothash (SHA256 of hotpreview)


---

### 3. HothashCalculator

**Import**:
```python
from imalink_core import HothashCalculator
```

**Methods**:
```python
# Calculate SHA256 hash from image bytes
hothash = HothashCalculator.calculate(image_bytes: bytes) -> str

# Verify hash matches expected value
is_valid = HothashCalculator.verify(image_bytes: bytes, expected_hash: str) -> bool
```

**Usage in Backend**:
```python
# Duplicate detection
existing = photo_repo.find_by_hothash(db, hothash)
if existing:
    raise DuplicatePhotoError(f"Photo already exists: {existing.id}")
```

---

### 4. PreviewGenerator

**Import**:
```python
from imalink_core import PreviewGenerator
```

**Methods**:
```python
# Generate hotpreview (150x150px)
hotpreview = PreviewGenerator.generate_hotpreview(
    image_path: Path,
    size: Tuple[int, int] = (150, 150),
    quality: int = 85
) -> HotPreview

# Generate coldpreview (1920x1080px)
coldpreview = PreviewGenerator.generate_coldpreview(
    image_path: Path,
    max_size: int = 1920,
    quality: int = 90
) -> ColdPreview

# Generate both in one pass (optimization)
hotpreview, coldpreview = PreviewGenerator.generate_both(
    image_path: Path
) -> Tuple[HotPreview, ColdPreview]
```

**HotPreview Structure**:
- `bytes: bytes` - Raw JPEG bytes
- `base64: str` - Base64-encoded string
- `hothash: str` - SHA256 hash (unique ID)
- `width: int` - Actual width after resize
- `height: int` - Actual height after resize

**ColdPreview Structure**:
- `bytes: bytes` - Raw JPEG bytes
- `base64: str` - Base64-encoded string
- `width: int` - Actual width after resize
- `height: int` - Actual height after resize

**Usage in Backend**:
Used internally by `process_image()`, called directly for on-demand coldpreview generation.

---

## Data Model Contracts

### CorePhoto (from imalink-core)

**Purpose**: Complete data extractable from image file  
**Source**: imalink-core processing  
**NOT persisted**: Backend creates its own Photo model

**Structure (via `result.photo.to_dict()`)**:
```python
{
    # Identity
    "hothash": str,  # SHA256 hash (64 chars)
    
    # Hotpreview (150x150px, ~5-15KB)
    "hotpreview_base64": str,
    "hotpreview_width": int,
    "hotpreview_height": int,
    
    # Coldpreview (1920x1080px, ~100-200KB) - OPTIONAL
    "coldpreview_base64": Optional[str],
    "coldpreview_width": Optional[int],
    "coldpreview_height": Optional[int],
    
    # File info
    "primary_filename": str,
    "width": int,
    "height": int,
    
    # Timestamps
    "taken_at": Optional[str],  # ISO 8601
    "first_imported": None,  # Backend sets
    "last_imported": None,   # Backend sets
    
    # Camera metadata
    "camera_make": Optional[str],
    "camera_model": Optional[str],
    
    # GPS
    "gps_latitude": Optional[float],
    "gps_longitude": Optional[float],
    "has_gps": bool,
    
    # Camera settings
    "iso": Optional[int],
    "aperture": Optional[float],
    "shutter_speed": Optional[str],
    "focal_length": Optional[float],
    "lens_model": Optional[str],
    "lens_make": Optional[str],
    
    # NOT included (backend-specific)
    "rating": None,
    "visibility": None,
    "title": None,
    "description": None,
    "tags": None,
    "user_id": None
}
```

**Backend Mapping**:
```python
# Map CorePhoto to Backend Photo model
photo = Photo(
    # From CorePhoto
    hothash=core_photo.hothash,
    hotpreview=base64.b64decode(core_photo.hotpreview_base64),
    width=core_photo.width,
    height=core_photo.height,
    taken_at=core_photo.taken_at,
    camera_make=core_photo.camera_make,
    camera_model=core_photo.camera_model,
    gps_latitude=core_photo.gps_latitude,
    gps_longitude=core_photo.gps_longitude,
    
    # Backend additions
    user_id=current_user.id,
    rating=0,
    visibility="private",
    title=None,
    description=None,
    
    # NOT from CorePhoto (too large)
    # coldpreview - stored separately or generated on-demand
)
```

---

### Photo (Backend Database Model)

**Purpose**: Persisted photo data with user ownership  
**Source**: Backend database  
**Differences from CorePhoto**:

| Field | CorePhoto | Backend Photo | Notes |
|-------|-----------|---------------|-------|
| `id` | ❌ No | ✅ Yes | Database primary key |
| `user_id` | ❌ No | ✅ Yes | User ownership (REQUIRED) |
| `hothash` | ✅ Yes | ✅ Yes | Same (unique ID) |
| `hotpreview` | ✅ base64 | ✅ bytes | Backend stores as BLOB |
| `coldpreview` | ✅ base64 | ❌ No | Too large for DB |
| `taken_at` | ✅ Yes | ✅ Yes | Can be user-corrected |
| `camera_make/model` | ✅ Yes | ✅ Yes | Same |
| `gps_latitude/longitude` | ✅ Yes | ✅ Yes | Same |
| `title` | ❌ No | ✅ Yes | User-added |
| `description` | ❌ No | ✅ Yes | User-added |
| `rating` | ❌ No | ✅ Yes | User organization (0-5) |
| `visibility` | ❌ No | ✅ Yes | Access control |
| `tags` | ❌ No | ✅ Yes (relation) | User organization |
| `created_at` | ❌ No | ✅ Yes | Backend timestamp |
| `updated_at` | ❌ No | ✅ Yes | Backend timestamp |

---

## Version Compatibility

### Current Versions
- **Backend**: v0.1.x (pre-1.0, can break between minors)
- **imalink-core**: v1.0.x (follows SemVer)

### Version Constraints
```toml
# pyproject.toml
[project]
dependencies = [
    "imalink-core>=1.0.0,<2.0.0",  # Pin to major version
]
```

### Breaking Change Protocol

**When imalink-core releases 2.x**:
1. ⚠️ **Do not upgrade immediately**
2. Review BACKEND_MIGRATION.md in imalink-core repo
3. Test in isolated environment (separate branch)
4. Update mapping code in `src/services/photo_service.py`
5. Run full test suite (`uv run pytest`)
6. Update contract tests
7. Update `pyproject.toml` dependency
8. Deploy with monitoring

**What constitutes a breaking change**:
- ❌ Removing fields from CorePhoto
- ❌ Renaming fields in CorePhoto
- ❌ Changing field types in CorePhoto
- ❌ Removing public API functions
- ❌ Changing ImportResult structure
- ✅ Adding new optional fields (non-breaking)
- ✅ Adding new functions (non-breaking)
- ✅ Internal refactoring (non-breaking)

---

## Testing Contracts

### Contract Tests (Backend)

**Purpose**: Verify imalink-core integration still works  
**Location**: `tests/contracts/test_imalink_core_integration.py`

```python
"""
Contract tests - catch breaking changes in imalink-core.
Run these tests before updating imalink-core dependency.
"""
from imalink_core import process_image, __version__
from pathlib import Path

def test_core_version():
    """Verify compatible imalink-core version"""
    major, minor, patch = map(int, __version__.split('.'))
    assert major == 1, "imalink-core 2.x requires backend migration"

def test_process_image_contract():
    """Verify process_image returns expected structure"""
    result = process_image(Path("tests/fixtures/test.jpg"))
    
    # Required fields
    assert hasattr(result, 'success')
    assert hasattr(result, 'hothash')
    assert hasattr(result, 'photo')
    assert hasattr(result.photo, 'hotpreview_base64')
    assert hasattr(result.photo, 'hothash')
    assert hasattr(result.metadata, 'taken_at')
    
    # Verify types
    assert isinstance(result.success, bool)
    assert isinstance(result.hothash, str)
    assert len(result.hothash) == 64

def test_photo_to_dict_contract():
    """Verify CorePhoto.to_dict() includes expected fields"""
    result = process_image(Path("tests/fixtures/test.jpg"))
    photo_dict = result.photo.to_dict()
    
    # Required fields
    assert 'hothash' in photo_dict
    assert 'hotpreview_base64' in photo_dict
    assert 'width' in photo_dict
    assert 'height' in photo_dict
    
    # Optional fields (can be None)
    assert 'taken_at' in photo_dict
    assert 'camera_make' in photo_dict
    assert 'gps_latitude' in photo_dict
```

---

## PhotoEgg API Contract (Planned)

### New Endpoint (To Be Implemented)

**Endpoint**: `POST /api/v1/photos/photoegg`

**Request Body** (PhotoEgg from imalink-core):
```json
{
  "hothash": "abc123...",
  "hotpreview_base64": "/9j/4AAQ...",
  "hotpreview_width": 150,
  "hotpreview_height": 113,
  "coldpreview_base64": null,
  "coldpreview_width": null,
  "coldpreview_height": null,
  "primary_filename": "IMG_1234.jpg",
  "width": 4032,
  "height": 3024,
  "taken_at": "2024-11-10T14:30:00",
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "has_gps": true,
  "iso": 400,
  "aperture": 2.8,
  "shutter_speed": "1/1000",
  "focal_length": 85.0,
  "lens_model": "RF 85mm F2",
  "lens_make": "Canon"
}
```

**Response**:
```json
{
  "id": 123,
  "hothash": "abc123...",
  "user_id": 1,
  "rating": 0,
  "visibility": "private",
  "created_at": "2024-11-10T15:30:00Z"
}
```

**Implementation Status**: 🔴 Not yet implemented  
**Migration Guide**: See imalink-core/BACKEND_MIGRATION.md

---

## Questions & Support

**Before making changes**:
1. Check this contract document
2. Review imalink-core CHANGELOG
3. Run contract tests
4. Test with real images

**When contract breaks**:
1. Create GitHub issue in imalink-core repo
2. Tag with `breaking-change` label
3. Coordinate migration timeline
4. Update this CONTRACTS.md

**Resources**:
- imalink-core repo: https://github.com/kjelkols/imalink-core
- Backend repo: https://github.com/kjelkols/imalink
- Migration guide: imalink-core/BACKEND_MIGRATION.md
- API reference: docs/API_REFERENCE.md
