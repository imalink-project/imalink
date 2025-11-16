# Photo Payload Redesign - November 2025

## Bakgrunn

Dette dokumentet beskriver foreslåtte endringer for å tydeliggjøre terminologi og struktur mellom imalink-core (image processing) og imalink-backend (metadata management).

**Nåværende status:** PhotoEgg er et bra konsept, men navnet er uklart og "master" vs "primary" er inkonsistent.

**Mål:** Rydde opp i terminologi og gjøre arkitekturen tydeligere.

---

## Terminologiendringer

### 1. PhotoEgg → PhotoPayload

**Før:**
```python
class PhotoEgg(BaseModel):
    hothash: str
    hotpreview_base64: str
    exif_dict: dict
```

**Etter:**
```python
class PhotoPayload(BaseModel):
    """
    Photo processing result from imalink-core.
    Transport/transfer format - NOT stored in database.
    Contains all data needed to create a Photo in backend.
    """
    hothash: str
    hotpreview_base64: str
    primary_filename: str  # NEW - which file is source of hotpreview/exif
    width: int
    height: int
    metadata: PhotoMetadata
    exif_dict: dict
```

**Årsak:** "Payload" er mer tydelig enn "Egg" - det er data som overføres, ikke en entitet.

---

### 2. master → primary (konsistent bruk)

**Problem:** Photo model bruker "master" i kommentarer, men har `primary_filename` property.

**Løsning:** Bruk **primary** konsekvent overalt.

**Endringer:**
- ✅ `primary_filename` (database kolonne, ikke property)
- ✅ `primary_file` (property som returnerer ImageFile)
- ❌ Fjern all bruk av "master"

---

## Photo Model Endringer

### Legg til primary_filename kolonne

**Før (linje 160-166):**
```python
@property
def primary_filename(self) -> str:
    """Get the primary filename (prefer JPEG over RAW for display)"""
    jpeg = self.jpeg_file
    if jpeg:
        return getattr(jpeg, 'filename', 'Unknown')
    if self.image_files:
        return getattr(self.image_files[0], 'filename', 'Unknown')
    return "Unknown"
```

**Etter (linje ca. 65, etter hothash):**
```python
# Primary file reference - which ImageFile is source of hotpreview/exif
primary_filename = Column(String(255), nullable=False)
```

**Ny property (erstatter gammel primary_filename property):**
```python
@property
def primary_file(self) -> Optional["ImageFile"]:
    """Get the primary ImageFile (source of hotpreview/exif)"""
    if not self.image_files:
        return None
    for file in self.image_files:
        if file.filename == self.primary_filename:
            return file
    # Fallback to first file if primary_filename not found
    return self.image_files[0] if self.image_files else None
```

---

## PhotoPayload Schema Endringer

### Fil: `src/schemas/photoegg_schemas.py`

**Før:**
```python
class PhotoEgg(BaseModel):
    hothash: str
    hotpreview_base64: str
    coldpreview_base64: Optional[str] = None
    width: int
    height: int
    metadata: PhotoEggMetadata
    exif_dict: dict

class PhotoEggRequest(BaseModel):
    photo_egg: PhotoEgg
    rating: int = 0
    visibility: str = "private"
    author_id: Optional[int] = None
    import_session_id: Optional[int] = None
```

**Etter (rename fil til `photo_payload_schemas.py`):**
```python
class PhotoPayload(BaseModel):
    """Photo processing result from imalink-core"""
    hothash: str
    hotpreview_base64: str
    coldpreview_base64: Optional[str] = None
    width: int
    height: int
    
    # NEW - Which file is primary (source of hotpreview/exif)
    primary_filename: str  # e.g., "IMG_1234.jpg"
    
    metadata: PhotoMetadata  # Renamed from PhotoEggMetadata
    exif_dict: dict

class PhotoPayloadRequest(BaseModel):
    """Request to create Photo from PhotoPayload"""
    photo_payload: PhotoPayload  # Renamed from photo_egg
    rating: int = 0
    visibility: str = "private"
    author_id: Optional[int] = None
    import_session_id: Optional[int] = None
```

---

## API Endpoint Endringer

### Fil: `src/api/v1/photos.py`

**INGEN endring i endpoint URL** - `/photoegg` beholdes for backward compatibility.

**Før (linje 450):**
```python
@router.post("/photoegg", response_model=PhotoEggResponse, status_code=201)
async def create_photo_from_photoegg(
    request: PhotoEggRequest,
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Create Photo from PhotoEgg (New Architecture)
    
    PhotoEgg is the complete JSON package from imalink-core server containing
    all image processing results. Frontend sends image to imalink-core server,
    receives PhotoEgg, then posts it here.
    """
    ...
```

**Etter:**
```python
@router.post("/photoegg", response_model=PhotoPayloadResponse, status_code=201)
async def create_photo_from_payload(
    request: PhotoPayloadRequest,  # Renamed type
    current_user: User = Depends(get_current_active_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Create Photo from PhotoPayload (imalink-core processing result)
    
    PhotoPayload is the complete JSON package from imalink-core server containing
    all image processing results. Desktop app sends images to imalink-core (local),
    receives PhotoPayload, then posts it here to create Photo + ImageFiles.
    """
    payload = request.photo_payload
    
    photo = photo_service.create_photo_from_payload(
        payload,
        user_id=current_user.id,
        rating=request.rating,
        visibility=request.visibility,
        author_id=request.author_id,
        import_session_id=request.import_session_id
    )
    
    return photo
```

---

## Service Layer Endringer

### Fil: `src/services/photo_service.py`

**Før (linje 609):**
```python
def create_photo_from_photoegg(self, photoegg_request, user_id: int) -> Photo:
    egg = photoegg_request.photo_egg
    
    photo = Photo(
        hothash=egg.hothash,
        hotpreview=base64.b64decode(egg.hotpreview_base64),
        exif_dict=exif_dict,
        width=egg.width,
        height=egg.height,
        ...
    )
```

**Etter:**
```python
def create_photo_from_payload(self, payload_request, user_id: int) -> Photo:
    """Create Photo from PhotoPayload (imalink-core processing result)"""
    payload = payload_request.photo_payload
    
    photo = Photo(
        hothash=payload.hothash,
        primary_filename=payload.primary_filename,  # NEW
        hotpreview=base64.b64decode(payload.hotpreview_base64),
        exif_dict=payload.exif_dict,
        width=payload.width,
        height=payload.height,
        taken_at=parse(payload.metadata.taken_at) if payload.metadata.taken_at else None,
        gps_latitude=payload.metadata.gps_latitude,
        gps_longitude=payload.metadata.gps_longitude,
        ...
    )
    
    return photo
```

---

## Database Migration

### Ny migrasjon: `add_primary_filename_to_photos`

```python
"""add primary_filename to photos

Revision ID: xxxx
Revises: fa8291463a7e
Create Date: 2025-11-16
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add column (nullable first for existing data)
    op.add_column('photos', 
        sa.Column('primary_filename', sa.String(255), nullable=True)
    )
    
    # Backfill: Set primary_filename from first ImageFile
    connection = op.get_bind()
    photos = connection.execute(sa.text("SELECT id FROM photos"))
    
    for photo in photos:
        # Get first ImageFile for this photo
        first_file = connection.execute(sa.text(
            "SELECT filename FROM image_files "
            "WHERE photo_id = :photo_id "
            "ORDER BY id LIMIT 1"
        ), {"photo_id": photo.id}).first()
        
        if first_file:
            connection.execute(sa.text(
                "UPDATE photos SET primary_filename = :filename "
                "WHERE id = :photo_id"
            ), {"filename": first_file.filename, "photo_id": photo.id})
    
    # Make NOT NULL after backfill
    op.alter_column('photos', 'primary_filename', nullable=False)


def downgrade():
    op.drop_column('photos', 'primary_filename')
```

---

## Oppdateringer i imalink-core (eksternt repo)

imalink-core må oppdateres til å inkludere `primary_filename` i PhotoPayload response:

```json
{
  "hothash": "abc123...",
  "hotpreview_base64": "...",
  "primary_filename": "IMG_1234.jpg",
  "width": 4000,
  "height": 3000,
  "metadata": {
    "taken_at": "2025-11-16T10:30:00Z",
    "camera_make": "Canon",
    ...
  },
  "exif_dict": { ... }
}
```

**Regel:** Første fil som prosesseres er primary file.

---

## Oppsummering av endringer

### Photo Model (`src/models/photo.py`)
- ✅ Legg til kolonne: `primary_filename = Column(String(255), nullable=False)`
- ✅ Fjern property: `@property def primary_filename(self)`
- ✅ Legg til property: `@property def primary_file(self)` (returnerer ImageFile)
- ✅ Oppdater kommentarer: "master" → "primary"

### PhotoPayload Schema (`src/schemas/photo_payload_schemas.py`)
- ✅ Rename fil: `photoegg_schemas.py` → `photo_payload_schemas.py`
- ✅ Rename class: `PhotoEgg` → `PhotoPayload`
- ✅ Rename class: `PhotoEggRequest` → `PhotoPayloadRequest`
- ✅ Rename class: `PhotoEggMetadata` → `PhotoMetadata`
- ✅ Legg til felt: `primary_filename: str`
- ✅ Rename felt: `photo_egg` → `photo_payload`

### API Endpoints (`src/api/v1/photos.py`)
- ✅ Rename function: `create_photo_from_photoegg` → `create_photo_from_payload`
- ✅ Oppdater types: `PhotoEggRequest` → `PhotoPayloadRequest`
- ✅ Oppdater docstring: PhotoEgg → PhotoPayload
- ⚠️ **URL beholdes:** `/photoegg` (backward compatibility)

### Service Layer (`src/services/photo_service.py`)
- ✅ Rename method: `create_photo_from_photoegg` → `create_photo_from_payload`
- ✅ Legg til: `primary_filename=payload.primary_filename`

### Migration
- ✅ Ny migration: `add_primary_filename_to_photos`
- ✅ Backfill fra første ImageFile

### External (imalink-core)
- ⚠️ Må oppdateres: Inkluder `primary_filename` i PhotoPayload response

---

## Implementeringsrekkefølge

1. **Photo model** - Legg til `primary_filename` kolonne, oppdater properties
2. **Migration** - Generer og test lokalt
3. **Schema** - Rename PhotoEgg → PhotoPayload, legg til `primary_filename`
4. **Service** - Oppdater `create_photo_from_payload`
5. **API** - Oppdater endpoint (funksjonsnavn, ikke URL)
6. **Tests** - Oppdater alle referanser til PhotoEgg
7. **imalink-core** - Oppdater til å sende `primary_filename`
8. **Deploy** - Backend først, så desktop med oppdatert core

---

## Backward Compatibility

### URL endpoints - INGEN endring
```
POST /api/v1/photos/photoegg  ✅ Beholdes
POST /api/v1/photos/register-image  ✅ Uendret
```

### PhotoPayload - Bakoverkompatibel
- `primary_filename` er nytt felt
- Desktop/core må oppdateres samtidig
- Backend kan defaulte til første ImageFile hvis feltet mangler (overgangsfase)

---

## Testing Checklist

- [ ] Photo.primary_filename kolonne lagt til
- [ ] Migration backfiller primary_filename fra første ImageFile
- [ ] Photo.primary_file property returnerer riktig ImageFile
- [ ] PhotoPayload schema validerer primary_filename
- [ ] create_photo_from_payload setter primary_filename
- [ ] Alle tester oppdatert (PhotoEgg → PhotoPayload)
- [ ] API endpoint fungerer med nye types
- [ ] imalink-core sender primary_filename i response

---

## Spørsmål å avklare

1. ✅ **PhotoEgg → PhotoPayload** - Godkjent navn?
2. ✅ **primary_filename** - OK som kolonnenavn?
3. ✅ **primary_file** - OK som property-navn?
4. ⚠️ **Skal vi beholde `/photoegg` URL** eller rename til `/import` eller `/payload`?
5. ⚠️ **ImageFile endringer** - Trenger vi `is_raw`, `file_format` kolonner? (Foreløpig NEI - kan utledes fra filename)

---

## Notater

- Photo model har allerede bra struktur - endringene er minimale
- ImageFile har allerede `local_storage_info` og `cloud_storage_info` - ingen endringer nødvendig
- PhotoPayload er transportformat - lagres IKKE i database
- primary_filename er eneste nye database-kolonne

---

**Dokumentert:** 16. november 2025  
**Status:** Forslag, venter på godkjenning  
**Neste steg:** Review etter ferie, deretter implementering
