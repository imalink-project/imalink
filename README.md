# ImaLink

Et enkelt og intuitivt verktøy for organisering av store bildematerialer.

## 🎯 Status

**Fase 1 MVP er ferdig!** ✅

### ✅ Implementerte funksjoner:
- **Desktop Client**: Python/Flet desktop application med direkte database-tilgang
- **Import System**: Bakgrunnsprosessering med sanntids fremgang
- **EXIF-rotasjon**: Automatisk orientering av bilder som i File Explorer
- **RAW+JPEG håndtering**: Smart deteksjon og håndtering av RAW-filer
- **Duplikatdeteksjon**: Perceptuell hash for å unngå duplikater
- **Fotograf-admin**: Fullstendig CRUD med email og bio
- **Modern arkitektur**: FastAPI + SQLite + Flet desktop

## 🧠 Designfilosofi

ImaLink følger noen unike prinsipper som skiller den fra andre fotoarkiveringsprogrammer:

### 1. "Hot Hotpreview med Rotasjonsuavhengig Hash"
- **Hot hotpreview**: Miniaturbilder lagres som binærdata direkte i databasen for umiddelbar tilgang
- **Rotasjonsuavhengig hash**: Perceptuell hash beregnes fra bildeinnholdet, ikke fildata
- **Resultat**: Samme bilde får samme hash uavhengig av rotasjon eller EXIF-orientering
- **Fordel**: Perfekt duplikatdeteksjon selv når bilder er rotert eller re-eksportert

### 2. Hundre Prosent Skille Mellom Kildefil og Server
- **Kildefiler kan være offline**: Original-filer kan ligge på USB-disker, NAS eller cloud-lagring
- **Serveren er komplett uavhengig**: All nødvendig informasjon lagres i databasen
- **Metadata-preservering**: EXIF, hotpreview og bildedata bevares i database
- **Resultat**: Du kan vise, søke og organisere bilder selv om kildefilene ikke er tilgjengelige
- **Fordel**: Perfekt for arkivering på portable medier eller cloud-lagring

### 3. Hash som Universell Nøkkel
- **Perceptuell hash = bildeidentitet**: Hash-verdien ER bildet, uavhengig av filnavn eller lokasjon
- **Universell referanse**: Samme hash refererer til samme bilde på tvers av alle systemer
- **Filnavn-uavhengig**: Bilder kan flyttes, omdøpes eller kopieres uten å miste identitet
- **Fremtidssikring**: Hash-basert system kan utvides til distribuerte løsninger
- **Fordel**: Robust identifikasjon som aldri går i stykker ved filoperasjoner

Denne filosofien gjør ImaLink spesielt egnet for fotografer med store arkiver som må håndtere bilder på tvers av forskjellige lagringsmedier og systemer.

## 🚀 Kom i gang

### 📚 Dokumentasjon
- **[Fullstendig dokumentasjon](docs/README.md)** - Oversikt over all dokumentasjon
- **[API Reference](docs/api/API_REFERENCE.md)** - REST API dokumentasjon
- **[Qt Frontend Guide](docs/frontend/QT_FRONTEND_GUIDE.md)** - Qt desktop client utvikling

### Backend API:
```bash
# Naviger til Fase 1
cd fase1/src

# Start backend
python main.py

# API dokumentasjon
open http://localhost:8000/docs
```

### Desktop Client:
```bash
# Start desktop demo
cd fase1/desktop_demo
uv run python author_crud_demo.py

# Åpner i nettleser (WSL mode)
open http://localhost:8550
```

Se [Fase 1 README](./fase1/README.md) for detaljert backend-dokumentasjon og [docs/](docs/) for fullstendig API og frontend guides.

## 🏗️ Utviklingsplan

1. **✅ Programspesifikasjon** - Ferdig
2. **✅ Teknologivalg** - Python/FastAPI/SQLite/Flet
3. **✅ Prototype (Fase 1)** - Ferdig MVP med desktop client
4. **⏳ Full Import** - Photo import i desktop client
5. **⏳ Bildehåndtering** - Visning, organisering, tagging

## 🎯 Målsetting

Utvikle et skalerbart system for:
- ✅ Organisering av store bildesamlinger
- ✅ Duplikatdeteksjon
- ✅ EXIF-metadata håndtering
- ✅ Desktop-grensesnitt (Python/Flet)
- ⏳ Fullverdig photo management
- ⏳ Web viewer (read-only, senere fase)

