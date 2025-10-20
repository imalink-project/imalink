# Fase 1 - ImaLink MVP ✅ FERDIG + Multi-User System

## ✅ Oppnådde mål
Ferdigstilt fungerende versjon av ImaLink med:
- ✅ Import av store bildegallerie med sanntids fremgang
- ✅ EXIF-metadata uttrekk og automatisk orientering  
- ✅ Perceptuell hash for duplikatdeteksjon
- ✅ Moderne web-basert galleri med responsive design
- ✅ SQLite database med fullstendig migrasjonsstøtte
- ✅ RAW+JPEG smart håndtering
- ✅ Fotograf-administrasjon med CRUD
- ✅ CSS-organisert arkitektur
- ✅ Bakgrunnsprosessering av imports
- ✅ **NYTT:** Multi-user autentisering med JWT
- ✅ **NYTT:** User-scoped data isolasjon
- ✅ **NYTT:** Krystallklare ImageFile upload endepunkter

## 🧠 Kjerneprinsippene

Fase 1 implementerer ImaLinks unike designfilosofi:

1. **🔥 Hot preview + Rotasjonsuavhengig Hash**
   - Miniaturbilder lagres binært i database for umiddelbar tilgang
   - Perceptuell hash beregnes fra bildeinnhold, ikke EXIF-orientering
   - Samme bilde = samme hash, uavhengig av rotasjon

2. **🔌 Server/Kildefil Separasjon** 
   - Alle metadata og hotpreviews lagres i database
   - Original-filer kan være offline (USB, NAS, cloud)
   - Galleri fungerer selv uten tilgang til kildebilder

3. **🔑 Hash som Universell Identitet**
   - Hash-verdien ER bildeidentiteten
   - Robust mot filflytting, omdøping og kopiering
   - Fremtidssikker for distribuerte systemer

Se [hovedprosjektets README](../README.md) for utdypende forklaring.

## Teknologi-stack
- **Backend:** Python 3.11+ med FastAPI
- **Database:** SQLite med SQLAlchemy  
- **Autentisering:** JWT tokens med SHA256-crypt
- **Bildeprosessering:** Pillow, piexif, imagehash
- **Demo/Testing:** Python scripts, CLI tools  
- **Testing:** pytest, Custom Python test suite

## Prosjektstruktur
```
fase1/
├── src/                    # Hovedkode
│   ├── main.py            # FastAPI app entry point
│   ├── api/               # API endpoints og routes
│   ├── core/              # Konfigurasjon og dependencies
│   ├── database/          # Database connection
│   ├── models/            # SQLAlchemy modeller
│   ├── repositories/      # Data access layer
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── utils/             # Hjelpefunksjoner
├── tests/                  # Unit tests og integrasjonstester
├── python_demos/           # Enkle demo scripts
├── scripts/                # Utility scripts og maintenance
├── docs/                   # Detaljert dokumentasjon
├── demos/                  # Demo applikasjoner (deprecated)
├── test_user_files/        # Test data og eksempelfiler
│   │   ├── models.py      # SQLAlchemy modeller
│   │   ├── connection.py  # Database connection
│   │   └── migrations/    # Database migrations
│   ├── services/          # Forretningslogikk
│   │   ├── __init__.py
│   │   ├── import_service.py
│   │   ├── image_service.py
│   │   └── metadata_service.py
│   ├── api/              # API endpoints
│   │   ├── __init__.py
│   │   ├── images.py
│   │   └── import.py
├── demos/                # Demo system
│   ├── README.md         # Demo documentation
│   └── streamlit/        # Streamlit demo system
│       ├── main.py       # Demo hub homepage
│       └── pages/        # Individual demo pages
├── tests/                # Tester
├── docs/                 # Dokumentasjon
├── requirements.txt      # Python avhengigheter
├── .env.example         # Miljøvariabler
└── README.md            # Setup instruksjoner
```

## Fordeler med denne strukturen
- **Isolert:** Kan slettes uten å påvirke resten av prosjektet
- **Modulær:** Lett å teste individuelle komponenter
- **Skalerbar:** Kan utvides til fullversjonen senere
- **Trygg:** Eksperimentering uten risiko

## ✅ Ferdigstilt
1. ✅ Requirements.txt med alle avhengigheter
2. ✅ Database-modeller (ImageFile, Photo, Author, ImportSession)
3. ✅ Import-tjeneste med bakgrunnsprosessering
4. ✅ Komplette API-endpoints (image-files, photos, authors, import)
5. ✅ Desktop client proof-of-concept (Flet)
6. ✅ EXIF-rotasjonshåndtering
7. ✅ Direct database access pattern
8. ✅ Hotpreview-generering med korrekt orientering

## 🚀 Bruk

### Start backend API:
```bash
cd src
python main.py
```

### Start desktop demo:
```bash
cd desktop_demo
uv run python author_crud_demo.py
```

### API og Testing:
- **Health**: `http://localhost:8000/health` - Server status
- **API Docs**: `http://localhost:8000/docs` - Interaktiv API dokumentasjon
- **Auth**: `http://localhost:8000/api/v1/auth/` - User registration/login
- **Users**: `http://localhost:8000/api/v1/users/` - User profile management
- **Authors API**: `http://localhost:8000/api/v1/authors/` - CRUD for fotografer
- **ImageFiles API**: `http://localhost:8000/api/v1/image-files/` - Fildata og metadata
  - **NEW**: `POST /image-files/new-photo` - Upload new unique photo
  - **NEW**: `POST /image-files/add-to-photo` - Add companion file to existing photo
- **Photos API**: `http://localhost:8000/api/v1/photos/` - Fotovisning og metadata

### Demo Suite:
```bash
# Kjør alle Python demos
uv run python python_demos/run_all_demos.py

# Individuell demo
uv run python python_demos/health_demo.py
uv run python python_demos/author_demo.py
uv run python python_demos/api_demo_suite.py

# Unit tests
uv run python tests/run_tests.py
```

### Database Reset (Experimentation):
```bash
# Show reset options
uv run python scripts/reset_options.py

# Quick API reset (recommended)
uv run python scripts/api_fresh_start.py

# Nuclear file deletion
uv run python scripts/nuclear_reset.py

# Full reset with backup
uv run python scripts/reset_database.py
```

### Database:
- Lokasjon: `/mnt/c/temp/00imalink_data/imalink.db` (WSL/Linux)
- Automatisk initialisering ved første kjøring
- Migrasjonsstøtte for oppgraderinger