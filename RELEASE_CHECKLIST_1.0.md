# ImaLink 1.0 Release Checklist

## 🎯 Pre-Release Tasks

### 1. Code Cleanup & Organization
- [ ] Flytt `fase1/` innhold til rot-nivå `src/`
- [ ] Slett gammel dokumentasjon og test-filer som ikke er relevante
- [ ] Rydd opp i `scripts/` - behold kun produksjonsklare scripts
- [ ] Fjern `desktop_demo/` hvis ikke produksjons-klar
- [ ] Fjern `python_demos/` hvis kun for utvikling

### 2. Version & Dependencies
- [ ] Oppdater `version = "1.0.0"` i `pyproject.toml`
- [ ] Lås alle dependency-versjoner (fjern `>=`, bruk `==`)
- [ ] Kjør sikkerhetsskanning: `pip-audit` eller `safety check`
- [ ] Test at alle dependencies installeres korrekt
- [ ] Generer `requirements.txt` fra `pyproject.toml`

### 3. Documentation
- [ ] Oppdater `CHANGELOG.md` med fullstendig 1.0.0 release notes
- [ ] Oppdater `README.md` med produksjons-setup
- [ ] Verifiser at `API_REFERENCE.md` er oppdatert
- [ ] Skriv `DEPLOYMENT.md` med installasjonsinstruksjoner
- [ ] Legg til `CONTRIBUTING.md` hvis open source
- [ ] Sjekk at `LICENSE` er på plass

### 4. Testing
- [ ] Kjør alle unit tests: `pytest tests/`
- [ ] Verifiser at alle API endpoints fungerer
- [ ] Test autentisering og user isolation
- [ ] Test photo corrections (timeloc, view)
- [ ] Test photo tags (create, rename, delete)
- [ ] Test import flow
- [ ] Test med fresh database (init_db)

### 5. Configuration
- [ ] Lag `.env.example` med alle nødvendige miljøvariabler
- [ ] Dokumenter alle config-parametere
- [ ] Sett opp produksjons-klar `config.py`
- [ ] Fjern hardkodede paths (`/mnt/c/temp`)
- [ ] Legg til environment-basert config (dev/staging/prod)

### 6. Security
- [ ] Endre default SECRET_KEY i eksempler
- [ ] Sjekk at ingen passord/tokens er commited
- [ ] Verifiser CORS-settings for produksjon
- [ ] Sjekk at DEBUG=False i prod
- [ ] Review all authentication endpoints
- [ ] Test rate limiting (hvis implementert)

### 7. Database
- [ ] Lag Alembic migration for 1.0 schema
- [ ] Test database migration fra tom database
- [ ] Dokumenter backup-strategi
- [ ] Lag script for database initialization

### 8. Git & GitHub
- [ ] Lag `v1.0.0` branch fra main
- [ ] Tag release: `git tag -a v1.0.0 -m "Release 1.0.0"`
- [ ] Push tags: `git push origin --tags`
- [ ] Lag GitHub Release med release notes
- [ ] Legg ved assets (hvis nødvendig)

### 9. Distribution
- [ ] Bygg Docker image (hvis relevant)
- [ ] Test Docker deployment
- [ ] Publiser til PyPI (hvis relevant): `python -m build && twine upload dist/*`
- [ ] Lag installasjonsinstruksjoner for ulike plattformer

### 10. Post-Release
- [ ] Opprett `v1.1.0-dev` branch for videre utvikling
- [ ] Oppdater `version = "1.1.0-dev"` i `pyproject.toml`
- [ ] Announce release (blog, forum, etc.)
- [ ] Monitor for issues og feedback

---

## 📊 Version 1.0.0 Feature Summary

### Core Features
✅ Multi-user authentication (JWT)
✅ User data isolation
✅ Photo import system
✅ EXIF metadata extraction
✅ Photo corrections (time/location/view)
✅ Photo tagging system
✅ Author management
✅ Duplicate detection
✅ Preview generation (hot/cold)
✅ RAW+JPEG companion support

### API Endpoints
- Authentication: `/auth/*`
- Photos: `/photos/*`
- Tags: `/tags/*`
- Authors: `/authors/*`
- Import Sessions: `/import-sessions/*`

### Tech Stack
- Python 3.13.7
- FastAPI
- SQLAlchemy 2.0
- SQLite
- Pydantic v2
- JWT Authentication

---

## 🔄 Future Releases Planning

### Version 1.1.0 (Minor)
- New features, backward compatible
- Bug fixes from 1.0.0

### Version 2.0.0 (Major)
- Breaking API changes
- Major architectural changes

---

*Sjekk av alle items før du går videre med release!*
