## PhotoSearch System - Komplett implementering ✅

PhotoSearch-systemet er nå implementert og klart til bruk! Det støtter både **ad-hoc** søk (one-time searches) og **lagrede søk** (reusable saved searches).

---

## 📋 Oversikt

### Ny arkitektur
```
┌─────────────────────────────────────────────────────────┐
│  /api/v1/photo-searches                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  POST   /ad-hoc              → Ad-hoc søk (ikke lagret) │
│                                                          │
│  POST   /                    → Lagre nytt søk           │
│  GET    /                    → List lagrede søk         │
│  GET    /{id}                → Hent spesifikt søk       │
│  PUT    /{id}                → Oppdater søk             │
│  DELETE /{id}                → Slett søk                │
│                                                          │
│  POST   /{id}/execute        → Kjør lagret søk          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Gammelt endpoint (deprecated)
```
POST /api/v1/photos/search  → Fortsatt tilgjengelig for bakoverkompatibilitet
                               Bruker nå PhotoSearchService internt
```

---

## 🚀 Komme i gang

### 1. Kjør database-migrering
```bash
uv run python scripts/migrations/add_saved_photo_searches.py
```

### 2. Start serveren
```bash
export DISABLE_AUTH=True  # Hvis du bruker test-modus
uv run src/main.py
```

### 3. Test APIet
Gå til http://localhost:8000/docs og se den nye **photo-searches** seksjonen!

---

## 📚 Brukseksempler

### Ad-hoc søk (direkte søk uten å lagre)

```bash
curl -X POST http://localhost:8000/api/v1/photo-searches/ad-hoc \
  -H "Content-Type: application/json" \
  -d '{
    "author_id": 1,
    "import_session_id": 3,
    "tag_ids": [5, 12, 23],
    "rating_min": 4,
    "rating_max": 5,
    "has_raw": true,
    "has_gps": true,
    "taken_after": "2024-06-01T00:00:00",
    "taken_before": "2024-08-31T23:59:59",
    "offset": 0,
    "limit": 50,
    "sort_by": "taken_at",
    "sort_order": "desc"
  }'
```

**Søkekriterier-regler:**
- ✅ Alle felter er optional (None = ignorer dette filteret)
- ✅ Tomme søk (alle felter None) returnerer alle brukerens bilder
- ✅ Flere filtre kombineres med AND-logikk
- ✅ `tag_ids` bruker OR-logikk (bilder med MINST ÉN av taggene)
- ✅ Rating/dato-ranges er inclusive (både min og max inkludert)
- ✅ `has_gps`/`has_raw`: true = bare med, false = bare uten, null = alle

**Nye søkekriterier:**
- `import_session_id`: Filtrer på import-sesjon
- `tag_ids`: Filtrer på tags (array av tag IDs)

### Lagre et søk

```bash
curl -X POST http://localhost:8000/api/v1/photo-searches/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer 2024 RAW files",
    "description": "High quality RAW photos from summer vacation with landscape tag",
    "is_favorite": true,
    "search_criteria": {
      "author_id": 1,
      "import_session_id": 3,
      "tag_ids": [5],
      "rating_min": 4,
      "has_raw": true,
      "has_gps": true,
      "taken_after": "2024-06-01T00:00:00",
      "taken_before": "2024-08-31T23:59:59",
      "offset": 0,
      "limit": 100,
      "sort_by": "taken_at",
      "sort_order": "desc"
    }
  }'
```

### List lagrede søk

```bash
# Alle søk
curl http://localhost:8000/api/v1/photo-searches/

# Bare favoritter
curl "http://localhost:8000/api/v1/photo-searches/?favorites_only=true"
```

### Kjør et lagret søk

```bash
# Kjør søk med ID 1
curl -X POST http://localhost:8000/api/v1/photo-searches/1/execute

# Override pagination
curl -X POST "http://localhost:8000/api/v1/photo-searches/1/execute?override_offset=50&override_limit=25"
```

### Oppdater et lagret søk

```bash
curl -X PUT http://localhost:8000/api/v1/photo-searches/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer 2024 RAW files (5 stars only)",
    "search_criteria": {
      "author_id": 1,
      "rating_min": 5,
      "has_raw": true,
      "taken_after": "2024-06-01T00:00:00"
    }
  }'
```

---

## 🏗️ Teknisk implementering

### Nye filer opprettet:

1. **Model**: `src/models/saved_photo_search.py`
   - SavedPhotoSearch model med JSON-felt for search_criteria
   - Relationships til User

2. **Schemas**: `src/schemas/photo_search_schemas.py`
   - SavedPhotoSearchCreate
   - SavedPhotoSearchUpdate
   - SavedPhotoSearchResponse
   - SavedPhotoSearchSummary
   - SavedPhotoSearchListResponse

3. **Repository**: `src/repositories/photo_search_repository.py`
   - CRUD operations for SavedPhotoSearch
   - update_execution_stats for tracking

4. **Service**: `src/services/photo_search_service.py`
   - execute_adhoc_search() - direkte søk
   - create/get/list/update/delete_saved_search() - CRUD
   - execute_saved_search() - kjør lagret søk

5. **API**: `src/api/v1/photo_searches.py`
   - POST /ad-hoc - Ad-hoc søk
   - CRUD endpoints for lagrede søk
   - POST /{id}/execute - Kjør lagret søk

6. **Migration**: `scripts/migrations/add_saved_photo_searches.py`
   - Lager saved_photo_searches tabell

### Endrede filer:

- `src/models/user.py` - La til saved_photo_searches relationship
- `src/models/__init__.py` - Eksporterer SavedPhotoSearch
- `src/main.py` - Registrerer photo_searches router
- `src/api/v1/photos.py` - POST /search bruker nå PhotoSearchService

---

## 💾 Database-skjema

```sql
CREATE TABLE saved_photo_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    search_criteria JSON NOT NULL,  -- PhotoSearchRequest as JSON
    is_favorite BOOLEAN NOT NULL DEFAULT 0,
    result_count INTEGER,
    last_executed DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 🎯 Fremtidige utvidelser

Systemet er designet for å enkelt kunne utvides med:

1. **Smart Collections**: Kombinere lagrede søk med manuelle photo selections
2. **Søk for andre entiteter**: Kan lage ImportSessionSearch, AuthorSearch, etc.
3. **Deling**: Del lagrede søk med andre brukere
4. **Scheduled searches**: Automatiske e-post varsler ved nye resultater
5. **Search templates**: Pre-definerte søkemaler
6. **Query builder UI**: Visuell builder i frontend

---

## 📖 API Dokumentasjon

Komplett API-dokumentasjon finnes på:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Alle endpoints er user-scoped og krever autentisering (eller DISABLE_AUTH=True i test-modus).

---

## ✅ Testing checklist

- [x] Model opprettet med JSON field
- [x] Schemas for CRUD operations
- [x] Repository med alle CRUD methods
- [x] Service med ad-hoc og saved search logic
- [x] API endpoints registrert
- [x] User relationship lagt til
- [x] Migration script opprettet
- [ ] Kjør migration
- [ ] Test i /docs
- [ ] Test med curl/Postman

---

Systemet er nå klart til bruk! 🎉
