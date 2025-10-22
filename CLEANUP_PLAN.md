# ImaLink 1.0 Filstruktur Cleanup Plan

## 🎯 Mål
Flytte fra utviklings-struktur (`fase1/`) til produksjons-klar struktur.

---

## 📁 Nåværende Struktur (Før Cleanup)

```
imalink/
├── CHANGELOG.md
├── README.md
├── fase1/                        # ← ALT ER HER (skal flyttes)
│   ├── src/                      # ← Backend kode
│   ├── tests/                    # ← Test suite
│   ├── scripts/                  # ← Utility scripts
│   ├── python_demos/             # ← Demo scripts (development)
│   ├── desktop_demo/             # ← Flet demo app
│   ├── demos/                    # ← Diverse demos
│   ├── docs/                     # ← Fase1-spesifikk dok
│   └── pyproject.toml            # ← Dependencies
├── docs/                         # ← Hoved-dokumentasjon
└── gammel_dokumentasjon/         # ← Legacy docs
```

---

## 🎨 Foreslått Struktur (Etter Cleanup)

```
imalink/
├── src/                          # ← Flyttet fra fase1/src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── photo_stacks.py
│   │   └── v1/
│   │       ├── photos.py
│   │       ├── tags.py
│   │       ├── authors.py
│   │       ├── import_sessions.py
│   │       └── debug.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── mixins.py
│   │   ├── user.py
│   │   ├── photo.py
│   │   ├── tag.py
│   │   ├── author.py
│   │   ├── image_file.py
│   │   ├── import_session.py
│   │   └── photo_stack.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── photo_repository.py
│   │   ├── tag_repository.py
│   │   ├── author_repository.py
│   │   ├── image_file_repository.py
│   │   ├── import_session_repository.py
│   │   └── photo_stack_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── photo_service.py
│   │   ├── tag_service.py
│   │   ├── author_service.py
│   │   ├── auth_service.py
│   │   ├── image_file_service.py
│   │   ├── import_session_service.py
│   │   └── photo_stack_service.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── photo_schemas.py
│   │   ├── tag_schemas.py
│   │   ├── author_schemas.py
│   │   ├── image_file_upload_schemas.py
│   │   ├── import_session_schemas.py
│   │   └── responses/
│   │       └── photo_stack_responses.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── exceptions.py
│   └── utils/
│       ├── __init__.py
│       ├── exif_utils.py
│       ├── security.py
│       └── image_processing.py
│
├── tests/                        # ← Flyttet fra fase1/tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_photos.py
│   ├── test_tags.py
│   ├── test_user_isolation.py
│   └── README.md
│
├── scripts/                      # ← Utvalgte scripts fra fase1/scripts/
│   ├── fresh_start.py
│   ├── nuclear_reset.py
│   └── README.md
│
├── docs/                         # ← Konsolidert dokumentasjon
│   ├── README.md
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── FRONTEND_INTEGRATION.md
│   └── api/
│       └── (eksisterende API docs)
│
├── .github/                      # ← NY: GitHub workflows
│   └── workflows/
│       ├── test.yml
│       └── deploy.yml
│
├── .env.example                  # ← NY: Environment template
├── .gitignore
├── pyproject.toml                # ← Flyttet fra fase1/
├── requirements.txt              # ← Generert fra pyproject.toml
├── pytest.ini                    # ← Flyttet fra fase1/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── RELEASE_CHECKLIST_1.0.md
└── RELEASE_PROCEDURE.md
```

---

## 🗑️ Filer/Mapper å Slette

### 1. Development/Demo Filer
```bash
fase1/python_demos/               # Demo scripts - ikke prod
fase1/desktop_demo/               # Flet demo - separat prosjekt
fase1/demos/                      # Streamlit demos - ikke prod
```

### 2. Utviklings-Scripts
```bash
fase1/scripts/debug/              # Debug scripts - ikke prod
fase1/scripts/maintenance/        # Hvis tomme/ubrukte
fase1/scripts/migrations/         # Hvis tomme
fase1/scripts/testing/            # Hvis tomme
```

### 3. Test-Data og Temp Filer
```bash
fase1/test_user_files/            # Test data
fase1/src/fase1.egg-info/         # Build artifacts
fase1/src/__pycache__/            # Python cache
```

### 4. Gammel Dokumentasjon
```bash
gammel_dokumentasjon/             # Legacy docs
fase1/docs/finpuss_todo.md        # TODO lists
fase1/README.md                   # Duplikat av rot-README
```

---

## 🔧 Steg-for-Steg Cleanup

### Steg 1: Backup
```bash
cd /home/kjell/git_prosjekt
cp -r imalink imalink_backup_$(date +%Y%m%d)
```

### Steg 2: Opprett ny struktur
```bash
cd imalink

# Flytt hovedkode
mv fase1/src ./
mv fase1/tests ./
mv fase1/pyproject.toml ./
mv fase1/pytest.ini ./

# Flytt utvalgte scripts
mkdir -p scripts
mv fase1/scripts/fresh_start.py scripts/
mv fase1/scripts/nuclear_reset.py scripts/
mv fase1/scripts/README.md scripts/
```

### Steg 3: Slett unødvendige filer
```bash
# Slett development/demo filer
rm -rf fase1/python_demos
rm -rf fase1/desktop_demo
rm -rf fase1/demos

# Slett debug scripts
rm -rf fase1/scripts/debug
rm -rf fase1/scripts/maintenance
rm -rf fase1/scripts/testing

# Slett test data
rm -rf fase1/test_user_files

# Slett build artifacts
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Slett gammel dokumentasjon
rm -rf gammel_dokumentasjon
rm -rf fase1/docs/finpuss_todo.md
```

### Steg 4: Oppdater imports
```bash
# Alle imports må endres fra:
# from src.models.photo import Photo

# Til:
# from models.photo import Photo

# (Vi kan lage et script for dette hvis du vil)
```

### Steg 5: Oppdater config paths
```python
# src/core/config.py
# Oppdater hardkodede paths til environment variables
DATA_DIRECTORY: str = os.getenv("DATA_DIRECTORY", "/var/lib/imalink/data")
STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "/var/lib/imalink/storage")
```

### Steg 6: Lag .env.example
```bash
cat > .env.example << 'EOF'
# ImaLink Configuration

# Database
DATABASE_URL=sqlite:///./imalink.db

# Storage
DATA_DIRECTORY=/var/lib/imalink/data
STORAGE_ROOT=/var/lib/imalink/storage

# Authentication
SECRET_KEY=change-this-to-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=False
LOG_LEVEL=INFO

# Optional: Cloud Storage
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_S3_BUCKET=

# Optional: Email
# SMTP_HOST=
# SMTP_PORT=587
# SMTP_USERNAME=
# SMTP_PASSWORD=
EOF
```

### Steg 7: Test etter flytting
```bash
# Aktiver venv
cd /home/kjell/git_prosjekt/imalink
source .venv/bin/activate

# Reinstaller package
uv pip install -e .

# Kjør tester
pytest tests/

# Start server
cd src
python main.py
```

### Steg 8: Oppdater dokumentasjon
- [ ] README.md: Oppdater paths og instruksjoner
- [ ] docs/DEPLOYMENT.md: Oppdater til ny struktur
- [ ] docs/ARCHITECTURE.md: Reflekter ny struktur

### Steg 9: Commit endringer
```bash
git add -A
git commit -m "Restructure for 1.0 release

- Move fase1/src to root src/
- Move fase1/tests to root tests/
- Remove development demos and scripts
- Add .env.example
- Update documentation for new structure
"
```

---

## ⚠️ Viktige Merknader

1. **Import paths**: Alle imports må oppdateres når vi flytter `src/` til root
2. **PYTHONPATH**: Må settes riktig i production
3. **Config paths**: Hardkodede `/mnt/c/temp` må ut
4. **Database**: Test fresh database init etter flytting
5. **Testing**: Kjør full test suite etter flytting

---

## 📌 Alternativ: Behold fase1/

Hvis du vil beholde `fase1/` for å unngå store endringer:

```
imalink/
├── fase1/                        # Produksjonskode (rename til 'backend'?)
│   ├── src/
│   ├── tests/
│   └── pyproject.toml
├── docs/
├── README.md
└── CHANGELOG.md
```

Dette er enklere men mindre standard.

---

*Velg strategi basert på din tidslinje og behov!*
