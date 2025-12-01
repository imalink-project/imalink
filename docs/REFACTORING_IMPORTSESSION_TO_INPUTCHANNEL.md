# Refactoring Plan: ImportSession → InputChannel

**Dato:** 2025-12-01  
**Status:** PLANLEGGING  
**Breaking Change:** JA

## Bakgrunn

ImportSession ble opprinnelig designet for batch-import av bilder. Konseptet har utviklet seg til å være en fleksibel måte for brukere å organisere bildeopplastinger på - ikke bare import-batches.

**Nytt konsept:** InputChannel
- Bruker definerer egne "kanaler" for forskjellige kilder/formål
- Fleksibelt: Minnekort, kamera, hendelse, prosjekt - hva brukeren vil
- Aktivt valg: Bruker velger kanal for hver opplasting

## Navneendringer

### Database
| Gammelt | Nytt |
|---------|------|
| `import_sessions` (tabell) | `input_channels` |
| `import_session_id` (FK i photos) | `input_channel_id` |

### Python/Backend
| Gammelt | Nytt |
|---------|------|
| `ImportSession` (model) | `InputChannel` |
| `ImportSessionRepository` | `InputChannelRepository` |
| `ImportSessionService` | `InputChannelService` |
| `ImportSessionCreateRequest` | `InputChannelCreateRequest` |
| `ImportSessionResponse` | `InputChannelResponse` |
| `import_session` (variabel) | `input_channel` |
| `import_session_id` (parameter) | `input_channel_id` |

### API Endpoints
| Gammelt | Nytt |
|---------|------|
| `GET /api/v1/import-sessions` | `GET /api/v1/input-channels` |
| `POST /api/v1/import-sessions` | `POST /api/v1/input-channels` |
| `GET /api/v1/import-sessions/{id}` | `GET /api/v1/input-channels/{id}` |
| `PATCH /api/v1/import-sessions/{id}` | `PATCH /api/v1/input-channels/{id}` |
| `DELETE /api/v1/import-sessions/{id}` | `DELETE /api/v1/input-channels/{id}` |

### JSON Fields
| Gammelt | Nytt |
|---------|------|
| `import_session_id` | `input_channel_id` |
| `import_sessions` | `input_channels` |

### UI/Brukervennlig
| Gammelt | Nytt |
|---------|------|
| "Quick Add" | "Quick Channel" / "Default Channel" |
| "Import Session" | "Input Channel" |
| "Import Batch" | "Upload Channel" |

## Påvirkede Komponenter

### 1. imalink Backend

#### Database Migration (Alembic)
**Fil:** `alembic/versions/2025_12_XX_XXXX-rename_import_session_to_input_channel.py`

```python
def upgrade():
    # Rename table
    op.rename_table('import_sessions', 'input_channels')
    
    # Rename foreign key column in photos
    op.alter_column('photos', 'import_session_id', 
                    new_column_name='input_channel_id')
    
    # Rename indexes
    op.execute('ALTER INDEX idx_import_sessions_user_id 
                RENAME TO idx_input_channels_user_id')
    op.execute('ALTER INDEX idx_photos_import_session_id 
                RENAME TO idx_photos_input_channel_id')

def downgrade():
    # Reverse operations
    ...
```

#### Models
**Filer å endre:**
- `src/models/import_session.py` → `src/models/input_channel.py`
- `src/models/photo.py` (FK referanse)
- `src/models/user.py` (relationship)
- `src/models/author.py` (relationship)

**Eksempel:**
```python
# src/models/input_channel.py
class InputChannel(Base, TimestampMixin):
    """User's input channel for organizing photo uploads"""
    __tablename__ = "input_channels"
    
    # ... rest of model
```

#### Repositories
**Filer å endre:**
- `src/repositories/import_session_repository.py` → `src/repositories/input_channel_repository.py`
- Alle imports av ImportSessionRepository

#### Services
**Filer å endre:**
- `src/services/import_session_service.py` → `src/services/input_channel_service.py`
- `src/services/photo_service.py` (referanser)
- `src/services/auth_service.py` ("Quick Add" → "Quick Channel")

#### API Endpoints
**Filer å endre:**
- `src/api/v1/import_sessions.py` → `src/api/v1/input_channels.py`
- `src/api/v1/photos.py` (query parameters)
- `src/main.py` (router registration)

#### Schemas
**Filer å endre:**
- `src/schemas/import_session_schemas.py` → `src/schemas/input_channel_schemas.py`
- `src/schemas/photo_schemas.py` (import_session_id fields)
- `src/schemas/photo_create_schemas.py` (import_session_id → input_channel_id)

#### Tests
**Filer å endre:**
- `tests/api/test_import_sessions_api.py` → `tests/api/test_input_channels_api.py`
- `tests/conftest.py` (fixtures)
- Alle test-filer som bruker `import_session` fixture
- `tests/README.md`

#### Dependencies
**Filer å endre:**
- `src/core/dependencies.py` (get_import_session_service → get_input_channel_service)

#### Examples
**Filer å endre:**
- `examples/import_session/` → `examples/input_channel/`
- Alle demo-scripts

#### Documentation
**Filer å endre:**
- `docs/API_REFERENCE.md` - Komplett oppdatering av alle referanser
- `docs/API_CHANGELOG_2025_11_12.md` - Legacy, noter endring
- `docs/multiuser/*.md` - Alle referanser
- `README.md` - Hvis ImportSession nevnt
- `.github/copilot-instructions.md` - Oppdater terminologi

### 2. imalink-schemas Package

**VIKTIG:** PhotoCreateSchema har `import_session_id` felt!

**Endringer:**
- `src/imalink_schemas/photo.py`:
  - `import_session_id: Optional[int]` → `input_channel_id: Optional[int]`
- Publiser ny major version: v3.0.0
- Breaking change for alle consumers

### 3. imalink-web (Frontend)

**Påvirkede områder:**
- API client calls til `/import-sessions` → `/input-channels`
- TypeScript interfaces:
  ```typescript
  interface ImportSession {  // → InputChannel
    id: number;
    title: string;
    // ...
  }
  
  interface Photo {
    import_session_id: number;  // → input_channel_id
    // ...
  }
  ```
- UI komponenter:
  - Import session selector → Input channel selector
  - Labels: "Import Session" → "Input Channel"
- State management (Redux/Zustand/etc)
- API hooks (react-query/swr)

**Filer å identifisere (i imalink-web):**
- Grep for: `import-session`, `importSession`, `import_session`
- API client: `api/` eller `services/`
- Types: `types/` eller `interfaces/`
- Components: UI komponenter

### 4. imalink-desktop (Desktop App)

**Påvirkede områder:**
- API client til backend
- Data models (TypeScript/Rust?)
- UI for å velge/opprette kanaler
- Lokal database/state

**Må identifiseres i imalink-desktop repo**

### 5. imalink-core

**Sjekk:** Bruker imalink-core ImportSession/import_session_id?
- Sannsynligvis IKKE (kun PhotoCreateSchema)
- Men hvis imalink-core refererer til imalink-schemas, må det oppdateres til v3.0.0

## Deployment Strategi

### Fase 1: Forberedelse (Parallell utvikling)
1. **Backend branch:** Create `refactor/input-channel`
2. **imalink-schemas:** Release v3.0.0-beta (for testing)
3. **Frontend branch:** Create `refactor/input-channel`
4. **Desktop branch:** Create `refactor/input-channel`

### Fase 2: Backend Migration (DEV)
1. Alembic migration kjøres lokalt (SQLite)
2. Alle tester oppdateres og passerer
3. Lokal testing med oppdatert frontend
4. Code review

### Fase 3: Database Backup (PRODUCTION)
```bash
ssh trollfjell "pg_dump imalink > ~/backups/imalink_pre_input_channel_$(date +%Y%m%d).sql"
```

### Fase 4: Production Migration (KOORDINERT)
**Timing:** Planlagt vedlikehold, kort downtime

1. **Stopp services:**
   ```bash
   ssh trollfjell "sudo systemctl stop imalink"
   ssh trollfjell "sudo systemctl stop imalink-core"  # hvis relevant
   ```

2. **Deploy backend med migration:**
   ```bash
   ssh trollfjell "cd ~/imalink && git pull && uv sync"
   ssh trollfjell "cd ~/imalink && uv run alembic upgrade head"
   ```

3. **Verifiser migration:**
   ```bash
   ssh trollfjell "psql -d imalink -c '\\dt input_channels'"
   ssh trollfjell "psql -d imalink -c 'SELECT COUNT(*) FROM input_channels'"
   ```

4. **Start backend:**
   ```bash
   ssh trollfjell "sudo systemctl start imalink"
   ssh trollfjell "sudo systemctl status imalink"
   ssh trollfjell "sudo journalctl -u imalink -n 50"
   ```

5. **Deploy frontend:**
   ```bash
   # imalink-web deployment (depends on hosting setup)
   # imalink-desktop release (new version for users to download)
   ```

### Fase 5: Rollback Plan (hvis nødvendig)
```bash
# Stop services
ssh trollfjell "sudo systemctl stop imalink"

# Restore database
ssh trollfjell "psql -d imalink < ~/backups/imalink_pre_input_channel_YYYYMMDD.sql"

# Revert to previous backend version
ssh trollfjell "cd ~/imalink && git checkout <previous-commit>"
ssh trollfjell "uv run alembic downgrade -1"

# Restart
ssh trollfjell "sudo systemctl start imalink"
```

## API Versioning Strategi

**Anbefaling:** Breaking change = ny major version

**Alternativ 1: V2 API (Anbefalt for større systemer)**
- Behold `/api/v1/import-sessions` (deprecated)
- Ny `/api/v2/input-channels`
- Gradvis migrasjon

**Alternativ 2: Direct Breaking Change (Enklere for små systemer)**
- Erstatt direkte: `/api/v1/import-sessions` → `/api/v1/input-channels`
- Alle klienter MÅ oppdateres samtidig
- Dokumenter godt i CHANGELOG

**Valg:** Alternativ 2 (mindre system, kontrollerte klienter)

## Risiko & Mitigering

| Risiko | Sannsynlighet | Konsekvens | Mitigering |
|--------|---------------|------------|------------|
| Migration feiler i production | Lav | Høy | Backup + test på staging først |
| Frontend/backend mismatch | Middels | Middels | Koordinert deploy + feature flag |
| Data tap | Svært lav | Kritisk | Database backup før migration |
| Downtime > 5 min | Lav | Lav | Test migration lokalt først |
| Desktop app fungerer ikke | Middels | Middels | Release ny versjon samtidig |

## Testing Plan

### Unit Tests
- [ ] Alle model tester oppdatert
- [ ] Alle repository tester oppdatert
- [ ] Alle service tester oppdatert
- [ ] Alle API endpoint tester oppdatert

### Integration Tests
- [ ] Backend end-to-end tests (create photo med input_channel_id)
- [ ] Migration test (SQLite)
- [ ] Migration test (PostgreSQL - via Docker)

### Manual Testing
- [ ] Lokal backend + frontend integration
- [ ] Desktop app mot lokal backend
- [ ] Staging deployment test
- [ ] Production smoke test etter deploy

## Timeline Estimat

- **Backend refactoring:** 4-6 timer
- **imalink-schemas update:** 1 time
- **Frontend refactoring:** 2-3 timer (avhengig av kompleksitet)
- **Desktop refactoring:** 2-3 timer (avhengig av arkitektur)
- **Testing:** 2-3 timer
- **Documentation:** 1-2 timer
- **Deployment:** 1 time (inkl. backup, migration, verification)

**Totalt:** ~13-18 timer arbeid, spredt over flere dager

## Checklist

### Pre-Refactoring
- [ ] Les denne planen grundig
- [ ] Backup production database
- [ ] Kommuniser planlagt downtime til brukere
- [ ] Create feature branches i alle repos

### Backend
- [ ] Alembic migration skrevet
- [ ] Models renamed og oppdatert
- [ ] Repositories renamed og oppdatert
- [ ] Services renamed og oppdatert
- [ ] API endpoints renamed og oppdatert
- [ ] Schemas renamed og oppdatert
- [ ] Dependencies oppdatert
- [ ] Tests oppdatert og passerer (159/159)
- [ ] Documentation oppdatert

### imalink-schemas
- [ ] PhotoCreateSchema oppdatert
- [ ] Version bumped til v3.0.0
- [ ] Tagged og published til GitHub
- [ ] CHANGELOG oppdatert

### imalink-web
- [ ] API client oppdatert
- [ ] TypeScript interfaces oppdatert
- [ ] UI components oppdatert
- [ ] Tests oppdatert og passerer
- [ ] Build successful

### imalink-desktop
- [ ] API client oppdatert
- [ ] Data models oppdatert
- [ ] UI oppdatert
- [ ] Tests oppdatert og passerer
- [ ] Build successful

### Deployment
- [ ] Backend deployed til trollfjell
- [ ] Migration executed successfully
- [ ] Services restarted
- [ ] Smoke tests passed
- [ ] Frontend deployed
- [ ] Desktop app released

### Post-Deployment
- [ ] Monitor logs for errors (24h)
- [ ] User feedback collected
- [ ] Performance metrics checked
- [ ] Database backup retention verified

## Referanser

- **Original model:** `src/models/import_session.py`
- **API docs:** `docs/API_REFERENCE.md`
- **Database:** `alembic/versions/`
- **Copilot instructions:** `.github/copilot-instructions.md`
