# Quick Start Guide

## 1. Installer avhengigheter

```bash
cd mini-frontend
pip install -r requirements.txt
```

## 2. Start FastAPI backend

I ett terminalvindu:
```bash
cd ../fase1
uvicorn src.main:app --reload
```

Backend starter på: http://localhost:8000

## 3. Start mini-frontend

I et annet terminalvindu:
```bash
cd mini-frontend
python main.py
```

## Funksjoner

### 📸 Gallery View (Standard)
- Viser alle photos i grid layout
- Hotpreview thumbnails hentet fra API
- Klikk på photo for detaljer
- Refresh-knapp for å oppdatere

### ⬆️ Import View
1. Klikk "Import" i navigasjon
2. Klikk "Select Images"
3. Velg én eller flere bildefiler
4. Klikk "Import Selected Files"

**Import prosess:**
- Hotpreview (150x150) genereres lokalt
- EXIF-rotasjon anvendes automatisk
- Metadata strippes fra hotpreview
- Base64-encoded hotpreview sendes til API
- Photo opprettes automatisk i backend

## Støttede filformater

- JPEG (.jpg, .jpeg)
- PNG (.png)
- HEIC (.heic)
- RAW (.dng, .cr2, .nef)

## Feilsøking

**"Connection refused"**
- Sjekk at FastAPI backend kjører på port 8000

**"No photos found"**
- Import noen bilder først via Import view

**Hotpreview ikke synlig**
- Sjekk at bildefilen er gyldig
- Se console output for feilmeldinger
