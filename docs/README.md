# ImaLink Documentation

Felles dokumentasjon for ImaLink backend og frontend utvikling.

## 📚 Dokumentasjonsstruktur

```
docs/
├── README.md                    # Dette dokumentet
├── api/
│   └── API_REFERENCE.md        # Komplett REST API referanse
├── frontend/
│   └── QT_FRONTEND_GUIDE.md    # Qt frontend utviklingsguide
└── general_api_guidelines.md   # (eksisterende)
```

## 🔗 Hurtigreferanser

### Backend Utviklere
- **[API Reference](api/API_REFERENCE.md)** - Komplett REST API dokumentasjon
- **[Service Layer Guide](../fase1/docs/service_layer_guide.md)** - Backend arkitektur
- **[General API Guidelines](general_api_guidelines.md)** - API design prinsipper

### Frontend Utviklere  
- **[Qt Frontend Guide](frontend/QT_FRONTEND_GUIDE.md)** - Komplett Qt utviklingsguide
- **[API Reference](api/API_REFERENCE.md)** - API endpoints og eksempler
- **WSL Setup**: Se Qt guide for Windows ↔ WSL kommunikasjon

### Felles Ressurser
- **Base URL**: `http://localhost:8000/api/v1` (lokalt) eller `http://172.x.x.x:8000/api/v1` (WSL→Windows)
- **Interactive API Docs**: `http://localhost:8000/docs` (når backend kjører)
- **OpenAPI Spec**: `../openapi.json`

## 🚀 Rask start

### Backend
```bash
cd fase1
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Qt)
```bash
# Se frontend/QT_FRONTEND_GUIDE.md for komplett oppsett
pip install PySide6 requests Pillow
python main.py
```

## 📋 Funksjonsoversikt

### Core Features
- ✅ **Photo Management**: CRUD operasjoner for foto metadata
- ✅ **Image Import**: Automatisk JPEG/RAW par-gjenkjenning
- ✅ **Preview System**: 
  - Hotpreview (150x150) for gallery thumbnails
  - Coldpreview (800-1200px) for detail viewing
- ✅ **Perceptual Hash**: Automatisk dublettgjenkjenning
- ✅ **Similarity Search**: Finn lignende bilder basert på innhold

### API Endpoints
- **Photos**: `/photos/` - Hovedentiteter med metadata
- **Image Files**: `/image-files/` - Fysiske filer
- **Authors**: `/authors/` - Fotografer/opphavsrett
- **Import Sessions**: `/import-sessions/` - Batch import tracking
- **Similarity**: `/image-files/similar/{id}` - Finn lignende bilder
- **Previews**: 
  - `/photos/{hash}/hotpreview` - 150x150 thumbnails
  - `/photos/{hash}/coldpreview` - Medium-size previews

## 🔄 Oppdatering av dokumentasjon

Begge dokumenter vedlikeholdes i dette repoet og deles mellom backend/frontend teams.

**For å oppdatere:**
1. Rediger filer i `docs/` mappen
2. Commit endringer til hovedrepoet
3. Frontend repo kan referere til disse dokumentene

**Synkronisering:**
- Frontend repositories bør lenke til disse dokumentene i stedet for å duplisere dem
- Bruk relative paths eller repo-links for referanser