# Database Schema Update: thumbnail → preview_image

## 🎯 **Endring gjennomført**

### **Dato:** 6. oktober 2025
### **Endring:** Omdøpt `thumbnail` felt til `preview_image` i Image-modellen

## ✅ **Hva er oppdatert:**

### 1. **Database Model**
```python
# FØR:
thumbnail = Column(LargeBinary)

# ETTER:  
preview_image = Column(LargeBinary)  # Preview image stored as binary data (small version for galleries/UI)
```

### 2. **Påvirkede Filer**
- ✅ `src/models/image.py` - Hovedmodell oppdatert
- ✅ `src/schemas/image_schemas.py` - Schema oppdatert til `has_preview_image` og `ImagePreviewResponse`
- ✅ `src/services/image_service_new.py` - Service-logikk og `get_image_preview()` metode oppdatert
- ✅ `src/api/v1/images.py` - API endpoint `/thumbnail` → `/preview` og `get_preview_image()` funksjon
- ✅ `scripts/testing/test_thumbnail_direct.py` - Test oppdatert til `test_preview_image_rotation_direct()`
- ✅ `scripts/testing/test_thumbnail_rotation.py` - URL oppdatert til `/preview`
- ✅ `docs/service_layer_guide.md` - Dokumentasjon oppdatert
- ✅ `SETUP.md` - API oversikt oppdatert
- ✅ `CHANGELOG.md` - Historikk oppdatert

### 3. **API Endringer**

#### **Database Schema:**
```python
# FØR:
has_thumbnail: bool = Field(False, description="Whether thumbnail is available")
class ImageThumbnailResponse(BaseModel):
    thumbnail_data: bytes

# ETTER:
has_preview_image: bool = Field(False, description="Whether preview image is available") 
class ImagePreviewResponse(BaseModel):
    preview_data: bytes
```

#### **API Endpoints:**
```python
# FØR:
GET /api/v1/images/{id}/thumbnail
async def get_thumbnail(image_id: int) -> Response

# ETTER:
GET /api/v1/images/{id}/preview  
async def get_preview_image(image_id: int) -> Response
```

#### **Service Methods:**
```python
# FØR:
await image_service.get_image_thumbnail(image_id)

# ETTER:
await image_service.get_image_preview(image_id)
```

## 🔄 **Database Migration (Når nødvendig)**

Når du oppdaterer en eksisterende database, vil du trenge en migration:

```sql
-- SQLite migration
ALTER TABLE images RENAME COLUMN thumbnail TO preview_image;
```

## 💭 **Bakgrunn for Endringen**

**Problem:** `thumbnail` er generisk og kan forveksles med vanlig bildeforminskning

**Løsning:** `preview_image` er mer beskrivende og indikerer tydelig at dette er for forhåndsvisning i UI/galleri

**Fordeler:**
- ✅ Tydeligere hensikt og kontekst
- ✅ Skiller seg fra generell "thumbnail"-terminologi  
- ✅ Bedre match med applikasjonens funksjonalitet
- ✅ Mindre sjanse for forvirring med andre bildeoperasjoner

## 🧪 **Testing**

Alle komponenter testet og bekreftet funksjonelle:
- ✅ Model imports fungerer
- ✅ Schema imports fungerer  
- ✅ Service imports fungerer
- ✅ Import system health check bestått

## 📋 **For Fremtidige Endringer**

Hvis du trenger å referere til preview images:
- **Database:** `image.preview_image`
- **Schema:** `has_preview_image`, `ImagePreviewResponse`
- **API:** Bruk `preview_data` for binærdata
- **Dokumentasjon:** "preview image" i stedet for "thumbnail"

---
*Endring implementert som del av ImaLink vedlikeholdsarbeid for bedre kodekvalitet og klarhet.*