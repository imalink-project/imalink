# Dokumentasjon for Frontend Repositories

## 🆕 VIKTIG API OPPDATERING - Oktober 2025

### GET Photo API nå inkluderer EXIF metadata

**GET `/api/v1/photos/{hothash}`** returnerer nå `exif_dict` som del av PhotoResponse:

```json
{
  "hothash": "abc123...",
  "title": "Mitt foto",
  "exif_dict": {
    "camera": "Canon EOS R5",
    "lens": "RF 24-70mm f/2.8L IS USM", 
    "iso": 400,
    "aperture": "f/5.6",
    "shutter_speed": "1/125",
    "focal_length": "50mm"
  },
  "gps_latitude": 60.3913,
  "gps_longitude": 5.3221,
  "taken_at": "2024-10-19T15:30:45.123Z",
  // ... alle andre feltene som før
}
```

**🔄 VIKTIG ENDRING - Oktober 20, 2025:**
Frontend må nå sende strukturerte felter i tillegg til `exif_dict`:

```typescript
// POST /api/v1/image-files
{
  "filename": "IMG_2024.jpg",
  "hotpreview": "data:image/jpeg;base64,/9j/4AAQ...",
  "exif_dict": { /* Komplett EXIF data */ },
  
  // 🆕 PÅKREVD: Frontend må ekstrahere og sende disse:
  "taken_at": "2024-10-19T15:30:45.123Z",
  "gps_latitude": 60.3913,
  "gps_longitude": 5.3221
}
```

**Frontend ansvar:**
- ✅ **Ekstrahere taken_at** fra EXIF og sende som ISO 8601 string
- ✅ **Ekstrahere GPS koordinater** fra EXIF og sende som tall
- ✅ **Sende komplett exif_dict** (som før) for visning
- ✅ **Backend parser ikke lenger** EXIF for strukturerte felter

**Backend-endring:** `exif_dict` kommer fra den første (master) ImageFile knyttet til Photo. For JPEG/RAW-par blir vanligvis JPEG sin EXIF data vist.

---

## 🔗 Referering til Felles Dokumentasjon

### For Qt Frontend Repository

I ditt frontend repository, legg til følgende i README.md:

```markdown
## 📚 Dokumentasjon

**Viktig**: All dokumentasjon ligger i hovedrepoet for å unngå duplikater.

- **[API Reference](https://github.com/kjelkols/imalink/blob/main/docs/api/API_REFERENCE.md)** - REST API dokumentasjon
- **[EXIF Extraction Guide](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_EXTRACTION_GUIDE.md)** - Detaljert EXIF implementasjonsguide (påkrevd)
- **[EXIF Specification](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_SPECIFICATION.md)** - EXIF JSON strukturspesifikasjon
- **[Qt Frontend Guide](https://github.com/kjelkols/imalink/blob/main/docs/frontend/QT_FRONTEND_GUIDE.md)** - Qt utviklingsguide  
- **[Dokumentasjonsoversikt](https://github.com/kjelkols/imalink/blob/main/docs/README.md)** - Alle dokumenter

### Lokalt oppsett
For lokal utvikling, klon hovedrepoet for tilgang til dokumentasjon:
\`\`\`bash
git clone https://github.com/kjelkols/imalink.git
# Dokumentasjon ligger i imalink/docs/
\`\`\`
```

### For andre Frontend Technologies (Web, Mobile, etc.)

```markdown
## 📚 Dokumentasjon

Dette frontend-prosjektet bruker ImaLink backend API.

- **[API Reference](https://github.com/kjelkols/imalink/blob/main/docs/api/API_REFERENCE.md)** - REST API dokumentasjon
- **[EXIF Extraction Guide](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_EXTRACTION_GUIDE.md)** - Praktisk implementasjonsguide (påkrevd)
- **[EXIF Specification](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_SPECIFICATION.md)** - JSON strukturspesifikasjon
- **[Backend Repository](https://github.com/kjelkols/imalink)** - Hovedrepo med full dokumentasjon

### Backend Setup
For lokal utvikling:
\`\`\`bash
git clone https://github.com/kjelkols/imalink.git
cd imalink/fase1
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
\`\`\`

API vil være tilgjengelig på: \`http://localhost:8000/api/v1\`
```

## 🔄 Synkronisering av Dokumentasjon

### Når du oppdaterer API-er
1. Oppdater dokumentasjon i hovedrepoet (`imalink/docs/`)
2. Commit endringer
3. Informer frontend teams om oppdateringer

### For Frontend Utviklere
1. Bookmark dokumentasjons-linkene over
2. Sjekk for oppdateringer i hovedrepoet regelmessig
3. Ikke dupliser dokumentasjon i frontend repos

## 📋 Fordeler med denne tilnærmingen

- ✅ **Single Source of Truth**: All dokumentasjon ligger ett sted
- ✅ **Konsistens**: Alle teams ser samme informasjon  
- ✅ **Vedlikehold**: Kun ett sted å oppdatere dokumentasjon
- ✅ **Versjonering**: Dokumentasjon følger backend-versjoner
- ✅ **Historie**: Full commit-historie for dokumentasjonsendringer

## 🔍 Alternativer

Hvis du foretrekker andre løsninger:

### 1. Git Submodules
```bash
# I frontend repo:
git submodule add https://github.com/kjelkols/imalink.git docs-source
# Dokumentasjon tilgjengelig i docs-source/docs/
```

### 2. GitHub Pages
Hvis hovedrepoet publiserer docs til GitHub Pages, kan du referere direkte til de publiserte sidene.

### 3. Package Distribution  
Dokumentasjon kan pakkes som NPM package eller PyPI package for automatisk distribusjon.

---

**Anbefaling**: Start med direkte GitHub-links (alternativ 1 over). Det er enkelt og effektivt for de fleste brukstilfeller.