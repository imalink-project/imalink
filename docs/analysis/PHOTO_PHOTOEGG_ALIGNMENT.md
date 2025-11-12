# Analyse: Photo Model vs PhotoEgg Structure

## Dagens situasjon

### PhotoEgg (fra imalink-core)
**Kilde**: imalink-core prosesserer bilde → returnerer PhotoEgg JSON  
**Ansvar**: Inneholder RAW data fra bildeprosessering  
**Levetid**: Flyktig - kun under import/opprettelse  

```python
PhotoEgg {
    # Identitet
    hothash: str                    # SHA256 av hotpreview
    primary_filename: str
    
    # Previews (base64 JPEG)
    hotpreview_base64: str          # 150x150px thumbnail
    coldpreview_base64: str?        # Valgfri større preview
    hotpreview_width: int
    hotpreview_height: int
    coldpreview_width: int?
    coldpreview_height: int?
    
    # Dimensjoner
    width: int                      # Original bilde-dimensjoner
    height: int
    
    # EXIF metadata (flat struktur)
    taken_at: datetime?
    camera_make: str?
    camera_model: str?
    lens_model: str?
    focal_length: float?
    iso: int?
    aperture: float?
    shutter_speed: str?
    gps_latitude: float?
    gps_longitude: float?
    has_gps: bool
    
    # Utvidet (v2.0+)
    image_format: str               # JPEG, PNG, HEIC
    file_size_bytes: int
    exif_dict: dict?                # Komplett EXIF (valgfri)
}
```

### Photo Model (backend database)
**Kilde**: Opprettes FRA PhotoEgg + bruker-input  
**Ansvar**: Persistent lagring, brukermetadata, gallerivisning  
**Levetid**: Permanent (til bruker sletter)  

```python
Photo {
    # Technical PKs
    id: int                         # Auto-increment (intern)
    hothash: str                    # Fra PhotoEgg (API-identitet)
    user_id: int                    # Eierskap
    
    # Visual data (fra PhotoEgg)
    hotpreview: bytes               # Dekodet fra base64
    width: int
    height: int
    exif_dict: json                 # KOMPLETT EXIF lagret
    
    # EXIF (ekstrahert til kolonner for queries)
    taken_at: datetime?
    gps_latitude: float?
    gps_longitude: float?
    
    # Brukermetadata (IKKE i PhotoEgg)
    rating: int                     # 0-5 stjerner
    visibility: str                 # private/space/authenticated/public
    author_id: int?
    stack_id: int?
    import_session_id: int?
    
    # Coldpreview (lagres på disk)
    coldpreview_path: str?
    
    # Korreksjoner (IKKE i PhotoEgg)
    timeloc_correction: json?       # Overstyr tid/GPS
    view_correction: json?          # Rotasjon/cropping
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
}
```

---

## Nøkkelforskjeller

| Aspekt | PhotoEgg | Photo Model |
|--------|----------|-------------|
| **Format** | Pydantic schema (validering) | SQLAlchemy model (persistence) |
| **Preview** | Base64 string | Binary bytes + path |
| **EXIF** | Flat felter (limited) | Duplisert: både flat + full exif_dict |
| **Metadata** | Kun EXIF fra bilde | EXIF + brukerdata (rating, tags) |
| **Eierskap** | Nei | Ja (user_id) |
| **Coldpreview** | Base64 (optional) | Filsti (optional) |
| **Validering** | Pydantic automatisk | Ingen (mangler) |

---

## Problem 1: EXIF-duplikasjon

**Dagens situasjon**:
```python
# PhotoEgg har flat struktur
photoegg.taken_at
photoegg.camera_make
photoegg.gps_latitude
photoegg.exif_dict  # PLUS fullstendig dict

# Photo dupliserer dette
photo.taken_at        # ← Fra PhotoEgg
photo.gps_latitude    # ← Fra PhotoEgg  
photo.exif_dict       # ← Fra PhotoEgg (hele pakka)
```

**Issue**: Vi lagrer samme data to ganger - både som kolonner og i JSON.

---

## Problem 2: Mapping PhotoEgg → Photo er manuell

**Dagens kode** (i `photo_service.py`):
```python
def create_photo_from_photoegg(photoegg, user_id):
    # Manuell mapping - lett å glemme felter
    photo = Photo(
        hothash=photoegg.hothash,
        user_id=user_id,
        hotpreview=base64.b64decode(photoegg.hotpreview_base64),
        width=photoegg.width,
        height=photoegg.height,
        taken_at=photoegg.taken_at,      # ← Manuell
        gps_latitude=photoegg.gps_latitude,  # ← Manuell
        gps_longitude=photoegg.gps_longitude, # ← Manuell
        exif_dict={...},  # ← Bygge opp fra scratch
    )
```

**Issue**: 
- Lett å glemme felter
- Ingen automatisk sync ved schema-endringer
- Må vedlikeholdes to steder

---

## Problem 3: PhotoEgg mangler validering mot Photo

Når PhotoEgg schema endres i imalink-core, har vi ingen garanti for at Photo-modellen kan lagre dataen.

---

## Muligheter for tettere kobling

### 🔧 Løsning 1: PhotoEgg.to_photo() factory method

```python
class PhotoEggCreate(BaseModel):
    """PhotoEgg from imalink-core"""
    hothash: str
    hotpreview_base64: str
    width: int
    height: int
    taken_at: Optional[datetime] = None
    # ... alle felt
    
    def to_photo(self, user_id: int, **overrides) -> Photo:
        """
        Convert PhotoEgg to Photo model instance.
        
        Args:
            user_id: Owner of the photo
            **overrides: Override default values (rating, visibility, etc)
            
        Returns:
            Unsaved Photo instance ready for db.add()
        """
        # Dekode previews
        hotpreview_bytes = base64.b64decode(self.hotpreview_base64)
        
        # Bygg EXIF dict
        exif_dict = self._build_exif_dict()
        
        # Opprett Photo
        photo = Photo(
            hothash=self.hothash,
            user_id=user_id,
            hotpreview=hotpreview_bytes,
            width=self.width,
            height=self.height,
            taken_at=self.taken_at,
            gps_latitude=self.gps_latitude,
            gps_longitude=self.gps_longitude,
            exif_dict=exif_dict,
            # Defaults (kan overstyres)
            rating=overrides.get('rating', 0),
            visibility=overrides.get('visibility', 'private'),
            author_id=overrides.get('author_id'),
        )
        
        # Håndter coldpreview hvis present
        if self.coldpreview_base64:
            # Lagre til disk og sett path
            coldpreview_path = self._save_coldpreview(self.hothash)
            photo.coldpreview_path = coldpreview_path
        
        return photo
    
    def _build_exif_dict(self) -> dict:
        """Build complete EXIF dict from PhotoEgg fields"""
        exif = {}
        
        # Timestamp
        if self.taken_at:
            exif["taken_at"] = self.taken_at.isoformat()
        
        # Camera
        if self.camera_make:
            exif["camera_make"] = self.camera_make
        if self.camera_model:
            exif["camera_model"] = self.camera_model
        
        # Lens
        if self.lens_model:
            exif["lens_model"] = self.lens_model
            
        # Settings
        if self.iso:
            exif["iso"] = self.iso
        if self.aperture:
            exif["aperture"] = self.aperture
        if self.shutter_speed:
            exif["shutter_speed"] = self.shutter_speed
        if self.focal_length:
            exif["focal_length"] = self.focal_length
        
        # GPS
        if self.gps_latitude:
            exif["gps_latitude"] = self.gps_latitude
        if self.gps_longitude:
            exif["gps_longitude"] = self.gps_longitude
        
        # Merge with full exif_dict if present
        if self.exif_dict:
            exif.update(self.exif_dict)
        
        return exif
```

**Bruk**:
```python
# I photo_service.py
def create_photo_from_photoegg(self, photoegg: PhotoEggCreate, user_id: int):
    # EN linje mapping!
    photo = photoegg.to_photo(
        user_id=user_id,
        rating=request.rating,      # Fra bruker-input
        visibility=request.visibility
    )
    
    self.db.add(photo)
    self.db.commit()
    return photo
```

**Fordeler**:
✅ Automatisk mapping - ingen manuell kode  
✅ Sentralisert logikk - én kilde til sannhet  
✅ Enkel å vedlikeholde  
✅ Type-safe (Pydantic + SQLAlchemy)  

---

### 🔧 Løsning 2: Shared EXIF mixin

```python
# I src/schemas/shared.py
class ExifFieldsMixin:
    """Shared EXIF field definitions for PhotoEgg and Photo"""
    
    taken_at: Optional[datetime] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    focal_length: Optional[float] = None
    iso: Optional[int] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None


# PhotoEgg bruker mixin
class PhotoEggCreate(BaseModel, ExifFieldsMixin):
    hothash: str
    hotpreview_base64: str
    width: int
    height: int
    # EXIF fields inherited from mixin


# Photo model bruker samme struktur (via annotation)
class Photo(Base):
    # ... existing fields ...
    
    # EXIF fields (samme som PhotoEgg via mixin)
    taken_at = Column(DateTime, nullable=True)
    camera_make = Column(String(100), nullable=True)
    # ...
```

**Fordeler**:
✅ DRY - ingen duplisering av felt-definisjoner  
✅ Type-kompatibilitet garantert  
✅ Endringer ett sted påvirker begge  

---

### 🔧 Løsning 3: Remove EXIF column duplication

**Radikal løsning**: Fjern alle flat EXIF-kolonner fra Photo, bruk KUN `exif_dict`.

```python
class Photo(Base):
    id: int
    hothash: str
    user_id: int
    hotpreview: bytes
    width: int
    height: int
    
    # ONLY JSON - no flat columns
    exif_dict: json  # ← Alt EXIF data her
    
    # User metadata
    rating: int
    visibility: str
    # ...
    
    # Queries via JSON extraction
    @property
    def taken_at(self):
        return self.exif_dict.get("taken_at")
    
    @property  
    def gps_latitude(self):
        return self.exif_dict.get("gps_latitude")
```

**Indexes med JSON**:
```sql
-- PostgreSQL JSON indexing
CREATE INDEX idx_photos_taken_at 
ON photos ((exif_dict->>'taken_at'));

CREATE INDEX idx_photos_gps_lat 
ON photos ((CAST(exif_dict->>'gps_latitude' AS FLOAT)));
```

**Fordeler**:
✅ Ingen duplikasjon  
✅ Enkel mapping fra PhotoEgg  
✅ Fleksibel - kan lagre ALT EXIF uten schema-endring  

**Ulemper**:
❌ Tregere queries (JSON extraction)  
❌ SQLite har begrenset JSON-støtte  
❌ Komplisert indexing  

---

## Anbefaling: Hybrid tilnærming

**Kombiner Løsning 1 + 2**:

1. **Shared EXIF mixin** → Garanterer kompatibilitet
2. **PhotoEgg.to_photo()** → Automatisk mapping
3. **Behold viktige kolonner** → taken_at, gps_* for queries
4. **Bruk exif_dict** → For alt annet EXIF

```python
# Definer viktige query-felt
INDEXED_EXIF_FIELDS = {
    'taken_at': DateTime,
    'gps_latitude': Float,
    'gps_longitude': Float,
}

# Resten i JSON
OTHER_EXIF_FIELDS = [
    'camera_make', 'camera_model', 'lens_model',
    'iso', 'aperture', 'shutter_speed', 'focal_length'
]
```

**Photo model**:
```python
class Photo(Base):
    # ... identity fields ...
    
    # Indexed EXIF (for queries)
    taken_at = Column(DateTime, index=True)
    gps_latitude = Column(Float, index=True)
    gps_longitude = Column(Float, index=True)
    
    # Complete EXIF in JSON (all fields)
    exif_dict = Column(JSON)
    
    # Properties for non-indexed fields
    @property
    def camera_make(self):
        return self.exif_dict.get("camera_make")
```

---

## Implementeringsplan

### Fase 1: Add factory method
1. Legg til `PhotoEggCreate.to_photo()` i schemas
2. Refaktorer `photo_service.create_photo_from_photoegg()`
3. Test med eksisterende PhotoEgg fixtures

### Fase 2: Validate mapping
1. Lag test som sjekker ALL PhotoEgg-felter mappes
2. Automatisk validering ved schema-endring

### Fase 3: Consider denormalization (optional)
1. Vurder fjerne redundante kolonner
2. Benchmark JSON vs kolonne-queries
3. Migrer hvis performance OK

---

## Konklusjon

**Hovedproblemet**: PhotoEgg og Photo er for løst koblet - manuell mapping, duplikasjon, ingen garantier.

**Beste løsning**: 
- `PhotoEggCreate.to_photo()` factory method
- Shared EXIF type definitions
- Keep indexed columns for queries, rest in JSON

**Gevinst**:
- ✅ Automatisk sync ved schema-endringer
- ✅ Mindre kode å vedlikeholde  
- ✅ Type-safety gjennom hele stacken
- ✅ Enklere testing (PhotoEgg → Photo er deterministisk)
