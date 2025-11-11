# ImaLink Backend Development Guide

## Module Purpose
FastAPI backend for photo metadata management with multi-user support, visibility controls, and timeline features.

**Core Philosophy**: Backend NEVER processes images - only metadata storage, organization, and access control.

## Architecture Principles

### 1. Hash-Based Photo Identity
- **Hothash** (SHA256 of hotpreview): Unique photo identifier across all systems
- **Hybrid PK**: Integer `id` (technical FK) + unique `hothash` (API operations)
- Use `hothash` in API paths: `/photos/{hothash}` not `/photos/{id}`
- JPEG+RAW pairs share same hothash → same Photo entity
- Filenames/locations irrelevant - hash is source of truth

### 2. Three-Layer Architecture
```
src/
├── api/v1/          # FastAPI endpoints - request validation, auth
├── services/        # Business logic - orchestrates repos
├── repositories/    # Database queries - SQLAlchemy ORM
├── schemas/         # Pydantic models - request/response validation
└── models/          # SQLAlchemy ORM - database entities
```

**Pattern**: `API → Service → Repository → Database`
- Never skip layers (e.g., API calling Repository directly)
- Use `src.` prefix for all internal imports
- Services contain business logic, repos contain queries

### 3. User Isolation (CRITICAL)
- **Every Photo/Tag/Author belongs to one User** (`user_id` required)
- All queries MUST filter by `user_id` OR visibility level
- Never expose private data to other users
- Visibility hierarchy: `private` < `space` < `authenticated` < `public`

### 4. External Dependencies

**imalink-core** (separate FastAPI server, NOT a library):
- **Repository**: https://github.com/kjelkols/imalink-core
- **Architecture**: Separate FastAPI server on localhost:8001 (configurable)
- **Flow**: Frontend sends image → imalink-core → PhotoEgg JSON → Backend
- **Backend role**: Receives pre-processed metadata only, NO image processing
- **Critical contract**: PhotoEgg schema defined in imalink-core, consumed here

**PhotoEgg Contract** (defined in imalink-core):
```json
{
  "hothash": "sha256...",
  "hotpreview_base64": "...",
  "coldpreview_base64": "..." | null,
  "width": 4000, "height": 3000,
  "metadata": { "taken_at": "...", "camera_make": "...", ... },
  "exif_dict": { ... }
}
```

**Backend implementation**: `src/schemas/photoegg_schemas.py` defines Pydantic models that validate incoming PhotoEgg data. This is backend's CONTRACT ENFORCEMENT, not the source definition.

**For AI agents**: When PhotoEgg schema questions arise:
1. Use `@github` tool to search `kjelkols/imalink-core` repository
2. Look for PhotoEgg/CorePhoto definitions in imalink-core codebase
3. Check `docs/CONTRACTS.md` in THIS repo for contract documentation
4. PhotoEgg is the SOURCE OF TRUTH - backend adapts to its schema
5. **Version compatibility**: v2.0+ added optional fields with defaults for backward compatibility


## Development Workflow

### Running Locally
```bash
# Start backend (from project root)
uvicorn src.main:app --reload --port 8000

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/api/test_timeline.py -v

# Run tests with coverage
uv run pytest --cov=src tests/

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Test Strategy
- **Fixtures**: Use PhotoEgg pattern from `tests/fixtures/photo_eggs.py`
- **Database**: SQLite in-memory for tests, PostgreSQL for production
- **Isolation**: Each test gets fresh database via `test_db_session` fixture
- **Critical coverage**: User isolation, visibility filtering, timeline aggregation
- **Pattern**: Create test users → Create photos → Assert access control

### Code Conventions
- **Imports**: Always use `src.` prefix (`from src.models import Photo`)
- **Type hints**: Required for all function signatures
- **Validation**: Pydantic schemas for API requests/responses
- **Error handling**: Raise domain exceptions (`NotFoundError`, `ValidationError`)
- **Repository pattern**: All database queries through repository layer
- **Service pattern**: Business logic orchestrates multiple repos

## Common Patterns

### User Authentication
```python
from src.core.dependencies import get_current_user, get_current_user_optional

# Protected endpoint (requires auth)
@router.get("/photos")
async def list_photos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    photos = photo_repo.list_by_user(db, current_user.id)
    ...

# Public endpoint (optional auth)
@router.get("/timeline")
async def timeline(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    user_id = current_user.id if current_user else None
    ...
```

### Visibility Filtering (Repository Layer)
```python
# In photo_repository.py
def get_photos(self, user_id: Optional[int], ...):
    query = self.db.query(Photo)
    
    if user_id:
        # Authenticated: own photos + accessible to user
        query = query.filter(
            (Photo.user_id == user_id) | 
            (Photo.visibility.in_(["authenticated", "public"]))
        )
    else:
        # Anonymous: only public photos
        query = query.filter(Photo.visibility == "public")
    
    return query.all()
```

### Creating Photos from PhotoEgg
```python
# In photo_service.py
def create_photo_from_photoegg(self, photoegg: PhotoEggRequest, user_id: int):
    # 1. Decode base64 → bytes
    hotpreview_bytes = base64.b64decode(photoegg.hotpreview_base64)
    
    # 2. Store ALL metadata in exif_dict JSON (flexible schema)
    exif_dict = {
        "taken_at": photoegg.metadata.taken_at.isoformat(),
        "camera_make": photoegg.metadata.camera_make,
        **photoegg.exif_dict  # Merge all EXIF data
    }
    
    # 3. Create Photo with indexed fields extracted
    photo = Photo(
        user_id=user_id,
        hothash=photoegg.hothash,
        hotpreview=hotpreview_bytes,
        exif_dict=exif_dict,  # Complete metadata
        taken_at=photoegg.metadata.taken_at,  # Indexed for queries
        gps_latitude=photoegg.metadata.gps_latitude,
        visibility="private"  # Default
    )
    self.db.add(photo)
    self.db.commit()
    return photo
```

### Error Handling
```python
from src.core.exceptions import NotFoundError, DuplicatePhotoError, AuthorizationError

# In service layer
def get_photo(self, hothash: str, user_id: int):
    photo = self.photo_repo.get_by_hash(hothash, user_id)
    if not photo:
        raise NotFoundError("Photo", hothash)
    
    # Check ownership for write operations
    if photo.user_id != user_id:
        raise AuthorizationError("Cannot modify other user's photo")
    
    return photo
```

## Database Schema

### Core Models
- **User**: `id`, `email`, `hashed_password` (authentication)
- **Photo**: `id`, `hothash`, `user_id`, `hotpreview` (BLOB), `exif_dict` (JSON), `visibility`, `taken_at`
- **ImageFile**: `id`, `photo_id`, `filename`, `file_path` (original files)
- **Tag**: `id`, `user_id`, `name` (user-scoped tags)
- **PhotoTag**: `photo_id`, `tag_id` (many-to-many)
- **Author**: `id`, `user_id`, `name`, `email` (photographers)
- **PhotoStack**: Groups related files (RAW+JPEG pairs, panoramas)

### Critical Indexes
```sql
-- User isolation
CREATE INDEX idx_photos_user_id ON photos(user_id);

-- Timeline queries
CREATE INDEX idx_photos_taken_at ON photos(taken_at);
CREATE INDEX idx_photos_visibility ON photos(visibility);
CREATE INDEX idx_photos_taken_at_visibility ON photos(taken_at, visibility);

-- Duplicate detection
CREATE UNIQUE INDEX idx_photos_hothash ON photos(hothash);
```


## Key API Endpoints

### Photo Management
- `POST /api/v1/photos/new-photo` - Create photo with hotpreview + ImageFile
- `GET /api/v1/photos` - List photos (paginated, visibility-filtered)
- `GET /api/v1/photos/{hothash}` - Get photo details
- `GET /api/v1/photos/{hothash}/hotpreview` - Get hotpreview image (JPEG bytes)
- `PUT /api/v1/photos/{hothash}` - Update photo metadata
- `DELETE /api/v1/photos/{hothash}` - Delete photo
- `PATCH /api/v1/photos/{hothash}/timeloc-correction` - Correct time/location
- `PATCH /api/v1/photos/{hothash}/view-correction` - Visual adjustments (frontend hints)

### Timeline API
- `GET /api/v1/timeline?granularity=year` - Hierarchical time aggregation
  - Query params: `granularity` (year/month/day/hour), `year`, `month`, `day`
  - Returns: Buckets with photo counts + representative preview
  - Preview selection: Rating 4-5 stars → temporal center fallback
  - Supports anonymous access (public photos only)

### Tags
- `GET /api/v1/tags` - List user's tags with counts
- `GET /api/v1/tags/autocomplete?q=land` - Tag suggestions
- `POST /api/v1/photos/{hothash}/tags` - Add tags to photo
- `DELETE /api/v1/photos/{hothash}/tags/{tag_name}` - Remove tag

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - Get JWT token
- Protected endpoints require: `Authorization: Bearer <token>`

## Important Constraints

### Security
- **JWT tokens**: 24-hour expiration (configurable in `src/utils/security.py`)
- **Password hashing**: sha256_crypt (configured in `src/utils/security.py`)
- **SQL injection**: Prevented via SQLAlchemy ORM (never raw SQL)
- **User isolation**: Enforced at repository layer - NEVER skip checks
- **CORS**: Configured in `src/main.py` (production: restrict origins)

### Performance
- **Pagination**: Required for list endpoints (default limit=50, max=100)
- **Timeline API**: Uses SQL aggregation (COUNT, GROUP BY) - NOT Python loops
- **Hotpreview**: Stored in database BLOB for instant gallery rendering
- **Coldpreview**: Optional larger preview (filesystem or database)
- **Database indexes**: See "Critical Indexes" section above

### Data Integrity
- **Hothash uniqueness**: Enforced by unique constraint - duplicate detection
- **User-scoped tags**: Same tag name allowed across users (composite key)
- **Visibility defaults**: New photos default to `"private"`
- **JSON fields**: `exif_dict`, `timeloc_correction`, `view_correction` - flexible schema
- **Nullable fields**: `author_id`, `coldpreview_path`, GPS coordinates

## Configuration & Environment

### Environment Variables (.env)
```bash
# Database (SQLite for dev/test, PostgreSQL for production)
DATABASE_URL=sqlite:////mnt/c/temp/00imalink_data/imalink.db
# DATABASE_URL=postgresql://user:pass@localhost/imalink

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-in-production

# Storage paths
DATA_DIRECTORY=/tmp/imalink_data
COLDPREVIEW_ROOT=/tmp/imalink_coldpreviews

# Testing (set by tests/conftest.py)
TESTING=1  # Uses sqlite:///:memory:
```

### Project Structure
```
imalink/
├── src/
│   ├── api/v1/          # FastAPI route handlers
│   ├── services/        # Business logic layer
│   ├── repositories/    # Database query layer
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response models
│   ├── core/            # Config, dependencies, exceptions
│   ├── database/        # DB connection & session management
│   └── utils/           # Security, helpers
├── tests/
│   ├── api/             # API endpoint tests
│   ├── services/        # Service layer tests
│   ├── repositories/    # Repository tests
│   └── fixtures/        # Shared test data (PhotoEggs)
├── alembic/             # Database migrations
├── docs/                # API reference, architecture docs
└── scripts/             # Maintenance, migration scripts
```

## Debugging Tips

### Check Auth Issues
```python
# Test token generation
from src.utils.security import create_access_token
token = create_access_token({"sub": "1"})
print(token)  # Should be valid JWT

# Verify user from token
from src.core.dependencies import get_current_user
# Use in FastAPI dependency
```

### Database State
```bash
# Check database directly
sqlite3 /mnt/c/temp/00imalink_data/imalink.db

# Useful queries
SELECT COUNT(*) FROM photos;
SELECT visibility, COUNT(*) FROM photos GROUP BY visibility;
SELECT user_id, COUNT(*) FROM photos GROUP BY user_id;
```

### API Testing
```bash
# Health check
curl http://localhost:8000/

# List routes
curl http://localhost:8000/debug/routes

# Login and get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

## Migration & Maintenance

### Alembic Migrations
```bash
# Generate migration from model changes
alembic revision --autogenerate -m "add_new_field"

# Review generated migration before applying!
# Edit alembic/versions/*.py if needed

# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current
```

### Database Reset (Development Only)
```bash
# Nuclear option - deletes everything
python scripts/nuclear_reset.py

# Safer option - reset with confirmation
python scripts/reset_database.py
```

## Known Issues & Gotchas

1. **User isolation**: Always check `user_id` in repositories - easy to forget
2. **Visibility filtering**: Anonymous users (`user_id=None`) only see public photos
3. **Hothash vs ID**: Use `hothash` in API paths, `id` only for foreign keys
4. **PhotoEgg base64**: Must decode before storing in database (`base64.b64decode()`)
5. **Timeline indexes**: Required for performance - see `alembic/versions/*timeline_indexes.py`
6. **Testing database**: Uses in-memory SQLite - different from production PostgreSQL
7. **CORS in production**: Update `src/main.py` to restrict origins (currently allows all)

## Additional Resources

- **API Reference**: `docs/API_REFERENCE.md` - Complete endpoint documentation
- **Timeline API**: `docs/TIMELINE_API.md` - Detailed timeline design & examples
- **Contracts**: `docs/CONTRACTS.md` - External API contracts (imalink-core)
- **README**: `README.md` - Project overview, design philosophy
- **Examples**: `examples/` - API usage examples, demo scripts

### External Codebases

When working with PhotoEgg schema or imalink-core integration:
- **imalink-core repository**: https://github.com/kjelkols/imalink-core
- Use GitHub search tools to query imalink-core for PhotoEgg/CorePhoto definitions
- PhotoEgg schema changes in imalink-core require backend migration updates
- Check imalink-core's `README.md` and API documentation for processing capabilities
