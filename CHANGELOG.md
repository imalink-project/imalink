# Changelog

Alle viktige endringer i dette prosjektet dokumenteres i denne filen.

## [1.0.0] - 2025-10-01

### Lagt til
- ✅ Komplett import-system med bakgrunnsprosessering
- ✅ EXIF-orientering og automatisk hotpreview-rotasjon  
- ✅ RAW+JPEG smart håndtering og deteksjon
- ✅ Fotograf-administrasjon med navn, email og bio
- ✅ Responsivt web-grensesnitt med moderne design
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
- Modern HTML/CSS/JavaScript frontend
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
- EXIF-uttrekk og thumbnail-generering

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