# Multi-User Implementasjon: Koordinering og Rollback Strategi

## 🎯 Utfordringen: Koordinert Backend/Frontend Utvikling

Multi-user implementasjon påvirker begge sider av systemet:
- **Backend**: Database schema, API authentication, data scoping
- **Frontend**: Login/logout UI, user context, API token handling
- **Risk**: Breaking changes kan gjøre systemet ubrukelig

## 🛡️ Trygg Implementasjonsstrategi

### Fase 0: Forberedelse og Branching Strategy

#### Git Branching Plan
```bash
# Opprett feature branch for multi-user arbeid
git checkout -b feature/multi-user-implementation

# Frontend repository - tilsvarende branch
git checkout -b feature/multi-user-support
```

#### Backup og Testing Strategy
```bash
# Opprett database backup før endringer
cp fase1/imalink.db fase1/imalink.db.backup.$(date +%Y%m%d_%H%M%S)

# Sett opp parallell test-database
export IMALINK_DB_PATH="/tmp/imalink_multiuser_test.db"
```

### Fase 1: Backward-Compatible API Foundation

#### Mål: Bygge multi-user støtte uten å ødelegge eksisterende funksjonalitet

#### Backend Changes (Non-Breaking)
```python
# 1. Legg til User modell - UTEN å endre eksisterende tabeller ennå
class User(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

# 2. Legg til authentication endpoints - VALGFRI å bruke
@router.post("/auth/register")  # Ny endpoint
@router.post("/auth/login")     # Ny endpoint
@router.post("/auth/logout")    # Ny endpoint
@router.get("/auth/me")         # Ny endpoint

# 3. Eksisterende endpoints BEHOLDES UENDRET
@router.get("/photos")  # Fungerer som før - ingen breaking changes
@router.post("/photos") # Fungerer som før
```

#### Frontend Changes (Opt-in)
```typescript
// 1. Legg til authentication service - VALGFRI
class AuthService {
    async login(username: string, password: string): Promise<User | null>
    async logout(): Promise<void>
    getCurrentUser(): User | null
    isAuthenticated(): boolean
}

// 2. Eksisterende komponenter BEHOLDES UENDRET
// 3. Nye komponenter for login/registrering
// 4. User context provider (opt-in)
```

#### Database Migration Strategy
```sql
-- Reversible migration: Kun legg til User tabell
-- IKKE endre eksisterende tabeller ennå

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Opprett default "system" bruker for backward compatibility
INSERT INTO users (id, username, email, password_hash, display_name) 
VALUES (1, 'system', 'system@imalink.local', 'disabled', 'System User');
```

### Fase 2: Optional Authentication Layer

#### Backend: Dual-Mode API Support
```python
# Dependency som støtter både authenticated og anonymous brukere
async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returnerer user hvis authenticated, None hvis anonymous
    Gjør at API kan håndtere begge modi
    """
    try:
        token = request.headers.get("Authorization")
        if not token:
            return None
        
        # Valider JWT token
        user = validate_jwt_token(token, db)
        return user
    except:
        return None  # Fallback til anonymous

# Oppdater eksisterende endpoints gradvis
@router.get("/photos")
async def get_photos(
    current_user: Optional[User] = Depends(get_current_user_optional),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Støtter både authenticated og anonymous brukere
    """
    if current_user:
        # Multi-user mode: returner brukerens fotos
        return photo_service.get_photos_for_user(current_user.id)
    else:
        # Legacy mode: returner alle fotos (backward compatibility)
        return photo_service.get_all_photos()
```

#### Frontend: Progressive Enhancement
```typescript
// App kan brukes både med og uten authentication
class PhotoService {
    async getPhotos(): Promise<Photo[]> {
        const headers: Record<string, string> = {};
        
        // Legg til auth header hvis bruker er logget inn
        const token = AuthService.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return fetch('/api/v1/photos', { headers });
    }
}

// UI viser login-knapp, men appen fungerer uten innlogging
function App() {
    const [user, setUser] = useState<User | null>(null);
    
    return (
        <div>
            {user ? (
                <UserMenu user={user} onLogout={() => setUser(null)} />
            ) : (
                <LoginButton onClick={() => /* show login form */} />
            )}
            
            {/* Eksisterende foto-gallery fungerer uansett */}
            <PhotoGallery />
        </div>
    );
}
```

### Fase 3: Database Schema Migration (Reversible)

#### Forberedelse: Test Migration Script
```python
# scripts/migrations/test_user_scoped_migration.py
def test_migration_dry_run():
    """
    Test migrering uten å endre prod database
    """
    # Kopier database til temp fil
    shutil.copy("imalink.db", "test_migration.db")
    
    # Kjør migrering på test database
    migrate_to_user_scoped("test_migration.db")
    
    # Valider at data er intakt
    validate_migrated_data("test_migration.db")
    
    # Test rollback
    rollback_migration("test_migration.db")
    
    print("✅ Migration test successful")

def migrate_to_user_scoped(db_path: str):
    """
    Legg til user_id på eksisterende tabeller
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Legg til user_id kolonner (nullable først)
        cursor.execute("ALTER TABLE photos ADD COLUMN user_id INTEGER")
        cursor.execute("ALTER TABLE import_sessions ADD COLUMN user_id INTEGER") 
        cursor.execute("ALTER TABLE image_files ADD COLUMN user_id INTEGER")
        cursor.execute("ALTER TABLE file_storages ADD COLUMN user_id INTEGER")
        
        # 2. Sett alle eksisterende data til system user (id=1)
        cursor.execute("UPDATE photos SET user_id = 1 WHERE user_id IS NULL")
        cursor.execute("UPDATE import_sessions SET user_id = 1 WHERE user_id IS NULL")
        cursor.execute("UPDATE image_files SET user_id = 1 WHERE user_id IS NULL")
        cursor.execute("UPDATE file_storages SET user_id = 1 WHERE user_id IS NULL")
        
        # 3. Opprett indekser
        cursor.execute("CREATE INDEX idx_photos_user_id ON photos(user_id)")
        cursor.execute("CREATE INDEX idx_import_sessions_user_id ON import_sessions(user_id)")
        cursor.execute("CREATE INDEX idx_image_files_user_id ON image_files(user_id)")
        cursor.execute("CREATE INDEX idx_file_storages_user_id ON file_storages(user_id)")
        
        conn.commit()
        print("✅ Migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Migration failed: {e}")
    finally:
        conn.close()

def rollback_migration(db_path: str):
    """
    Fjern user_id kolonner for rollback
    """
    # SQLite gjør ikke DROP COLUMN enkelt, så bruk backup
    shutil.copy(f"{db_path}.backup", db_path)
    print("✅ Rollback completed")
```

### Fase 4: Full Multi-User Activation

#### Activation Script
```python
# scripts/activate_multiuser.py
def activate_multiuser_mode():
    """
    Aktiver full multi-user mode
    """
    # 1. Kjør database migrering
    migrate_to_user_scoped("imalink.db")
    
    # 2. Oppdater konfigurasi
    config = {
        "multi_user_enabled": True,
        "require_authentication": True,
        "default_user_fallback": False
    }
    
    with open("config/multiuser.json", "w") as f:
        json.dump(config, f)
    
    print("✅ Multi-user mode activated")
    print("🔄 Restart application to apply changes")

def deactivate_multiuser_mode():
    """
    Deaktiver multi-user og gå tilbake til single-user
    """
    # 1. Rollback database
    rollback_migration("imalink.db")
    
    # 2. Oppdater config
    config = {
        "multi_user_enabled": False,
        "require_authentication": False,
        "default_user_fallback": True
    }
    
    with open("config/multiuser.json", "w") as f:
        json.dump(config, f)
    
    print("✅ Reverted to single-user mode")
```

## 🔄 Rollback Strategi

### Quick Rollback (Database Level)
```bash
# Gå tilbake til pre-migration state
cp imalink.db.backup.YYYYMMDD_HHMMSS imalink.db

# Restart application
systemctl restart imalink  # eller docker restart
```

### Code Rollback (Git Level)
```bash
# Gå tilbake til stable branch
git checkout main

# Eller reverter specific commits
git revert <commit-hash>
```

### Config-Based Rollback
```python
# I main.py - sjekk config før aktivering av multi-user
def get_multiuser_config():
    try:
        with open("config/multiuser.json") as f:
            return json.load(f)
    except:
        return {"multi_user_enabled": False}

# Conditional middleware loading
if get_multiuser_config().get("multi_user_enabled", False):
    app.add_middleware(AuthenticationMiddleware)
else:
    # Single-user mode - ingen auth required
    pass
```

## 📋 Koordineringsplan Med Frontend Team

### Sprint Planning
```markdown
**Sprint 1: Foundation**
- Backend: User model, auth endpoints, optional auth dependency
- Frontend: Auth service, login components (ikke påkrevd ennå)
- Testing: Parallell testing av begge modi

**Sprint 2: Dual-Mode API**  
- Backend: Oppdater endpoints til å støtte both auth/non-auth
- Frontend: Progressive enhancement av eksisterende komponenter
- Testing: Regresjonstesting av legacy funksjonalitet

**Sprint 3: Migration Ready**
- Backend: Database migration scripts, rollback procedures  
- Frontend: Full user context integration
- Testing: Migration testing på test-data

**Sprint 4: Activation**
- Koordinert deployment av begge sider
- Database migration i prod
- Monitoring og rollback preparedness
```

### Communication Protocol
```markdown
**Daily Standups:**
- Status på backend/frontend progress
- Integration testing results
- Blokkere som krever koordinering

**Integration Points:**
- API contract changes (versioned)
- Database schema changes (migration scripts)
- Configuration changes (feature flags)

**Rollback Triggers:**
- Performance degradation > 20%
- Critical bugs in auth flow
- Data integrity issues
- Frontend incompatibility
```

## 🎯 Success Metrics

### Technical Metrics
- ✅ Zero downtime deployment
- ✅ < 100ms performance impact on queries
- ✅ 100% data integrity after migration
- ✅ All legacy functionality preserved

### User Experience Metrics
- ✅ Existing users can continue without forced account creation
- ✅ New users can register and get isolated data
- ✅ No breaking changes to existing workflows

## 🚨 Risk Mitigation

### High-Risk Scenarios
1. **Database corruption during migration** 
   - Mitigation: Full backup + dry-run testing
   
2. **API incompatibility breaking frontend**
   - Mitigation: Versioned APIs + backward compatibility

3. **Performance degradation with user scoping**
   - Mitigation: Index optimization + query profiling

4. **Auth system failures**
   - Mitigation: Fallback to anonymous mode + monitoring

### Emergency Procedures
```bash
# 🚨 Emergency rollback procedure
# 1. Revert to backup database
cp imalink.db.backup.latest imalink.db

# 2. Switch to single-user config
echo '{"multi_user_enabled": false}' > config/multiuser.json

# 3. Restart services
docker-compose restart

# 4. Verify functionality
curl http://localhost:8000/health
```

## 📝 Deliverables Checklist

### Before Starting
- [ ] Database backup procedures tested
- [ ] Rollback scripts validated
- [ ] Test environment identical to prod
- [ ] Frontend team alignment on timeline

### Development Phase
- [ ] Feature branches created
- [ ] Backward-compatible auth layer
- [ ] Parallel testing passing
- [ ] Migration scripts tested

### Deployment Phase  
- [ ] Coordinated deployment window
- [ ] Monitoring dashboards ready
- [ ] Rollback procedures rehearsed
- [ ] Success criteria defined

Denne strategien gir deg maksimal sikkerhet ved å:
1. **Bevare backward compatibility** gjennom hele prosessen
2. **Tilby multiple rollback options** på forskjellige nivåer
3. **Koordinere tett med frontend team** for smooth integration
4. **Teste grundig** før hver fase

Vil du at jeg skal starte med implementeringen av Fase 1 (Backward-Compatible API Foundation)?