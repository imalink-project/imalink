# Fase 1 - ImaLink MVP

## Overordnet mål
Bygge en minimal, men fungerende versjon av ImaLink med:
- Import av 200-500 bilder 
- EXIF-metadata uttrekk
- Perceptuell hash for duplikatdeteksjon
- Enkel web-basert galleri
- SQLite database

## Teknologi-stack
- **Backend:** Python 3.11+ med FastAPI
- **Database:** SQLite med SQLAlchemy
- **Bildeprosessering:** Pillow, piexif, imagehash
- **Frontend:** Enkel HTML/CSS/JavaScript
- **Testing:** pytest

## Prosjektstruktur
```
fase1/
├── src/                    # Hovedkode
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point
│   ├── database/          # Database-relatert kode
│   │   ├── __init__.py
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
│   └── static/           # Frontend filer
│       ├── index.html
│       ├── style.css
│       └── app.js
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

## Neste steg
1. Sett opp requirements.txt
2. Implementer database-modeller
3. Lag import-tjeneste
4. Bygg API-endpoints
5. Lag enkel web-frontend