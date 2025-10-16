# ImaLink Mini-Frontend

Enkel desktop-applikasjon bygget med Flet for testing av ImaLink API.

## Funksjoner

- 📸 **Import bilder** - Velg bilder fra filsystem, generer hotpreview, send til API
- 🖼️ **Vis photos** - Se alle photos med hotpreview thumbnails
- 🔍 **Detaljer** - Klikk på photo for å se metadata og alle image files
- 👤 **Authors** - Administrer forfattere

## Installasjon

```bash
cd mini-frontend
pip install -r requirements.txt
```

## Kjøring

1. Start FastAPI backend først:
```bash
cd ../fase1
uvicorn src.main:app --reload
```

2. Start mini-frontend i nytt terminalvindu:
```bash
cd mini-frontend
python main.py
```

## API Endpoint

Standard API URL: `http://localhost:8000/api/v1`

Applikasjonen kommuniserer kun via REST API - ingen direkte database-tilgang.

## Struktur

```
mini-frontend/
├── main.py              # Hovedapplikasjon
├── components/          # UI-komponenter
│   ├── photo_gallery.py # Vis photos
│   ├── import_view.py   # Import bilder
│   └── photo_detail.py  # Detaljer om photo
├── services/            # API-kommunikasjon
│   └── api_client.py    # HTTP-klient for API-kall
└── utils/               # Hjelpefunksjoner
    └── image_utils.py   # Hotpreview-generering
```

## Hotpreview Generering

Hotpreview (150x150 JPEG) genereres lokalt i Python med PIL:
1. Åpne bilde
2. Anvend EXIF-rotasjon
3. Resize til 150x150 (thumbnail method)
4. Strip all EXIF metadata
5. Konverter til JPEG bytes
6. Base64-encode for API

## Avhengigheter

- `flet` - Desktop UI framework
- `Pillow` - Bildeprosessering (hotpreview)
- `httpx` - Moderne HTTP-klient for API-kall
