# Schema Sharing Strategy: imalink-schemas

## Decision: Shared Python Package

Both `imalink` (backend) and `imalink-core` will use a shared `imalink-schemas` package containing `PhotoCreateSchema` and `ImageFileCreateSchema`.

## Implementation Plan

### Phase 1: Create imalink-schemas Repository

```bash
# New repository structure
imalink-schemas/
├── pyproject.toml
├── README.md
└── src/
    └── imalink_schemas/
        ├── __init__.py           # Exports all schemas
        ├── version.py            # SCHEMA_VERSION = "2.0.0"
        │
        ├── photo.py              # PhotoCreateSchema, PhotoUpdateSchema, PhotoResponse
        ├── image_file.py         # ImageFileCreateSchema, ImageFileResponse
        ├── author.py             # AuthorCreateSchema, AuthorResponse
        ├── tag.py                # TagCreateSchema, TagResponse
        ├── import_session.py     # ImportSessionCreateSchema, ImportSessionResponse
        ├── user.py               # UserCreateSchema, UserResponse (without password)
        ├── timeline.py           # TimelineBucketResponse, TimelineQueryParams
        │
        ├── base.py               # Base classes and common validators
        ├── enums.py              # VisibilityLevel, CategoryType, etc.
        └── errors.py             # Shared error response schemas
```

### Phase 2: Schema Categories

**Core Data Schemas (Create/Update/Response):**
- `photo.py`: PhotoCreateSchema, PhotoUpdateSchema, PhotoResponse, PhotoListResponse
- `image_file.py`: ImageFileCreateSchema, ImageFileResponse
- `author.py`: AuthorCreateSchema, AuthorUpdateSchema, AuthorResponse
- `tag.py`: TagCreateSchema, TagResponse, TagAutocompleteResponse
- `import_session.py`: ImportSessionCreateSchema, ImportSessionResponse, ImportSessionStatsResponse
- `photo_stack.py`: PhotoStackCreateSchema, PhotoStackResponse
- `user.py`: UserCreateSchema, UserResponse (excluding passwords/secrets)

**Query & Filter Schemas:**
- `timeline.py`: TimelineBucketResponse, TimelineQueryParams
- `search.py`: PhotoSearchParams, SearchResultResponse
- `filters.py`: DateRangeFilter, LocationFilter, RatingFilter

**Common/Shared:**
- `base.py`: BaseSchema, PaginatedResponse, TimestampMixin
- `enums.py`: VisibilityLevel, CategoryType, FileType, ImportStatus
- `errors.py`: ErrorResponse, ValidationErrorResponse
- `corrections.py`: TimeLocCorrectionSchema, ViewCorrectionSchema

**Benefits of Complete Schema Package:**
- ✅ All API contracts in one place
- ✅ imalink-core knows exact response format expected by backend
- ✅ imalink-frontend can use same schemas for local validation
- ✅ imalink-web (TypeScript) can generate types from schemas
- ✅ Consistent error handling across all services
- ✅ Shared validators and business rules

### Phase 3: Configure Both Projects

**imalink/pyproject.toml:**
```toml
dependencies = [
    "imalink-schemas @ git+https://github.com/kjelkols/imalink-schemas.git@v2.0.0",
    # ... other deps
]
```

**imalink-core/pyproject.toml:**
```toml
dependencies = [
    "imalink-schemas @ git+https://github.com/kjelkols/imalink-schemas.git@v2.0.0",
    # ... other deps
]
```

### Phase 3: Update Imports

**In imalink (backend):**
```python
from imalink_schemas import PhotoCreateSchema, ImageFileCreateSchema, SCHEMA_VERSION
```

**In imalink-core:**
```python
from imalink_schemas import PhotoCreateSchema, ImageFileCreateSchema, SCHEMA_VERSION
```

## Version Management

### Semantic Versioning
- **Major (X.0.0)**: Breaking changes (remove/rename fields)
- **Minor (1.X.0)**: New optional fields
- **Patch (1.0.X)**: Documentation, validation changes

### Release Process
1. Make schema changes in `imalink-schemas` repo
2. Tag new version: `git tag v2.1.0 && git push --tags`
3. Update dependency in both `imalink` and `imalink-core`
4. Deploy both services (or handle backward compatibility)

### Compatibility Check
Add startup validation in both services:

```python
# src/main.py (in both imalink and imalink-core)
from imalink_schemas import SCHEMA_VERSION

@app.on_event("startup")
async def validate_schema_version():
    expected = "2.0.0"
    if SCHEMA_VERSION != expected:
        raise RuntimeError(f"Schema version mismatch: expected {expected}, got {SCHEMA_VERSION}")
    logger.info(f"Using imalink-schemas v{SCHEMA_VERSION}")
```

## Alternative: Local Development Override

For rapid development, use editable install:

```bash
# Clone schemas repo locally
cd ~/projects
git clone https://github.com/kjelkols/imalink-schemas.git

# In imalink or imalink-core
uv pip install -e ~/projects/imalink-schemas
```

Changes to schemas are immediately reflected in both services.

## Migration Path

### Current State
- Schemas defined in `imalink/src/schemas/photo_create_schemas.py`
- `imalink-core` has no shared access

### Migration Steps
1. ✅ Fix PhotoCreateSchema to match MY_OVERVIEW.md (current task)
2. Create `imalink-schemas` repository with corrected schemas
3. Update `imalink` to import from `imalink-schemas`
4. Update `imalink-core` to import from `imalink-schemas`
5. Remove duplicate schema definitions from both repos

## Benefits

✅ **Single Source of Truth**: Schema defined once, used everywhere
✅ **Type Safety**: Pydantic validation in both services
✅ **Version Control**: Git tags for schema versions
✅ **Easy Updates**: Change once, update dependency version
✅ **IDE Support**: Full autocompletion and type hints
✅ **Testing**: Schema validation tests in shared package

## Potential Issues & Solutions

**Issue**: Dependency update coordination
**Solution**: Use CI/CD to test both services with new schema versions

**Issue**: Breaking changes
**Solution**: Use major version bumps, maintain backward compatibility layers

**Issue**: Local development friction
**Solution**: Use editable installs during active development

## Cross-Language Usage

### imalink-desktop (Rust)
Generate Rust types from Python schemas:

```bash
# Option 1: Via JSON Schema (recommended)
# Generate JSON Schema from Pydantic
python -m imalink_schemas.codegen.generate_json_schema --output schemas.json

# Generate Rust types with serde
quicktype schemas.json \
  --lang rust \
  --derive-debug \
  --visibility public \
  -o src/schemas.rs
```

**In imalink-desktop/src/schemas.rs:**
```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhotoCreateSchema {
    pub hothash: String,
    pub hotpreview: String,
    pub exif_dict: Option<serde_json::Value>,
    pub width: i32,
    pub height: i32,
    pub image_file_list: Vec<ImageFileCreateSchema>,
    // ... other fields
}

// Validate JSON from imalink-core
pub fn validate_photo_schema(json: &str) -> Result<PhotoCreateSchema, serde_json::Error> {
    serde_json::from_str(json)
}
```

### imalink-web (TypeScript)
```bash
# Generate TypeScript types
datamodel-codegen \
  --input imalink_schemas/ \
  --input-file-type python \
  --output src/types/schemas.ts
```

## Decision Rationale

- **Python services** (imalink, imalink-core) → Native Pydantic sharing
- **Rust desktop** (imalink-desktop) → JSON Schema → serde types
- **TypeScript web** (imalink-web) → JSON Schema → TypeScript interfaces
- Services are tightly coupled → Breaking changes acceptable
- Small team → Coordination overhead manageable
- Single source of truth → All clients stay in sync
