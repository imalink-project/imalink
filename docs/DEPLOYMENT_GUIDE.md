# ImaLink Deployment Guide

Dette dokumentet beskriver arbeidsflyten for utvikling og deployment av ImaLink.

## 🎯 Arbeidsflyt Oversikt

### Lokal Utvikling (WSL)
- **Lokasjon**: `/home/kjell/git_prosjekt/imalink/`
- **Database**: PostgreSQL lokal utviklingsdatabase
- **Server**: `uv run uvicorn src.main:app --reload --port 8000`
- **Testing**: Lokal testing før push til GitHub

### Production (trollfjell.com)
- **Lokasjon**: `~/imalink/` på trollfjell-serveren
- **Database**: PostgreSQL production (`imalink` database)
- **Service**: Systemd service (`imalink.service`)
- **Port**: 8000 (intern), 80/443 via nginx reverse proxy

## 🔄 Standard Deployment Workflow

### 1. Utvikle lokalt
```bash
cd /home/kjell/git_prosjekt/imalink

# Gjør endringer i koden
# Test lokalt med:
uv run uvicorn src.main:app --reload

# Når alt fungerer lokalt:
git add -A
git commit -m "Beskrivelse av endringer"
git push
```

### 2. Deploy til production (automatisk)
```bash
./scripts/deploy.sh
```

Dette scriptet gjør automatisk:
- ✅ Pusher endringer til GitHub
- ✅ SSH til trollfjell-serveren
- ✅ Puller siste endringer
- ✅ Syncer Python dependencies med uv
- ✅ Kjører database migrations (Alembic)
- ✅ Restarter systemd service
- ✅ Viser status og logs

### 3. Manuell deployment (hvis nødvendig)
```bash
# Push lokalt først
git push

# På serveren
ssh trollfjell
cd ~/imalink
git pull
~/.local/bin/uv sync --python python3.13
~/.local/bin/uv run alembic upgrade head
sudo systemctl restart imalink
sudo systemctl status imalink
```

## 🗄️ Database Migrations med Alembic

### Hva er Alembic?
Alembic er et database migration-verktøy for SQLAlchemy. Det lar deg:
- Versjonskontrollere database schema-endringer
- Automatisk generere migrations fra model-endringer
- Rulle frem og tilbake mellom versjoner
- Synkronisere database-endringer mellom team-medlemmer

### Vanlige kommandoer

#### Se nåværende database-versjon
```bash
uv run alembic current
```

#### Se migration-historikk
```bash
uv run alembic history
```

#### Lag ny migration (autogenerate)
```bash
uv run alembic revision --autogenerate -m "Beskrivelse av endring"
```

#### Kjør migrations (oppdater database)
```bash
uv run alembic upgrade head
```

#### Gå tilbake én migration
```bash
uv run alembic downgrade -1
```

### Workflow for database-endringer

#### Eksempel: Legge til et nytt felt

**1. Endre modellen**
```python
# src/models/photo.py
class Photo(Base):
    # ... eksisterende felter ...
    description = Column(String(500), nullable=True)  # Nytt felt
```

**2. Generer migration automatisk**
```bash
uv run alembic revision --autogenerate -m "Add description field to Photo"
```

Alembic sammenligner modellene med databasen og genererer en migration-fil i `alembic/versions/`.

**3. Sjekk migration-filen**
```bash
# Se hva som ble generert
cat alembic/versions/2025_11_04_*_add_description_field_to_photo.py
```

Filen inneholder Python-kode som:
- `upgrade()`: Legger til kolonnen
- `downgrade()`: Fjerner kolonnen (for rollback)

**4. Test migrationen lokalt**
```bash
uv run alembic upgrade head
```

**5. Verifiser at alt fungerer**
```bash
uv run uvicorn src.main:app --reload
# Test API-endepunktene
```

**6. Commit og deploy**
```bash
git add alembic/versions/
git add src/models/photo.py
git commit -m "Add description field to Photo model"
./scripts/deploy.sh
```

Deployment-scriptet kjører automatisk `alembic upgrade head` på serveren!

## 📁 Filstruktur for Deployment

### .env filer (IKKE i git!)

**Lokal: `/home/kjell/git_prosjekt/imalink/.env`**
```bash
DATABASE_URL=postgresql://kjell:password@localhost/imalink_dev
DISABLE_AUTH=True
DEBUG=True
COLDPREVIEW_ROOT=/tmp/coldpreviews
```

**Server: `~/imalink/.env` på trollfjell**
```bash
DATABASE_URL=postgresql://imalink_user:imalink_prod_2025@localhost/imalink
DISABLE_AUTH=False
DEBUG=False
COLDPREVIEW_ROOT=/var/www/imalink/coldpreviews
```

### Systemd Service
**Lokasjon**: `/etc/systemd/system/imalink.service` på serveren

```ini
[Unit]
Description=ImaLink FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=kjell
WorkingDirectory=/home/kjell/imalink
Environment="PATH=/home/kjell/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/kjell/.local/bin/uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🛠️ Nyttige Kommandoer

### På serveren (trollfjell)

```bash
# Se service status
sudo systemctl status imalink

# Se live logs
sudo journalctl -u imalink -f

# Se siste 50 logglinjer
sudo journalctl -u imalink -n 50 --no-pager

# Restart service
sudo systemctl restart imalink

# Test at API svarer
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/docs
```

### Fra lokal maskin

```bash
# SSH til server
ssh trollfjell

# Følg server-logs direkte
ssh trollfjell "sudo journalctl -u imalink -f"

# Sjekk service status
ssh trollfjell "sudo systemctl status imalink"

# Deploy med ett script
./scripts/deploy.sh
```

## 🔍 Feilsøking

### Service starter ikke
```bash
# Se detaljerte feilmeldinger
sudo journalctl -u imalink -n 100 --no-pager

# Sjekk at .env filen eksisterer
cat ~/imalink/.env

# Test manuell oppstart
cd ~/imalink
~/.local/bin/uv run uvicorn src.main:app
```

### Database-problemer
```bash
# Sjekk at PostgreSQL kjører
sudo systemctl status postgresql

# Koble til database manuelt
psql -U imalink_user -d imalink -h localhost

# Se database-versjonen i Alembic
cd ~/imalink
~/.local/bin/uv run alembic current
```

### Import-feil
Alle imports må bruke `src.` prefix:
```python
# ✅ Riktig
from src.models import Photo
from src.services.photo_service import PhotoService

# ❌ Feil
from models import Photo
from services.photo_service import PhotoService
```

## 🚀 Neste Steg

### Nginx Reverse Proxy
Sett opp nginx for å eksponere API på port 80/443:
```bash
sudo nano /etc/nginx/sites-available/imalink
```

### HTTPS med Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d trollfjell.com
```

### Monitoring
- Sett opp logrotate for å håndtere logfiler
- Vurder Prometheus/Grafana for metrics
- Sett opp alerting for service-crashes

## 📚 Dokumentasjon

- **Alembic**: Se `alembic/README_ALEMBIC.md`
- **API Dokumentasjon**: http://trollfjell.com:8000/docs (når deployed)
- **Database Schema**: Se `src/models/` for alle modeller

## 🔐 Sikkerhet

- `.env` filer er ALDRI commitet til git
- Production har `DISABLE_AUTH=False`
- Database credentials er unike for production
- Service kjører som user `kjell` (ikke root)
