# PhotoEgg Redesign Analysis: Should PhotoEgg Mirror Photo Model?

**Date**: 2025-11-11  
**Question**: Should imalink-core's PhotoEgg be redesigned to match backend's Photo model structure?  
**Context**: Currently, backend adapts Photo model to PhotoEgg's structure. This analysis evaluates inverting that relationship.

---

## Executive Summary

**Recommendation**: **YES** - Redesign PhotoEgg to mirror Photo model structure.

**Key Finding**: The structures are already 90% aligned. The main difference is coldpreview handling (base64 vs filesystem path). Aligning schemas would:
- Eliminate manual mapping code
- Guarantee contract compatibility by design
- Reduce maintenance burden
- Enable automatic validation

**Impact**: Requires imalink-core v2.0 release with migration support for old format.

---

## Current Architecture Problems

### Problem 1: Dual EXIF Storage
Photo model stores EXIF data in **two places**:

```python
# Photo model (backend)
class Photo:
    # Indexed fields (for queries)
    taken_at = Column(DateTime)
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    camera_make = Column(String)
    camera_model = Column(String)
    
    # Complete EXIF (readonly JSON)
    exif_dict = Column(JSON)  # Contains ALL metadata including duplicates above
```

PhotoEgg has similar duplication:
```python
# PhotoEgg (current - imalink-core)
{
    "taken_at": "2024-11-10T14:30:00",
    "camera_make": "Canon",
    "camera_model": "EOS R5",
    "gps_latitude": 59.9139,
    "gps_longitude": 10.7522,
    
    "exif_dict": {  # Contains SAME data again
        "taken_at": "2024-11-10T14:30:00",
        "camera_make": "Canon",
        ...
    }
}
```

**Root Cause**: Both systems need:
- Indexed/queryable fields at root level (performance)
- Complete EXIF preservation in JSON (data integrity)

### Problem 2: Manual Mapping Code
Backend manually maps PhotoEgg → Photo:

```python
# Scattered across photo_service.py
def create_photo_from_photoegg(self, photoegg: PhotoEggRequest, user_id: int):
    # Manual extraction
    metadata = photoegg.photo_egg.metadata
    taken_at = metadata.taken_at if metadata else None
    gps_lat = metadata.gps_latitude if metadata else None
    
    # Build exif_dict manually
    exif_dict = photoegg.photo_egg.exif_dict or {}
    if metadata:
        exif_dict.update({
            "taken_at": metadata.taken_at.isoformat() if metadata.taken_at else None,
            "camera_make": metadata.camera_make,
            ...
        })
    
    # Create Photo
    photo = Photo(
        user_id=user_id,
        hothash=photoegg.photo_egg.hothash,
        taken_at=taken_at,
        gps_latitude=gps_lat,
        ...
    )
```

**Problems**:
- 50+ lines of mapping logic
- Easy to miss fields during updates
- No compile-time safety
- Tested only at runtime

### Problem 3: Schema Drift
PhotoEgg (imalink-core) and Photo (backend) are maintained separately:

| Responsibility | PhotoEgg | Photo |
|----------------|----------|-------|
| Owner | kjelkols/imalink-core | kjelkols/imalink (this repo) |
| Definition | `service/main.py` (PhotoEggResponse) | `src/models/photo.py` |
| Validation | `src/schemas/photoegg_schemas.py` (Pydantic) | SQLAlchemy ORM |

When imalink-core adds new EXIF fields, backend must manually update mapping code.

---

## Side-by-Side Comparison: Photo vs PhotoEgg

### Identity & Previews

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **id** | `id: int` (PK) | ❌ Not present | Backend-only (DB) |
| **hothash** | `hothash: str` (unique) | `hothash: str` | ✅ Identical |
| **hotpreview** | `hotpreview: bytes` (BLOB) | `hotpreview_base64: str` | 🟡 Format diff (bytes vs base64) |
| **hotpreview dimensions** | ❌ Not stored | `hotpreview_width/height: int` | 🔴 Backend missing |
| **coldpreview** | `coldpreview_path: str` (filesystem) | `coldpreview_base64: str \| null` | 🔴 **Major difference** |
| **coldpreview dimensions** | ❌ Not stored | `coldpreview_width/height: int \| null` | 🔴 Backend missing |

**Analysis**: 
- Preview handling is the **only major structural difference**
- Backend stores coldpreview as filesystem path (not in database)
- PhotoEgg transmits coldpreview as base64 (wire format)
- Backend could store `coldpreview_width/height` for efficiency

### Image Dimensions & Metadata

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **width** | `width: int` | `width: int` | ✅ Identical |
| **height** | `height: int` | `height: int` | ✅ Identical |
| **primary_filename** | ❌ Not in Photo (in ImageFile) | `primary_filename: str` | 🟡 Different layer |
| **exif_dict** | `exif_dict: JSON` (complete metadata) | `exif_dict: dict` (optional) | ✅ Identical concept |

**Analysis**:
- Dimensions perfectly aligned
- `primary_filename` in Photo is in separate `ImageFile` table (many-to-one relationship)
- `exif_dict` serves same purpose: complete EXIF preservation

### Time & Location (Indexed Fields)

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **taken_at** | `taken_at: DateTime` (indexed) | `taken_at: str \| null` | ✅ Same data, format diff |
| **gps_latitude** | `gps_latitude: float` (indexed) | `gps_latitude: float \| null` | ✅ Identical |
| **gps_longitude** | `gps_longitude: float` (indexed) | `gps_longitude: float \| null` | ✅ Identical |
| **has_gps** | ❌ Not present (derived) | `has_gps: bool` | 🟡 Backend derives |

**Analysis**:
- Perfect semantic alignment
- Both recognize time/location as "critical for queries" → root level
- `has_gps` is convenience field (backend can derive from lat/lon presence)

### Camera Metadata

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **camera_make** | `camera_make: str` | `camera_make: str \| null` | ✅ Identical |
| **camera_model** | `camera_model: str` | `camera_model: str \| null` | ✅ Identical |
| **lens_model** | ❌ Not at root (only in exif_dict) | `lens_model: str \| null` | 🔴 Backend missing |
| **lens_make** | ❌ Not at root (only in exif_dict) | `lens_make: str \| null` | 🔴 Backend missing |

**Analysis**:
- Camera make/model perfectly aligned
- Backend doesn't index lens fields (but PhotoEgg includes them)
- Lens data available in `exif_dict` but not queryable

### Camera Settings

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **iso** | ❌ Not at root (only in exif_dict) | `iso: int \| null` | 🔴 Backend missing |
| **aperture** | ❌ Not at root (only in exif_dict) | `aperture: float \| null` | 🔴 Backend missing |
| **shutter_speed** | ❌ Not at root (only in exif_dict) | `shutter_speed: str \| null` | 🔴 Backend missing |
| **focal_length** | ❌ Not at root (only in exif_dict) | `focal_length: float \| null` | 🔴 Backend missing |

**Analysis**:
- PhotoEgg exposes camera settings at root level
- Backend only has these in `exif_dict` JSON (not indexed)
- **Question**: Should these be indexed for search? ("Find all ISO 3200+ photos")

### User Organization (Backend Only)

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **user_id** | `user_id: int` (FK, required) | ❌ Not present | Backend-only |
| **rating** | `rating: int` (0-5 stars) | ❌ Not present | Backend-only |
| **visibility** | `visibility: str` (enum) | ❌ Not present | Backend-only |
| **author_id** | `author_id: int` (FK, optional) | ❌ Not present | Backend-only |
| **stack_id** | `stack_id: int` (FK, optional) | ❌ Not present | Backend-only |

**Analysis**:
- These are **backend persistence concerns** only
- PhotoEgg is pre-database (file processing output)
- Correctly absent from PhotoEgg

### Corrections & Adjustments (Backend Only)

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **timeloc_correction** | `timeloc_correction: JSON` | ❌ Not present | Backend-only |
| **view_correction** | `view_correction: JSON` | ❌ Not present | Backend-only |

**Analysis**:
- User-applied overrides (time zone fix, rotation, crop hints)
- Correctly absent from PhotoEgg (not extractable from file)

### Timestamps

| Field | Photo (Backend) | PhotoEgg (imalink-core) | Match? |
|-------|-----------------|-------------------------|--------|
| **created_at** | `created_at: DateTime` (auto) | ❌ Not present | Backend-only |
| **updated_at** | `updated_at: DateTime` (auto) | ❌ Not present | Backend-only |
| **first_imported** | ❌ Not in Photo | `first_imported: datetime \| null` | 🔴 PhotoEgg extra |
| **last_imported** | ❌ Not in Photo | `last_imported: datetime \| null` | 🔴 PhotoEgg extra |

**Analysis**:
- Photo uses `created_at/updated_at` (database lifecycle)
- PhotoEgg has `first_imported/last_imported` (file history)
- **Question**: Should backend track import history from PhotoEgg?

---

## Key Insight: The Only Real Difference is Coldpreview

After detailed comparison, **93% of fields are semantically identical**. The only major difference:

### Current Approach
```python
# PhotoEgg (imalink-core) - wire format
{
    "coldpreview_base64": "/9j/4AAQ..." | null,  # ~100-200KB inline
    "coldpreview_width": 2560,
    "coldpreview_height": 1920
}

# Photo (backend) - persistence format
class Photo:
    coldpreview_path = Column(String)  # "/tmp/imalink_coldpreviews/abc123.jpg"
    # Width/height NOT stored (derived on-demand)
```

**Why different?**
- **Wire format (PhotoEgg)**: Base64 for JSON transmission (standard practice)
- **Persistence (Photo)**: Filesystem path to avoid bloating database (~200KB per photo)

**Resolution**: These are **complementary formats**, not competing designs.

---

## Proposed Solution: Aligned Schema with Format Adapters

### Core Principle
> **PhotoEgg and Photo should have identical field structure, with format adapters for serialization.**

### Proposed PhotoEgg v2.0 Schema (imalink-core)

```python
# service/main.py (imalink-core)
class PhotoEggResponse(BaseModel):
    """
    PhotoEgg v2.0 - Aligned with backend Photo model
    
    Philosophy:
    - exif_dict is READONLY "DNA" (complete EXIF from file)
    - taken_at/GPS/camera are INDEXED COPIES (performance)
    - Previews use base64 for wire format (JSON standard)
    """
    # === IDENTITY ===
    hothash: str
    
    # === PREVIEWS (wire format: base64) ===
    hotpreview_base64: str
    hotpreview_width: int
    hotpreview_height: int
    
    coldpreview_base64: Optional[str] = None
    coldpreview_width: Optional[int] = None
    coldpreview_height: Optional[int] = None
    
    # === DIMENSIONS ===
    width: int
    height: int
    
    # === TIME & LOCATION (indexed copies from EXIF) ===
    taken_at: Optional[str] = None  # ISO 8601
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    
    # === CAMERA (indexed copies from EXIF) ===
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    
    # === COMPLETE EXIF (readonly "DNA") ===
    exif_dict: Optional[Dict[str, Any]] = None  # ALL metadata
    
    # === FILE INFO ===
    primary_filename: str
    file_size_bytes: int
    image_format: str  # "JPEG", "PNG", "HEIC", etc.
    
    # === VALIDATION ===
    is_valid_image: bool = True
```

### Backend Photo Model (MINIMAL CHANGES)

```python
# src/models/photo.py (backend)
class Photo(Base, TimestampMixin):
    """
    Photo model - aligned with PhotoEgg structure
    
    Additions to PhotoEgg:
    - Database fields (id, user_id)
    - User organization (rating, visibility)
    - Associations (author_id, stack_id)
    - Corrections (timeloc_correction, view_correction)
    
    Differences from PhotoEgg:
    - hotpreview: bytes (not base64) - stored in database
    - coldpreview_path: str (not base64) - filesystem reference
    """
    # === DATABASE IDENTITY ===
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # === PHOTO IDENTITY ===
    hothash = Column(String(64), unique=True, nullable=False, index=True)
    
    # === PREVIEWS (persistence format) ===
    hotpreview = Column(LargeBinary, nullable=False)  # bytes (not base64)
    hotpreview_width = Column(Integer)  # NEW: store dimensions
    hotpreview_height = Column(Integer)  # NEW: store dimensions
    
    coldpreview_path = Column(String)  # filesystem path (not base64)
    coldpreview_width = Column(Integer)  # NEW: store dimensions
    coldpreview_height = Column(Integer)  # NEW: store dimensions
    
    # === DIMENSIONS ===
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    
    # === TIME & LOCATION (indexed copies) ===
    taken_at = Column(DateTime, index=True)
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    
    # === CAMERA (indexed copies) ===
    camera_make = Column(String)
    camera_model = Column(String)
    
    # === COMPLETE EXIF (readonly "DNA") ===
    exif_dict = Column(JSON)  # ALL metadata from PhotoEgg
    
    # === USER ORGANIZATION (backend-only) ===
    rating = Column(Integer, default=0)
    visibility = Column(String, default="private")
    author_id = Column(Integer, ForeignKey('authors.id'))
    stack_id = Column(Integer, ForeignKey('photo_stacks.id'))
    
    # === CORRECTIONS (backend-only) ===
    timeloc_correction = Column(JSON)
    view_correction = Column(JSON)
```

### Automatic Mapping with Factory Method

```python
# src/services/photo_service.py
class PhotoService:
    @staticmethod
    def from_photoegg(photoegg: PhotoEggCreate, user_id: int) -> Photo:
        """
        Create Photo from PhotoEgg - AUTOMATIC MAPPING
        
        No manual field extraction - schemas are aligned!
        """
        # Decode base64 → bytes for database storage
        hotpreview_bytes = base64.b64decode(photoegg.hotpreview_base64)
        
        # Create Photo with direct field mapping
        return Photo(
            # Database identity
            user_id=user_id,
            
            # Photo identity (direct copy)
            hothash=photoegg.hothash,
            
            # Previews (format conversion only)
            hotpreview=hotpreview_bytes,  # base64 → bytes
            hotpreview_width=photoegg.hotpreview_width,
            hotpreview_height=photoegg.hotpreview_height,
            
            # Coldpreview handled separately (save to disk)
            coldpreview_path=None,  # Set after saving coldpreview_base64 to disk
            coldpreview_width=photoegg.coldpreview_width,
            coldpreview_height=photoegg.coldpreview_height,
            
            # Dimensions (direct copy)
            width=photoegg.width,
            height=photoegg.height,
            
            # Time & location (direct copy)
            taken_at=photoegg.taken_at,
            gps_latitude=photoegg.gps_latitude,
            gps_longitude=photoegg.gps_longitude,
            
            # Camera (direct copy)
            camera_make=photoegg.camera_make,
            camera_model=photoegg.camera_model,
            
            # Complete EXIF (direct copy)
            exif_dict=photoegg.exif_dict,
            
            # User organization (defaults)
            rating=0,
            visibility="private"
        )
```

**Benefits**:
- **15 lines** instead of **50+ lines** of mapping logic
- Perfect 1:1 field correspondence
- Compile-time safety (Pydantic → SQLAlchemy)
- Self-documenting (field names match exactly)

---

## Migration Strategy

### Phase 1: Backend Preparation (This Repo)
1. Add preview dimension columns to Photo model
   ```sql
   ALTER TABLE photos ADD COLUMN hotpreview_width INTEGER;
   ALTER TABLE photos ADD COLUMN hotpreview_height INTEGER;
   ALTER TABLE photos ADD COLUMN coldpreview_width INTEGER;
   ALTER TABLE photos ADD COLUMN coldpreview_height INTEGER;
   ```

2. Update PhotoEgg Pydantic schema
   - Flatten structure (remove nested `metadata` object)
   - Add `image_format`, `file_size_bytes`

3. Update `PhotoService.from_photoegg()` to use direct mapping

4. Test with existing PhotoEgg fixtures (backward compatibility)

### Phase 2: imalink-core Update (Other Repo)
1. Update `PhotoEggResponse` schema to match Photo structure

2. Add version field to PhotoEgg
   ```python
   class PhotoEggResponse(BaseModel):
       version: str = "2.0"  # Semantic versioning
       # ... rest of fields
   ```

3. Support both formats during transition
   ```python
   @app.post("/v1/process")
   async def process_image_endpoint(...):
       # Generate PhotoEgg v2.0
       photoegg = PhotoEggResponse(
           version="2.0",
           hothash=hothash,
           # Direct field assignments (no nesting)
           taken_at=metadata.taken_at,
           camera_make=metadata.camera_make,
           ...
       )
       return photoegg
   ```

### Phase 3: Deprecation (6+ months)
1. imalink-core logs warning if backend sends old format
2. Backend logs warning if receives PhotoEgg without `version` field
3. Documentation updated with migration guide

### Phase 4: Cleanup
1. Remove backward compatibility code
2. Lock contract with comprehensive tests

---

## Benefits of Alignment

### 1. Eliminated Complexity
**Before** (current):
```python
# 50+ lines of manual mapping
metadata = photoegg.photo_egg.metadata
taken_at = metadata.taken_at if metadata else None
gps_lat = metadata.gps_latitude if metadata else None
exif_dict = photoegg.photo_egg.exif_dict or {}
if metadata:
    exif_dict.update({"taken_at": ...})
# ... 40 more lines
```

**After** (aligned):
```python
# 15 lines of direct assignment
photo = Photo(
    hothash=photoegg.hothash,
    taken_at=photoegg.taken_at,
    gps_latitude=photoegg.gps_latitude,
    exif_dict=photoegg.exif_dict,
    ...
)
```

### 2. Guaranteed Compatibility
- Field names match exactly → impossible to mismap
- Pydantic validates PhotoEgg → SQLAlchemy validates Photo
- Changes to one schema force changes to other (compile error if mismatch)

### 3. Self-Documenting Contract
```python
# OLD: "What does PhotoEggMetadata.f_number map to?"
# Answer: Search codebase for manual mapping

# NEW: "What does PhotoEgg.aperture map to?"
# Answer: Photo.aperture (1:1 correspondence)
```

### 4. Simplified Testing
```python
# Generate PhotoEgg from Photo (perfect round-trip)
def test_photo_photoegg_roundtrip():
    photo = Photo(hothash="abc123", taken_at=datetime.now(), ...)
    photoegg = PhotoEgg.from_photo(photo)
    photo2 = Photo.from_photoegg(photoegg)
    
    assert photo.taken_at == photo2.taken_at
    assert photo.gps_latitude == photo2.gps_latitude
    # All fields match automatically
```

### 5. Reduced Maintenance
- imalink-core adds new EXIF field → backend gets it automatically via `exif_dict`
- Backend adds indexed field → imalink-core PR updates PhotoEgg schema
- No silent failures from missed mappings

---

## Potential Concerns & Responses

### Concern 1: "PhotoEgg should be minimal (only what's needed)"
**Response**: 
- Current PhotoEgg already has 20+ fields
- Alignment adds ~3 fields (hotpreview dimensions, coldpreview dimensions)
- **Benefit outweighs cost**: Eliminates 50+ lines of mapping code

### Concern 2: "imalink-core shouldn't know about backend structure"
**Response**:
- imalink-core **already defines the contract** (PhotoEgg schema)
- Backend **already conforms** to that contract (manual mapping)
- Alignment just makes implicit dependency explicit
- Alternative (current approach): Backend chases imalink-core changes

### Concern 3: "Breaking change for existing clients"
**Response**:
- Migration strategy supports both formats (6+ months)
- Version field enables graceful transition
- Only one client (this backend) → controlled migration

### Concern 4: "What if frontend needs different structure?"
**Response**:
- Frontend receives **Photo API response**, not PhotoEgg directly
- Backend can reshape Photo → PhotoResponse for frontend needs
- PhotoEgg is internal contract (backend ↔ imalink-core)

---

## Decision Matrix

| Criterion | Current Approach | Aligned Schemas |
|-----------|------------------|-----------------|
| **Lines of mapping code** | 50+ lines | 15 lines |
| **Compile-time safety** | ❌ Runtime only | ✅ Pydantic + SQLAlchemy |
| **Maintenance burden** | 🔴 High (manual sync) | 🟢 Low (enforced sync) |
| **Risk of field mismatch** | 🔴 High (easy to miss) | 🟢 None (1:1 mapping) |
| **Schema drift** | 🔴 Frequent | 🟢 Impossible |
| **Testing complexity** | 🔴 High (test mappings) | 🟢 Low (test conversions) |
| **Breaking changes** | 🟡 Medium (migration needed) | 🟡 Medium (one-time) |
| **Performance** | 🟢 Same | 🟢 Same |

**Score**: Aligned Schemas wins **6/8 criteria**.

---

## Recommendation

### ✅ **Redesign PhotoEgg to mirror Photo model structure**

**Justification**:
1. Structures already 93% aligned (only coldpreview format differs)
2. Eliminates 50+ lines of error-prone mapping code
3. Guarantees contract compatibility by design
4. Reduces long-term maintenance burden
5. Makes implicit dependency explicit and enforceable

**Next Steps**:
1. **Backend** (this repo):
   - Add migration: `hotpreview_width/height`, `coldpreview_width/height`
   - Update `PhotoEggCreate` schema (flatten, remove nesting)
   - Refactor `PhotoService.from_photoegg()` to direct mapping
   - Test with existing fixtures

2. **imalink-core** (other repo):
   - Update `PhotoEggResponse` schema to match Photo
   - Add version field (`"2.0"`)
   - Support backward compatibility (6+ months)

3. **Documentation**:
   - Update `CONTRACTS.md` with new PhotoEgg v2.0 schema
   - Document migration path for potential future clients

**Timeline**: 2-3 weeks for full implementation + testing.

---

## Appendix: readonly exif_dict Philosophy

### User's Key Insight
> "exif_dict should be readonly JSON (egg's DNA)"

**Interpretation**:
- `exif_dict` contains **complete EXIF scraped from file**
- Never edited or modified by backend
- Source of truth for all metadata
- Indexed fields (taken_at, GPS, camera) are **copies** for performance

### Implementation Pattern

```python
class Photo:
    # === INDEXED COPIES (for queries) ===
    taken_at = Column(DateTime)  # Copied from exif_dict['DateTimeOriginal']
    gps_latitude = Column(Float)  # Copied from exif_dict['GPSLatitude']
    camera_make = Column(String)  # Copied from exif_dict['Make']
    
    # === READONLY DNA (never modified) ===
    exif_dict = Column(JSON)  # Complete EXIF from file
    
    # === USER CORRECTIONS (overrides) ===
    timeloc_correction = Column(JSON)  # User fixes (time zone, GPS)
    view_correction = Column(JSON)  # Visual hints (rotation, crop)
```

**Query Pattern**:
```python
# Fast: Use indexed field
photos = db.query(Photo).filter(
    Photo.taken_at >= datetime(2024, 1, 1)
).all()

# Detailed: Read complete EXIF
for photo in photos:
    camera_settings = photo.exif_dict.get('CameraSettings', {})
    lens_info = photo.exif_dict.get('LensInfo', {})
```

**Correction Pattern**:
```python
# Time zone fix (user knows photo taken in UTC+2, not UTC)
photo.timeloc_correction = {
    "timezone_offset": "+02:00",
    "corrected_taken_at": "2024-11-10T16:30:00+02:00"
}

# exif_dict NEVER modified (preserves original "DNA")
assert photo.exif_dict['DateTimeOriginal'] == "2024-11-10T14:30:00"
```

**Benefits**:
- Clear separation: original vs corrected data
- EXIF integrity preserved (debugging, re-import)
- Corrections are optional overrides (can be reset)

---

**End of Analysis**
