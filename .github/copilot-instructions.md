# ImaLink Backend Development Guide

## Module Purpose
FastAPI backend for photo metadata management with multi-user support, visibility controls, and timeline features.

**NEW ARCHITECTURE (2024)**: Backend receives PhotoEgg JSON from frontend (which got it from imalink-core server). Backend does NO image processing - only metadata storage and organization.

## Architecture Principles

### 1. PhotoEgg Architecture (NEW)
- **imalink-core runs as separate FastAPI server** (localhost, same machine)
- **Frontend sends image → imalink-core server → PhotoEgg JSON**
- **Frontend sends PhotoEgg → Backend → Database storage**
- Backend NEVER processes images directly
- Backend stores metadata + previews (base64) in database

### 2. Photo Model
- **Backend Photo**: Database entity with user organization
  - From PhotoEgg: hothash, hotpreview, coldpreview, width, height, EXIF metadata
  - User additions: user_id, title, description, tags, rating, visibility
- **No original files stored** - user's responsibility on local machine
- Previews stored as bytes (decoded from base64) in database

### 3. User Isolation
- **Every Photo belongs to one User** (user_id required)
- All queries MUST filter by user_id or visibility level
- Never expose private photos to other users
- Visibility levels: private < space < authenticated < public

### 4. Visibility System
```python
VISIBILITY_LEVELS = {
    "private": 0,      # Only owner
    "space": 1,        # Shared with specific users/groups (future)
    "authenticated": 2, # All logged-in users
    "public": 3        # Everyone including anonymous
}
```

### 5. Preview Storage
- **Hotpreview**: BLOB in database (~5-15KB, 150x150px JPEG)
- **Coldpreview**: BLOB in database (~50-200KB, variable size JPEG) - OPTIONAL
- Both come pre-processed from PhotoEgg
- No on-demand generation - all from imalink-core server

## External Dependencies

### imalink-core Server
**Type**: Separate FastAPI server (not a library!)  
**Source**: https://github.com/kjelkols/imalink-core  
**Deployment**: Runs on localhost (same machine as backend)  
**Port**: Typically 8001 (configurable)

**What it does**:
- Receives images from frontend
- Processes images (EXIF extraction, preview generation, hashing)
- Returns PhotoEgg JSON
- Stateless - no storage

**Backend does NOT import imalink-core** - it's a separate service!

### PhotoEgg Contract
PhotoEgg is the JSON package from imalink-core server:

```json
{
  "hothash": "sha256_hash_of_hotpreview",
  "hotpreview_base64": "/9j/4AAQSkZJRg...",
  "coldpreview_base64": "/9j/4AAQSkZJRg..." or null,
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

**Backend receives this and adds**:
- user_id (from authentication)
- title, description (from user input)
- rating, visibility (from user preferences)
- tags, author_id (from user organization)


**Breaking Change Protocol**:
- imalink-core 2.x requires backend migration
- Test in isolated environment first
- Update mapping code in `photo_service.py`
- Run full test suite before deploying
- Update `pyproject.toml` dependency

## Key API Endpoints

### Photo Management
- `POST /api/v1/photos` - Create photo (legacy)
- `POST /api/v1/photos/photoegg` - Create from PhotoEgg (recommended)
- `GET /api/v1/photos` - List photos (paginated, filtered by user_id/visibility)
- `GET /api/v1/photos/{id}` - Get photo details
- `GET /api/v1/photos/{id}/hotpreview` - Get hotpreview image
- `PUT /api/v1/photos/{id}` - Update photo metadata
- `DELETE /api/v1/photos/{id}` - Delete photo

### Coldpreview Management (by hothash)
- `PUT /api/v1/photos/{hothash}/coldpreview` - Upload coldpreview separately
- `GET /api/v1/photos/{hothash}/coldpreview` - Get coldpreview (with optional resize)
- `DELETE /api/v1/photos/{hothash}/coldpreview` - Delete coldpreview
- **Note**: These are functional legacy endpoints. PhotoEgg can include coldpreview, but these allow separate upload.

### Timeline API
- `GET /api/v1/timeline` - Hierarchical time aggregation
  - Query params: `granularity` (year/month/day/hour), `year`, `month`, `day`, `visibility`
  - Returns: Buckets with photo counts + preview selection
  - Preview selection: Rating 4-5 stars → temporal center fallback

### Import Sessions
- `POST /api/v1/import-sessions/` - Start import
- `GET /api/v1/import-sessions/{id}` - Get status
- Background processing with progress tracking

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - Get JWT token
- All protected endpoints require: `Authorization: Bearer <token>`

## Database Schema

### Core Models
- `User`: id, email, hashed_password, created_at
- `Photo`: id, user_id, hothash, hotpreview, taken_at, rating, visibility, exif_dict
- `ImageFile`: id, photo_id, filename, file_path, file_format, file_size
- `PhotoStack`: Groups related files (JPEG+RAW pairs, panoramas, etc.)
- `Author`: id, user_id, name, description
- `Tag`: id, user_id, name
- `PhotoTag`: photo_id, tag_id

### Indexes
- `photos.user_id` (user isolation queries)
- `photos.hothash` (duplicate detection)
- `photos.taken_at` (timeline queries)
- `photos.visibility` (access control)
- Composite: `(taken_at, visibility)` for timeline API

## Testing Strategy

### Test Fixtures
- Use PhotoEgg pattern for consistent test data
- Store test photos as JSON in `tests/fixtures/`
- Generate eggs via imalink-core: `result.photo.to_dict()`

### Test Database
- SQLite for tests (`test_imalink.db`)
- PostgreSQL for production
- Clean database between test runs

### Critical Tests
- User isolation (no cross-user data leaks)
- Visibility filtering (correct access control)
- Timeline aggregation accuracy
- Duplicate detection (hothash collision handling)
- EXIF metadata preservation

## Code Organization

```
src/
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── repositories/    # Database query layer
├── services/        # Business logic
├── api/             # FastAPI endpoints (v1/)
├── core/            # Config, dependencies, exceptions
├── database/        # DB connection, session management
└── utils/           # Helpers (EXIF, coldpreview, etc.)
```

## Development Workflow

### Running Locally
```bash
# Start server
uvicorn src.main:app --reload --port 8000

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/api/test_timeline.py -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Code Style
- Use `src.` prefix for all imports from project
- Type hints required for all functions
- Pydantic models for validation
- Repository pattern for database access
- Service layer for business logic

## Common Patterns

### User Context
```python
from src.core.dependencies import get_current_user

@router.get("/photos")
async def list_photos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Always filter by user_id
    photos = photo_repo.list_by_user(db, current_user.id)
```

### Visibility Filtering
```python
# Get photos accessible to user
photos = photo_repo.list_accessible(
    db=db,
    viewer_user_id=current_user.id,  # or None for anonymous
    min_visibility="authenticated"
)
```

### Photo Creation from PhotoEgg
```python
# In API endpoint (photos.py)
@router.post("/photoegg", response_model=PhotoEggResponse)
async def create_photo_from_photoegg(
    photoegg: PhotoEggRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check for duplicates
    existing = photo_service.get_photo_by_hothash(photoegg.hothash, current_user.id)
    if existing:
        return PhotoEggResponse(id=existing.id, is_duplicate=True)
    
    # Create from PhotoEgg
    photo = photo_service.create_photo_from_photoegg(photoegg, current_user.id)
    return PhotoEggResponse(id=photo.id, is_duplicate=False)
```

```python
# In service layer (photo_service.py)
def create_photo_from_photoegg(
    self, 
    photoegg_request: PhotoEggRequest, 
    user_id: int
) -> Photo:
    # Decode base64 hotpreview to bytes
    hotpreview_bytes = base64.b64decode(photoegg_request.hotpreview_base64)
    
    # Handle coldpreview if provided (save to filesystem)
    coldpreview_path = None
    if photoegg_request.coldpreview_base64:
        coldpreview_bytes = base64.b64decode(photoegg_request.coldpreview_base64)
        coldpreview_path = self.coldpreview_repo.save_coldpreview(
            photoegg_request.hothash, 
            coldpreview_bytes
        )
    
    # Store ALL metadata in exif_dict JSON (flexible schema)
    exif_dict = {
        "taken_at": photoegg_request.metadata.taken_at.isoformat() if photoegg_request.metadata.taken_at else None,
        "camera_make": photoegg_request.metadata.camera_make,
        "camera_model": photoegg_request.metadata.camera_model,
        "lens_model": photoegg_request.metadata.lens_model,
        "focal_length": photoegg_request.metadata.focal_length,
        "f_number": photoegg_request.metadata.f_number,
        "iso": photoegg_request.metadata.iso,
        "exposure_time": photoegg_request.metadata.exposure_time,
        "gps_altitude": photoegg_request.metadata.gps_altitude,
        # Add any other metadata from photoegg_request.exif_dict
        **photoegg_request.exif_dict
    }
    
    # Create Photo with core fields only
    photo = Photo(
        user_id=user_id,
        hothash=photoegg_request.hothash,
        hotpreview=hotpreview_bytes,
        coldpreview_path=coldpreview_path,  # Filesystem path or None
        width=photoegg_request.width,
        height=photoegg_request.height,
        exif_dict=exif_dict,  # ALL metadata stored here
        
        # User-provided metadata
        title=photoegg_request.title,
        description=photoegg_request.description,
        rating=photoegg_request.rating or 0,
        visibility=photoegg_request.visibility or "private",
        
        # Extract key fields for indexed queries
        taken_at=photoegg_request.metadata.taken_at,
        gps_latitude=photoegg_request.metadata.gps_latitude,
        gps_longitude=photoegg_request.metadata.gps_longitude,
    )
    
    self.db.add(photo)
    self.db.commit()
    self.db.refresh(photo)
    
    # TODO: Handle tag association if photoegg_request.tags provided
    
    return photo
```

## Migration Notes

### Timeline API (Implemented)
- Added hierarchical time aggregation
- Requires indexes: `photos.taken_at`, `photos.visibility`
- Preview selection uses rating + temporal center
- All 26 tests passing

### PhotoEgg API (Implemented)
- ✅ New endpoint: `POST /api/v1/photos/photoegg`
- ✅ Receives PhotoEgg JSON from frontend (which got it from imalink-core server)
- ✅ Handles optional coldpreview_base64
- ✅ Duplicate detection via hothash
- ✅ Hotpreview stored as BLOB in database
- ✅ Coldpreview saved to filesystem (coldpreview_path)
- ✅ ALL metadata stored in exif_dict JSON (flexible schema)
- ⏳ TODO: Tag association in create_photo_from_photoegg

### Coldpreview Endpoints (Legacy but Functional)
- ✅ PUT /api/v1/photos/{hothash}/coldpreview - Separate coldpreview upload
- ✅ GET /api/v1/photos/{hothash}/coldpreview - Retrieve with optional resize
- ✅ DELETE /api/v1/photos/{hothash}/coldpreview - Delete coldpreview
- **Note**: These remain functional for backwards compatibility and separate workflows
- ⏳ TODO: Tag association in create_photo_from_photoegg

## Security Considerations

- JWT tokens with expiration
- Password hashing with bcrypt
- SQL injection prevention (SQLAlchemy ORM)
- User isolation enforced at repository layer
- Rate limiting on auth endpoints (SlowAPI)
- CORS configuration for production

## Performance Guidelines

- Pagination required for list endpoints (default 50 items)
- Timeline API uses efficient SQL aggregation (not Python loops)
- Hotpreview stored in DB for fast gallery rendering
- Coldpreview generated on-demand (cached separately)
- Database indexes on high-traffic query columns

## Error Handling

```python
from src.core.exceptions import NotFoundError, ValidationError, DuplicatePhotoError

# Raise domain-specific exceptions
if not photo:
    raise NotFoundError(f"Photo {photo_id} not found")

# Service layer catches and translates
# API layer returns proper HTTP status codes
```

## Future Considerations

- Multi-user spaces/groups (visibility="space")
- S3/object storage for coldpreviews
- PhotoText document support (already implemented)
- Advanced search with filters
- Batch operations
- Export/backup functionality

## Questions & Coordination

**Before breaking changes**:
1. Check imalink-core version compatibility
2. Review BACKEND_MIGRATION.md if updating core library
3. Run full test suite
4. Update API documentation
5. Coordinate with frontend teams

**When in doubt**:
- Photo model vs CorePhoto: Backend adds user fields, excludes coldpreview
- Visibility: Always filter by user_id or visibility level
- Coldpreview: Generate on-demand, don't store in DB
- Tests: Use PhotoEgg fixtures for consistency
