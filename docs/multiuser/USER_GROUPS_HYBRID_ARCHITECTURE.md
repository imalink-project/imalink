# User-Scoped med Gruppe-Deling: Hybrid Arkitektur

## 🎯 Konsept: Personal + Shared Spaces

Den beste løsningen kombinerer **User-Scoped** grunnarkitektur med **valgfri gruppe-deling** - dette gir både personlig sikkerhet og samarbeids-muligheter.

## 🏗️ Arkitektur: Dual-Mode System

### Core Principle
- **Default: Personal ownership** - All data tilhører en bruker
- **Optional: Group sharing** - Brukere kan velge å dele med grupper
- **Explicit permissions** - Deling krever aktiv handling

## 📊 Database Design: Evolved User-Scoped

### Basis Modeller (User-Scoped)
```python
class User(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255))
    is_active = Column(Boolean, default=True)

class Photo(Base, TimestampMixin):
    hothash = Column(String(64), primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    # ... resten som før
    
class ImportSession(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    # ... resten som før
```

### Gruppe-Utvidelser
```python
# ===== GRUPPE MODELLER =====

class Group(Base, TimestampMixin):
    """
    Brukergruppe for deling av foto-samlinger
    """
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Gruppe metadata
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_public = Column(Boolean, default=False)  # Synlig for andre brukere
    invite_code = Column(String(20), unique=True)  # For enkel joining
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")

class GroupMember(Base, TimestampMixin):
    """
    Gruppe-medlemskap med roller
    """
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    
    # Roller og tilganger
    role = Column(String(20), nullable=False, default='member')  # 'admin', 'editor', 'member', 'viewer'
    joined_at = Column(DateTime, default=datetime.utcnow)
    invited_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User")
    inviter = relationship("User", foreign_keys=[invited_by])

# ===== DELING MODELLER =====

class SharedPhoto(Base, TimestampMixin):
    """
    Foto delt med gruppe
    """
    photo_hothash = Column(String(64), ForeignKey('photos.hothash'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    
    # Deling metadata
    shared_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow)
    permissions = Column(String(20), default='view')  # 'view', 'edit', 'download'
    
    # Relationships
    photo = relationship("Photo")
    group = relationship("Group")
    sharer = relationship("User")

class SharedImportSession(Base, TimestampMixin):
    """
    ImportSession delt med gruppe
    """
    session_id = Column(Integer, ForeignKey('import_sessions.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    
    # Deling metadata
    shared_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow)
    permissions = Column(String(20), default='view')
    
    # Relationships
    session = relationship("ImportSession")
    group = relationship("Group")
    sharer = relationship("User")
```

## 🔑 Tilgangskontroll: Hybrid Queries

### Service Layer Med Tilgangskontroll
```python
class PhotoService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_photos_for_user(self, user_id: int, include_shared: bool = True) -> List[Photo]:
        """
        Hent fotos for bruker - både egne og delte
        """
        # Base query: Brukerens egne fotos
        own_photos = self.db.query(Photo).filter(Photo.owner_id == user_id)
        
        if not include_shared:
            return own_photos.all()
        
        # Utvidet query: + fotos delt med brukerens grupper
        user_groups = self.db.query(GroupMember.group_id).filter(
            GroupMember.user_id == user_id
        ).subquery()
        
        shared_photos = self.db.query(Photo).join(
            SharedPhoto, Photo.hothash == SharedPhoto.photo_hothash
        ).filter(
            SharedPhoto.group_id.in_(user_groups)
        )
        
        # Kombinér og returner (med duplikat-håndtering)
        all_photos = own_photos.union(shared_photos).distinct()
        return all_photos.all()
    
    def share_photo_with_group(self, user_id: int, photo_hothash: str, 
                              group_id: int, permissions: str = 'view') -> bool:
        """
        Del foto med gruppe (kun owner kan dele)
        """
        # Sjekk at bruker eier fotot
        photo = self.db.query(Photo).filter(
            Photo.hothash == photo_hothash,
            Photo.owner_id == user_id
        ).first()
        
        if not photo:
            raise PermissionError("You can only share photos you own")
        
        # Sjekk at bruker er medlem av gruppen
        membership = self.db.query(GroupMember).filter(
            GroupMember.user_id == user_id,
            GroupMember.group_id == group_id
        ).first()
        
        if not membership:
            raise PermissionError("You must be a member of the group to share")
        
        # Opprett deling
        shared_photo = SharedPhoto(
            photo_hothash=photo_hothash,
            group_id=group_id,
            shared_by=user_id,
            permissions=permissions
        )
        
        self.db.add(shared_photo)
        self.db.commit()
        return True

class GroupService:
    def create_group(self, user_id: int, name: str, description: str = None) -> Group:
        """
        Opprett ny gruppe
        """
        group = Group(
            name=name,
            description=description,
            created_by=user_id,
            invite_code=self._generate_invite_code()
        )
        
        self.db.add(group)
        self.db.flush()  # Get group.id
        
        # Legg til skaperen som admin
        membership = GroupMember(
            group_id=group.id,
            user_id=user_id,
            role='admin'
        )
        
        self.db.add(membership)
        self.db.commit()
        return group
    
    def join_group_by_invite(self, user_id: int, invite_code: str) -> bool:
        """
        Bli med i gruppe via invite-kode
        """
        group = self.db.query(Group).filter(
            Group.invite_code == invite_code
        ).first()
        
        if not group:
            raise NotFoundError("Invalid invite code")
        
        # Sjekk om allerede medlem
        existing = self.db.query(GroupMember).filter(
            GroupMember.group_id == group.id,
            GroupMember.user_id == user_id
        ).first()
        
        if existing:
            return True  # Already member
        
        # Legg til som medlem
        membership = GroupMember(
            group_id=group.id,
            user_id=user_id,
            role='member'
        )
        
        self.db.add(membership)
        self.db.commit()
        return True
```

## 🎨 API Design: Gradual Sharing

### Photo Endpoints Med Gruppe-Støtte
```python
@router.get("/photos")
async def get_photos(
    include_shared: bool = Query(True, description="Include photos shared with user's groups"),
    group_id: Optional[int] = Query(None, description="Filter by specific group"),
    current_user: User = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Hent fotos - default inkluderer delte fotos
    """
    if group_id:
        # Kun fotos delt med spesifikk gruppe
        return photo_service.get_photos_for_group(current_user.id, group_id)
    else:
        # Alle fotos (egne + delte)
        return photo_service.get_photos_for_user(current_user.id, include_shared)

@router.post("/photos/{photo_hothash}/share")
async def share_photo(
    photo_hothash: str,
    share_request: PhotoShareRequest,
    current_user: User = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Del foto med gruppe
    """
    return photo_service.share_photo_with_group(
        current_user.id, 
        photo_hothash, 
        share_request.group_id,
        share_request.permissions
    )

@router.delete("/photos/{photo_hothash}/share/{group_id}")
async def unshare_photo(
    photo_hothash: str,
    group_id: int,
    current_user: User = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Fjern deling av foto fra gruppe
    """
    return photo_service.unshare_photo(current_user.id, photo_hothash, group_id)

# ===== GRUPPE MANAGEMENT =====

@router.post("/groups")
async def create_group(
    group_data: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """
    Opprett ny gruppe
    """
    return group_service.create_group(current_user.id, group_data.name, group_data.description)

@router.post("/groups/join")
async def join_group(
    join_request: GroupJoinRequest,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """
    Bli med i gruppe via invite-kode
    """
    return group_service.join_group_by_invite(current_user.id, join_request.invite_code)

@router.get("/groups")
async def get_my_groups(
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """
    Hent brukerens grupper
    """
    return group_service.get_groups_for_user(current_user.id)
```

## 🔐 Tilgangsroller og Permissions

### Gruppe-Roller
```python
class GroupRole(str, Enum):
    ADMIN = "admin"      # Full kontroll over gruppen
    EDITOR = "editor"    # Kan dele egne fotos, redigere metadata på delte fotos
    MEMBER = "member"    # Kan se og dele egne fotos
    VIEWER = "viewer"    # Kun visning av delte fotos

class SharePermission(str, Enum):
    VIEW = "view"        # Kun visning
    EDIT = "edit"        # Kan redigere metadata (tittel, tags)
    DOWNLOAD = "download"  # Kan laste ned originale filer
```

### Permission Matrix
| Rolle | Se Delte Fotos | Del Egne Fotos | Rediger Metadata | Last Ned | Administrer Gruppe |
|-------|---------------|----------------|------------------|----------|-------------------|
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| Editor | ✅ | ✅ | ✅ | ✅ | ❌ |
| Member | ✅ | ✅ | ❌ | ⚠️* | ❌ |
| Viewer | ✅ | ❌ | ❌ | ⚠️* | ❌ |

*Avhenger av share permission satt av eier

## 🚀 Implementeringsstrategi: Gradvis Utbygging

### Fase 1: Basic User-Scoped (Ferdig)
- User modell og authentication
- Personal data isolation
- Basic multi-user API

### Fase 2: Gruppe Foundation
```python
# Legg til gruppe-tabeller
# Grunnleggende gruppe-operasjoner
# Invite-system
```

### Fase 3: Photo Sharing
```python
# SharedPhoto tabellen
# share/unshare endpoints
# Shared photo queries
```

### Fase 4: Advanced Features
```python
# Rolle-baserte permissions
# Batch sharing (hele ImportSessions)
# Gruppe-notifications
```

## 🎯 Bruksscenarier

### Scenario 1: Familie-Fotoalbum
```python
# Familie-gruppe hvor alle kan dele fotos fra familietreff
group = create_group("Andersen Familie", "Familiebilder og minner")
invite_family_members(group.invite_code)

# Mamma deler bilder fra bursdagsfest
share_photos_with_group(birthday_photos, group.id, permissions="download")
```

### Scenario 2: Fotoklubb
```python
# Fotoklubb hvor medlemmer deler sine beste bilder
club = create_group("Bergen Fotoklubb", "Månedlige foto-utfordringer")

# Kun visning som default, admin kan laste ned for utstillinger
share_photos_with_group(contest_photos, club.id, permissions="view")
```

### Scenario 3: Profesjonell Samarbeid
```python
# Fotograf deler med klient for godkjenning
client_group = create_group("Bryllup Smith 2025", "Proofs for godkjenning")

# Klient kan se, kommentere, men ikke laste ned før betaling
share_photos_with_group(wedding_proofs, client_group.id, permissions="view")
```

## 📊 Performance Considerasjoner

### Optimalisering av Shared Queries
```sql
-- Indekser for rask tilgang
CREATE INDEX idx_shared_photos_group_id ON shared_photos(group_id);
CREATE INDEX idx_shared_photos_photo_hash ON shared_photos(photo_hothash);
CREATE INDEX idx_group_members_user_id ON group_members(user_id);
CREATE INDEX idx_group_members_group_id ON group_members(group_id);

-- Composite indeks for bruker -> grupper -> fotos
CREATE INDEX idx_user_group_access ON group_members(user_id, group_id);
```

### Caching Strategy
```python
# Cache brukerens gruppe-medlemskap
@lru_cache(maxsize=1000, ttl=300)  # 5 min cache
def get_user_groups(user_id: int) -> List[int]:
    return db.query(GroupMember.group_id).filter(
        GroupMember.user_id == user_id
    ).all()
```

## ✅ Fordeler Med Denne Hybrid-Arkitekturen

1. **🔒 Standard Privacy** - Alt er privat som default
2. **🤝 Opt-in Sharing** - Deling krever aktiv valg
3. **🎯 Granular Control** - Per-foto og per-gruppe permissions
4. **📈 Skalerer Godt** - Basis user-scoped queries er raske
5. **🔧 Backward Compatible** - Kan legges til eksisterende user-scoped system
6. **👥 Fleksible Grupper** - Fra familie til profesjonelle workflows

## 🎯 Konklusjon

Denne hybrid-arkitekturen gir deg **det beste fra begge verdener**:
- **Personal ownership** som grunnprinsipp
- **Fleksibel group sharing** når ønskelig
- **Enkel migrering** fra basic user-scoped
- **Robust security** med eksplisitte permissions

Vil du at jeg skal starte implementeringen av gruppe-funksjonaliteten, eller trenger du mer detaljer om spesifikke aspekter?