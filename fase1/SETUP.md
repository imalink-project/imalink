# Kom i gang med ImaLink Fase 1

## 🚀 Rask oppstart

### 1. Installer avhengigheter
```bash
cd fase1
pip install -r requirements.txt
```

### 2. Opprett miljøvariabler (valgfritt)
```bash
# Kopier eksempel-filen
copy .env.example .env

# Rediger .env etter behov (standardverdier fungerer fint)
```

### 3. Start applikasjonen
```bash
cd src
python main.py
```

### 4. Åpne i nettleser
Gå til: http://localhost:8000

---

## 🧪 Test systemet

### Test 1: Import av enkeltbilde
```bash
# Via API (bruk PowerShell eller Postman)
curl -X POST "http://localhost:8000/api/import/test-single" \
     -H "Content-Type: application/json" \
     -d '{"file_path": "C:\\temp\\testbilde.jpg"}'
```

### Test 2: Import av katalog
1. Åpne http://localhost:8000
2. Skriv inn sti til en katalog med bilder (f.eks. `C:\temp\bilder`)
3. Klikk "Start Import"
4. Følg fremdriften i statusfeltet

### Test 3: Se bildegalleri
- Bildene vises automatisk etter import
- Klikk på et bilde for å se detaljer
- Bruk søkefeltet for å filtrere

---

## 📁 Mappestruktur

```
fase1/
├── src/                     # Hovedkildekode
│   ├── main.py             # FastAPI app (start her)
│   ├── database/           # Database-lag
│   │   ├── models.py       # SQLAlchemy modeller
│   │   └── connection.py   # DB-tilkobling
│   ├── services/           # Forretningslogikk
│   │   └── image_service.py # Bildeprosessering
│   ├── api/                # REST API
│   │   ├── images.py       # Bilde-endpoints
│   │   └── import_api.py   # Import-endpoints
│   └── static/             # Web-frontend
│       ├── index.html      # Hovedside
│       ├── style.css       # Stiler
│       └── app.js          # JavaScript
├── tests/                  # Tester (ikke implementert ennå)
├── requirements.txt        # Python-avhengigheter
└── README.md              # Denne filen
```

---

## 🔧 API-dokumentasjon

FastAPI genererer automatisk API-dokumentasjon:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Viktige endpoints:

**Import:**
- `POST /api/import/start` - Start import av katalog
- `GET /api/import/status/{session_id}` - Sjekk importstatus
- `POST /api/import/test-single` - Test enkeltbilde

**Bilder:**
- `GET /api/images/` - List bilder
- `GET /api/images/{id}` - Bildedetaljer
- `GET /api/images/{id}/thumbnail` - Thumbnail
- `GET /api/images/search` - Søk i bilder

---

## 🗃️ Database

Systemet bruker SQLite som lagres som `imalink.db` i `src/`-mappen.

### Tabeller:
- **images** - Bildemetadata og thumbnails
- **import_sessions** - Sporing av import-prosesser

### Reset database:
```bash
# Stopp applikasjonen og slett databasefilen
rm src/imalink.db
# Start applikasjonen igjen for å lage ny database
```

---

## 🚨 Feilsøking

### "Import "xxx" could not be resolved"
Dette er bare IDE-advarsler. Kjør likevel:
```bash
cd src
python main.py
```

### "No module named 'piexif'"
Installer avhengigheter:
```bash
pip install -r requirements.txt
```

### Databasefeil
Slett og opprett database på nytt:
```bash
rm src/imalink.db
```

### Port allerede i bruk
Endre port i `main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
```

---

## 📋 Testscenarier

### Scenario 1: Første gangs oppsett
1. Installer avhengigheter
2. Start app
3. Importer 10-20 testbilder
4. Utforsk galleriet

### Scenario 2: Større import
1. Forbered katalog med 100+ bilder
2. Start import via web-grensesnittet
3. Følg fremdriften
4. Test søkefunksjoner

### Scenario 3: Duplikatsjekk
1. Importer samme bilder to ganger
2. Verifiser at duplikater hoppes over
3. Sjekk import-statistikk

---

## 🎯 Neste steg

Når Fase 1 fungerer tilfredsstillende:

1. **Ytelsesoptimalisering** - Database-indekser, caching
2. **Mobilgrensesnitt** - Responsive design eller app
3. **Avanserte funksjoner** - Tags, rating, GPS-kart
4. **Integrasjoner** - Eksport til andre verktøy

---

## 💡 Tips

- **Backup:** Database og thumbnails lagres lokalt - ta backup!
- **Ytelse:** Store katalogimporter kan ta tid - vær tålmodig
- **Logging:** Sjekk konsollutskriften for detaljert informasjon
- **Utvikling:** Bruk `reload=True` for automatisk restart ved endringer