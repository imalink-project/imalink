# Changelog

Alle viktige endringer i dette prosjektet dokumenteres i denne filen.

## [Unreleased] - 2025-10-20

### 🔄 API Endring - Frontend Ansvar
- **Frontend sender nå strukturerte EXIF felter**: `taken_at`, `gps_latitude`, `gps_longitude` må sendes direkte i POST ImageFile
- ✅ Backend stopper EXIF parsing - frontend ekstraherer og sender strukturerte data
- ✅ `exif_dict` fortsetter å sendes for komplett EXIF visning
- ⚠️ **BREAKING**: Frontend må oppdateres for å sende taken_at og GPS som direkte felter

### API Forbedring
- 🆕 **GET Photo API inkluderer nå EXIF metadata**: `exif_dict` field lagt til PhotoResponse
- ✅ EXIF data hentes automatisk fra master ImageFile (typisk JPEG for JPEG/RAW-par)
- ✅ Eliminerer behov for ekstra API-kall for å hente EXIF metadata
- ✅ Oppdatert API-dokumentasjon med komplette eksempler

### Arkitektur Cleanup
- 🧹 **FileStorage system fjernet**: Forenklet arkitektur før multi-user implementasjon
- ✅ ImportSession modell renset for FileStorage-avhengigheter
- ✅ Fjernet FileStorage API endpoints, services og repositories
- ✅ Frontend-sentrert tilnærming: All filhåndtering i klient-applikasjoner

## [2.0.0] - 2025-10-16

### Arkitektur-endring
- 🔄 Fjernet Svelte frontend - byttet til desktop-first tilnærming
- ✅ Ny desktop client (Flet) med direkte database-tilgang
- ✅ Backend renset for frontend-spesifikke referanser
- ✅ Arkivert frontend-dokumentasjon i gammel_dokumentasjon/
- ✅ Oppdatert terminologi: "frontend" → "client applications"

### Begrunnelse
Desktop client gir:
- Enklere arkitektur uten browser-begrensninger
- Direkte database-tilgang for bedre ytelse
- Ingen koordinering mellom frontend og backend
- Smidigere utvikling og vedlikehold

## [1.0.0] - 2025-10-01

### Lagt til
- ✅ Komplett import-system med bakgrunnsprosessering
- ✅ EXIF-orientering og automatisk hotpreview-rotasjon  
- ✅ RAW+JPEG smart håndtering og deteksjon
- ✅ Fotograf-administrasjon med navn, email og bio
- ✅ Responsivt web-grensesnitt med moderne design (nå arkivert)
- ✅ Sanntids import-fremgang med detaljert statistikk
- ✅ Duplikatdeteksjon basert på perceptuell hash
- ✅ SQLite database med migrasjonstøtte
- ✅ Søk og filtrering i bildegalleri
- ✅ CSS-organisering i eksterne filer
- ✅ Brukerrotasjon av hotpreviews
- ✅ GPS og EXIF-metadata uttrekk

### Teknisk
- FastAPI backend med automatisk API-dokumentasjon
- SQLAlchemy ORM med robuste modeller  
- PIL/Pillow for bildeprosessering med EXIF-støtte
- Python/Flet desktop client (erstatter web frontend)
- Automatisk database-initialisering
- Komprehensiv feilhåndtering

### Rettet
- EXIF-orientering håndteres nå konsekvent som File Explorer
- Duplikatsjekk basert på bildeinnhold, ikke filnavn
- RAW-filer med JPEG-kompanjon hoppes over riktig
- Hotpreview-generering med korrekt orientering
- Database-migrasjoner kjører automatisk og sikkert
- Responsiv design fungerer på alle enheter

### Sikkerhetsoppdateringer
- SQL injection-beskyttelse via parameteriserte queries
- Input-validering på alle API-endepunkter
- Sikker filsystem-tilgang med path-validering

---

## [0.1.0] - 2025-09-XX (Utviklingsversjoner)

### Lagt til
- Grunnleggende prosjektstruktur
- Database-modeller og migrasjoner
- Import-pipeline prototype
- Første versjon av web-grensesnitt
- EXIF-uttrekk og hotpreview-generering

### Teknisk
- Etablert FastAPI + SQLite arkitektur
- Implementert grunnleggende bildeprosessering
- Satt opp utviklingsmiljø og avhengigheter

---

## Versjonering

Dette prosjektet følger [Semantic Versioning](https://semver.org/).

Format: [MAJOR.MINOR.PATCH]
- **MAJOR**: Inkompatible API-endringer
- **MINOR**: Ny funksjonalitet på bakoverkompatibel måte  
- **PATCH**: Bakoverkompatible feilrettinger