# ImaLink

Et enkelt og intuitivt verktøy for organisering av store bildematerialer.

## 🎯 Status

**Fase 1 MVP er ferdig!** ✅

### ✅ Implementerte funksjoner:
- **Import System**: Bakgrunnsprosessering med sanntids fremgang
- **EXIF-rotasjon**: Automatisk orientering av bilder som i File Explorer
- **RAW+JPEG håndtering**: Smart deteksjon og håndtering av RAW-filer
- **Duplikatdeteksjon**: Perceptuell hash for å unngå duplikater
- **Fotograf-admin**: Fullstendig CRUD med email og bio
- **Responsivt galleri**: Web-basert visning med thumbnail-rotasjon
- **Modern arkitektur**: FastAPI + SQLite + ekstern CSS

## 🧠 Designfilosofi

ImaLink følger noen unike prinsipper som skiller den fra andre fotoarkiveringsprogrammer:

### 1. "Hot Thumbnail med Rotasjonsuavhengig Hash"
- **Hot thumbnail**: Miniaturbilder lagres som binærdata direkte i databasen for umiddelbar tilgang
- **Rotasjonsuavhengig hash**: Perceptuell hash beregnes fra bildeinnholdet, ikke fildata
- **Resultat**: Samme bilde får samme hash uavhengig av rotasjon eller EXIF-orientering
- **Fordel**: Perfekt duplikatdeteksjon selv når bilder er rotert eller re-eksportert

### 2. Hundre Prosent Skille Mellom Kildefil og Server
- **Kildefiler kan være offline**: Original-filer kan ligge på USB-disker, NAS eller cloud-lagring
- **Serveren er komplett uavhengig**: All nødvendig informasjon lagres i databasen
- **Metadata-preservering**: EXIF, thumbnail og bildedata bevares i database
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

```bash
# Naviger til Fase 1
cd fase1/src

# Start applikasjonen
python main.py

# Åpne i nettleser
open http://localhost:8000
```

Se [Fase 1 README](./fase1/README.md) for detaljert dokumentasjon.

## 🏗️ Utviklingsplan

1. **✅ Programspesifikasjon** - Ferdig
2. **✅ Teknologivalg** - Python/FastAPI/SQLite
3. **✅ Prototype (Fase 1)** - Ferdig MVP
4. **⏳ Utrulling** - Neste fase

## 🎯 Målsetting

Utvikle et skalerbart system for:
- ✅ Organisering av store bildesamlinger
- ✅ Duplikatdeteksjon
- ✅ EXIF-metadata håndtering
- ✅ Web-basert grensesnitt
- ⏳ Desktop-grensesnitt (senere fase)

