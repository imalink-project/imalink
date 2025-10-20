# 🚀 Oppsummering: Start produksjon

Dette dokumentet inneholder retningslinjer for å gå fra fase 1 (utvikling) til produksjonskode.

## 📋 Innholdsfortegnelse

1. [Kodestruktur og organisering](#1-kodestruktur-og-organisering)
2. [Konfigurasjon og miljøvariabler](#2-konfigurasjon-og-miljøvariabler)
3. [Database og migrasjoner](#3-database-og-migrasjoner)
4. [Sikkerhet](#4-sikkerhet)
5. [Logging og overvåking](#5-logging-og-overvåking)
6. [Testing](#6-testing)
7. [Dokumentasjon](#7-dokumentasjon)
8. [Dependencies og pakker](#8-dependencies-og-pakker)
9. [Performance](#9-performance)
10. [Deployment](#10-deployment)
11. [Foreslått filstruktur](#11-foreslått-filstruktur-for-produksjon)
12. [Quick checklist før deploy](#12-quick-checklist-før-deploy)

---

## 1. Kodestruktur og organisering

### Vurder å flytte koden ut av `/fase1/`

**Alternativ A: Flytt til rot-nivå**
- Flytt `/fase1/src/` til `/src/` (hovedprosjektet)
- Flytt `/fase1/tests/` til `/tests/`
- Fjern "fase1"-prefikset fra strukturen

**Alternativ B: Omdøp mappen**
- Omdøp `/fase1/` til et mer beskrivende navn som `/backend/` eller `/api/`

### ✅ Sjekkliste
- [ ] Besluttet struktur for produksjon
- [ ] Flyttet eller omdøpt fase1-mappen
- [ ] Oppdatert alle imports og paths
- [ ] Testet at alt fortsatt fungerer

---

## 2. Konfigurasjon og miljøvariabler

### ✅ Må gjøres
- [ ] Opprett `.env.example` med alle nødvendige miljøvariabler (uten sensitive verdier)
- [ ] Sjekk at `.env` er i `.gitignore`
- [ ] Bruk forskjellige konfigurasjonsfiler for dev/staging/prod
- [ ] Dokumenter alle miljøvariabler i README

### Foreslått struktur

```
config/
  ├── __init__.py
  ├── base.py          # Felles konfigurasjon
  ├── development.py   # Utviklingsmiljø
  ├── staging.py       # Test/staging-miljø
  └── production.py    # Produksjonsmiljø
```

### Eksempel `.env.example`

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/imalink
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ACCESS_TOKEN_EXPIRES=3600

# Storage
STORAGE_PATH=/var/lib/imalink/storage
MAX_UPLOAD_SIZE=100MB

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://app.imalink.no

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# External services (hvis relevant)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

---

## 3. Database og migrasjoner

### ✅ Må gjøres
- [ ] Sett opp Alembic for database-migrasjoner (hvis ikke allerede gjort)
- [ ] Lag en clean migreringshistorikk før produksjon
- [ ] Dokumenter hvordan migrasjoner skal kjøres
- [ ] Sett opp backup-strategi for produksjonsdatabase
- [ ] Test rollback av migrasjoner

### Alembic setup (hvis ikke allerede gjort)

```bash
# Installer Alembic
pip install alembic

# Initialiser Alembic
alembic init migrations

# Opprett første migrering
alembic revision --autogenerate -m "Initial schema"

# Kjør migrering
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backup-strategi
- Daglig automatisk backup
- Test restore-prosedyren regelmessig
- Oppbevar backups på flere lokasjoner
- Dokumenter restore-prosedyren

---

## 4. Sikkerhet

### ✅ Kritisk - må sjekkes før produksjon

- [ ] **Fjern alle hardkodede secrets/passord/API-nøkler**
  - Søk gjennom kodebasen: `grep -r "password.*=.*\"" --include="*.py"`
  - Bruk miljøvariabler for alle secrets
  
- [ ] **Aktiver HTTPS/TLS for produksjon**
  - Sett opp SSL-sertifikater (Let's Encrypt anbefales)
  - Redirect HTTP til HTTPS
  
- [ ] **Sett opp riktige CORS-regler**
  - Begrens til spesifikke domener i produksjon
  - Ikke bruk wildcard (`*`) i produksjon
  
- [ ] **Implementer rate limiting**
  - Begrens API-kall per bruker/IP
  - Beskytt mot brute-force angrep på login
  
- [ ] **Bruk sterke passord-hashing algoritmer**
  - bcrypt eller argon2 (ikke MD5 eller SHA1)
  - Implementer passord-policy (lengde, kompleksitet)
  
- [ ] **Sett opp logging av sikkerhetshendelser**
  - Logg mislykkede login-forsøk
  - Logg endringer i brukerrettigheter
  - Logg tilgang til sensitive data
  
- [ ] **Vurder å bruke secrets manager**
  - AWS Secrets Manager
  - HashiCorp Vault
  - Azure Key Vault
  - Google Cloud Secret Manager

### Sikkerhetstips
```python
# ❌ Dårlig - hardkodet secret
SECRET_KEY = "my-super-secret-key-123"

# ✅ Bra - fra miljøvariabel
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
```

---

## 5. Logging og overvåking

### ✅ Må gjøres
- [ ] Sett opp strukturert logging (JSON format)
- [ ] Konfigurer forskjellige log-nivåer for dev/prod
- [ ] Implementer health check endpoints
- [ ] Vurder metrics og monitoring
- [ ] Sett opp error tracking

### Health check endpoints

```python
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "ok"}

@app.get("/ready")
async def readiness_check():
    """Check if app is ready (database connected, etc.)"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}, 503
```

### Logging-konfigurasjon

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Bruk JSON-formatter i produksjon
if ENV == "production":
    handler.setFormatter(JSONFormatter())
```

### Monitoring-verktøy (vurder)
- **Prometheus + Grafana** - Metrics og visualisering
- **Sentry** - Error tracking
- **DataDog** - Full-stack monitoring
- **New Relic** - Application performance monitoring
- **ELK Stack** - Log aggregering og analyse

---

## 6. Testing

### ✅ Før produksjon
- [ ] Kjør alle unit tests og sørg for at de passerer
- [ ] Implementer integrasjonstester
- [ ] Vurder å sette opp CI/CD pipeline
- [ ] Lag smoke tests for kritisk funksjonalitet
- [ ] Test med realistiske data-volumer
- [ ] Gjennomfør load testing

### Test-kommandoer

```bash
# Kjør alle tester
pytest

# Med coverage
pytest --cov=src --cov-report=html

# Bare integrasjonstester
pytest tests/integration/

# Med verbose output
pytest -v

# Stopp ved første feil
pytest -x
```

### CI/CD Pipeline (GitHub Actions eksempel)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=src
      - name: Security check
        run: pip-audit
```

---

## 7. Dokumentasjon

### ✅ Oppdater før produksjon
- [ ] README.md med produksjons-setup
- [ ] API-dokumentasjon (OpenAPI/Swagger)
- [ ] Deployment-instruksjoner
- [ ] Troubleshooting guide
- [ ] Arkitektur-dokumentasjon
- [ ] Changelog oppdatert

### README.md skal inneholde
- Prosjektbeskrivelse
- Krav (Python-versjon, dependencies)
- Installasjonsinstruksjoner
- Konfigurasjon
- Kjøreinstruksjoner
- Testing
- Deployment
- Lisensinformasjon

### API-dokumentasjon
FastAPI genererer automatisk OpenAPI-dokumentasjon:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## 8. Dependencies og pakker

### ✅ Må gjøres
- [ ] Lås alle dependencies med eksakte versjoner
- [ ] Kjør sikkerhetsskanning
- [ ] Fjern development-only dependencies fra prod
- [ ] Dokumenter minimum Python-versjon

### Lås dependencies

```bash
# Med pip
pip freeze > requirements.txt

# Med poetry
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Med uv (hvis du bruker det)
uv pip freeze > requirements.txt
```

### Sikkerhetsskanning

```bash
# pip-audit
pip install pip-audit
pip-audit

# safety
pip install safety
safety check

# bandit (for kode-analyse)
pip install bandit
bandit -r src/
```

### Separer dev og prod dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "sqlalchemy>=2.0.0",
    # ... prod dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    # ... dev dependencies
]
```

---

## 9. Performance

### ✅ Vurder for produksjon
- [ ] Database indexes på ofte brukte kolonner
- [ ] Caching-strategi
- [ ] Connection pooling for database
- [ ] Async endpoints hvor det gir mening
- [ ] CDN for statiske filer (hvis relevant)

### Database indexes

```python
# I SQLAlchemy models
class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Indexed
    hothash = Column(String, unique=True, index=True)  # Indexed
    created_at = Column(DateTime, index=True)  # For sorting/filtering
```

### Connection pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # Antall permanente connections
    max_overflow=10,       # Maks ekstra connections
    pool_timeout=30,       # Timeout for å få connection
    pool_recycle=3600,     # Recycle connections hver time
)
```

### Caching med Redis

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

## 10. Deployment

### ✅ Forbered
- [ ] Velg deployment-strategi
- [ ] Opprett Dockerfile
- [ ] Sett opp CI/CD pipeline
- [ ] Definer rollback-strategi
- [ ] Test deployment i staging-miljø først

### Deployment-alternativer

1. **Docker + Docker Compose** (enkel start)
2. **Kubernetes** (skalering og orchestration)
3. **VM med systemd** (tradisjonell)
4. **Serverless** (AWS Lambda, Cloud Functions)
5. **PaaS** (Heroku, Railway, Render)

### Eksempel Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 imalink && chown -R imalink:imalink /app
USER imalink

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Eksempel docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/imalink
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./storage:/app/storage
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=imalink
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

### Rollback-strategi
1. Bruk versjonering (semantic versioning)
2. Tag alle releases i git
3. Ha en kjapp rollback-prosess
4. Test rollback regelmessig
5. Dokumenter rollback-prosedyren

---

## 11. Foreslått filstruktur for produksjon

```
imalink/
├── src/                          # Flyttet fra fase1/src/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── api/                      # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── photos.py
│   │   ├── photo_stacks.py
│   │   └── ...
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── photo.py
│   │   └── ...
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   └── ...
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   └── ...
│   ├── schemas/                  # Pydantic schemas
│   │   ├── requests/
│   │   └── responses/
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── logging.py
│   └── utils/                    # Utility functions
│       └── __init__.py
│
├── tests/                        # Flyttet fra fase1/tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── config/                       # Konfigurasjonsfiler
│   ├── __init__.py
│   ├── base.py
│   ├── development.py
│   ├── staging.py
│   └── production.py
│
├── migrations/                   # Alembic migrasjoner
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
│
├── scripts/                      # Utility scripts
│   ├── deploy.sh
│   ├── backup_db.sh
│   └── health_check.sh
│
├── docs/                         # Dokumentasjon
│   ├── README.md
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT.md
│   └── archive/                  # Gammel dokumentasjon
│
├── .github/                      # GitHub-spesifikk
│   └── workflows/
│       ├── test.yml
│       └── deploy.yml
│
├── .env.example                  # Eksempel miljøvariabler
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml                # Project metadata
├── requirements.txt              # Prod dependencies
├── requirements-dev.txt          # Dev dependencies
├── pytest.ini
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## 12. Quick checklist før deploy

### 🔒 Sikkerhet
- [ ] Ingen secrets i koden
- [ ] Alle passord og API-nøkler i miljøvariabler
- [ ] HTTPS aktivert
- [ ] CORS konfigurert riktig
- [ ] Rate limiting aktivert
- [ ] Sikkerhetsskanning kjørt (`pip-audit`, `safety`)
- [ ] SQL injection-beskyttelse verifisert
- [ ] XSS-beskyttelse implementert

### 💾 Database
- [ ] Migrasjoner kjørt og testet
- [ ] Backup konfigurert
- [ ] Restore-prosedyre testet
- [ ] Connection pooling satt opp
- [ ] Indexes på kritiske kolonner
- [ ] Database credentials sikret

### 📊 Logging og monitoring
- [ ] Produksjons-logging aktivert
- [ ] Log-nivå satt riktig (INFO eller WARNING)
- [ ] Strukturert logging (JSON) aktivert
- [ ] Error tracking satt opp (Sentry, etc.)
- [ ] Health check endpoints fungerer
- [ ] Metrics samles inn (hvis relevant)

### 🧪 Testing
- [ ] Alle unit tests passerer
- [ ] Integrasjonstester passerer
- [ ] Load testing utført
- [ ] Sikkerhetstester kjørt
- [ ] Staging-miljø testet grundig
- [ ] Rollback-prosedyre testet

### 📚 Dokumentasjon
- [ ] README oppdatert med prod-instruksjoner
- [ ] API-dokumentasjon generert og tilgjengelig
- [ ] Deployment guide skrevet
- [ ] Troubleshooting guide tilgjengelig
- [ ] CHANGELOG oppdatert
- [ ] Miljøvariabler dokumentert

### 🚀 Deployment
- [ ] Deployment-strategi valgt og dokumentert
- [ ] CI/CD pipeline satt opp og testet
- [ ] Dockerfile testet
- [ ] Docker Compose fungerer
- [ ] Produksjonsmiljø konfigurert
- [ ] DNS og domene satt opp
- [ ] SSL-sertifikater installert
- [ ] Rollback-plan definert

### ⚡ Performance
- [ ] Database queries optimalisert
- [ ] N+1 queries eliminert
- [ ] Caching vurdert og implementert hvor nødvendig
- [ ] Static files served effektivt
- [ ] Lazy loading implementert hvor relevant

### 📦 Dependencies
- [ ] Alle dependencies låst med eksakte versjoner
- [ ] Development dependencies skilt fra prod
- [ ] Sikkerhetssårbarheter sjekket
- [ ] Minimum Python-versjon dokumentert
- [ ] Docker image bygget og testet

---

## 🎯 Anbefalte neste steg for dette prosjektet

1. **Konsolider dokumentasjon** ✅ (pågående)
2. **Flytt koden fra `/fase1/` til rot-nivå eller omdøp til `/backend/`**
3. **Opprett produksjonskonfigurasjon** (`config/production.py`)
4. **Sett opp `.env.example` med alle nødvendige variabler**
5. **Lag Dockerfile og docker-compose.yml**
6. **Implementer health check endpoints**
7. **Sett opp strukturert logging**
8. **Kjør sikkerhetsskanning**
9. **Opprett CI/CD pipeline (GitHub Actions)**
10. **Test i staging-miljø**
11. **Deploy til produksjon**

---

## 📞 Ressurser

### Offisiell dokumentasjon
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Docker](https://docs.docker.com/)
- [Kubernetes](https://kubernetes.io/docs/)

### Sikkerhet
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

### Deployment
- [12 Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Sist oppdatert:** 2025-10-20
