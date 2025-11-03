# Database Migrations med Alembic

Alembic håndterer database schema-endringer på en kontrollert måte.

## 🚀 Vanlige kommandoer

### Lag en ny migration (autogenerate)
```bash
uv run alembic revision --autogenerate -m "Beskrivelse av endring"
```

### Kjør migrations (oppdater database)
```bash
uv run alembic upgrade head
```

### Se migration-historikk
```bash
uv run alembic history
```

### Se nåværende database-versjon
```bash
uv run alembic current
```

### Gå tilbake én migration
```bash
uv run alembic downgrade -1
```

## 📋 Workflow

### 1. Endre modellene dine
Eksempel: Legg til en kolonne i `src/models/photo.py`:
```python
description = Column(String(500), nullable=True)
```

### 2. Generer migration automatisk
```bash
uv run alembic revision --autogenerate -m "Add description to Photo"
```

### 3. Sjekk migration-filen
Se i `alembic/versions/` - Alembic har generert Python-kode for å endre databasen.

### 4. Kjør migration lokalt
```bash
uv run alembic upgrade head
```

### 5. Commit og push
```bash
git add alembic/versions/
git commit -m "Add description field to Photo model"
git push
```

### 6. Deploy til server (kjør migration automatisk)
```bash
./scripts/deploy.sh
```

## ⚙️ Konfigurasjon

- **alembic.ini**: Hovedkonfigurasjon
- **alembic/env.py**: Kobler til dine SQLAlchemy-modeller
- **alembic/versions/**: Migration-filer (GIT-tracked)

Alembic leser `DATABASE_URL` fra `.env` automatisk.

## 🎯 Fordeler

✅ **Versjonskontroll av database**: Hver endring er tracket i git  
✅ **Automatisk generering**: Sammenligner modeller vs database  
✅ **Reversible**: Kan gå tilbake til tidligere versjoner  
✅ **Team-friendly**: Alle kjører samme migrations i riktig rekkefølge
