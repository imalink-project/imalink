# Imalink Sharing Architecture - Markedsanalyse og Design

**Dato:** 7. november 2025  
**Formål:** Analysere eksisterende løsninger og designe en forfatter-sentrert delingsarkitektur

---

## Executive Summary

Imalink posisjonerer seg som et **forfatter-sentrert visual storytelling verktøy** med kontrollert deling og samarbeid. Analysen viser at det finnes et gap mellom sosiale medieplattformer (500px, Behance) og klient-fokuserte verktøy (SmugMug, Pixieset). Imalinks unike kombinasjon av PhotoText-narrativer, content-addressable storage og workspace-basert samarbeid kan fylle denne nisjen.

**Anbefaling:** Implementer i to faser - Basic Visibility → Spaces

---

## 1. Markedsanalyse

### 1.1 SmugMug (Profesjonelle fotografer)

**Target audience:** Profesjonelle fotografer som selger til klienter  
**Prising:** $7-$47/måned  
**Brukere:** ~200,000 betalende fotografer

**Delingsfunksjoner:**
- ✅ Private gallerier (password-protected)
- ✅ Public gallerier (åpen URL)
- ✅ "Unlisted" gallerier (kun de med link)
- ✅ Client proofing (kunder kan velge favorittbilder)
- ✅ Salg/e-handel integrert

**Styrker:**
- Fotografen har full kontroll
- Enkel privat/public toggle
- Godt etablert i profesjonelt marked
- Pålitelig hosting (ikke komprimering)

**Svakheter:**
- ❌ Ingen fotograf-til-fotograf samarbeid
- ❌ Ingen space/gruppe-konsept
- ❌ Ingen narrative/story format utover gallerier
- ❌ Begrenset EXIF/metadata håndtering
- ❌ Ingen RAW-fil støtte

**Imalink differensiering:**
- PhotoText for storytelling (ikke bare gallerier)
- Spaces for fotograf-samarbeid
- Content-addressable storage (deduplisering)
- Fullstendig RAW + JPEG støtte

---

### 1.2 500px (Fotograf-community)

**Target audience:** Entusiastfotografer og semi-profesjonelle  
**Prising:** Gratis + $4-$13/måned for premium  
**Brukere:** ~15 millioner registrerte

**Delingsfunksjoner:**
- ✅ Public portfolio (alle ser)
- ✅ Private uploads (kun deg)
- ✅ Licensing marketplace
- ✅ Pulse/Activity feed
- ❌ Likes, comments, follows (sosialt medium)

**Styrker:**
- Stort community for exposure
- Lisensieringsmuligheter
- Quest/challenges for engasjement

**Svakheter:**
- ❌ **For sosialt** - likes/follows driver plattformen
- ❌ Fotografen mister kontroll (algoritme-drevet)
- ❌ Ingen granulær tilgangskontroll
- ❌ Komprimering av bilder
- ❌ Ingen samarbeids-spaces
- ❌ Ingen story/narrative format

**Imalink differensiering:**
- **Null sosiale features** - rent forfatter-verktøy
- Fotografen kontrollerer alt (ikke algoritme)
- Granulær tilgang (private/space/authenticated/public)
- PhotoText for visuell storytelling

---

### 1.3 Notion (Collaborative workspace)

**Target audience:** Teams, knowledge workers  
**Prising:** Gratis + $8-$15/bruker/måned  
**Brukere:** ~30 millioner (Sept 2024)

**Delingsfunksjoner:**
- ✅ Private pages (kun deg)
- ✅ Team workspaces (kolleger)
- ✅ Public pages (hvem som helst)
- ✅ Invite-only pages (spesifikke folk)
- ✅ Granulære permissions (view/comment/edit)

**Arkitektur (direkte sammenlignbar med Imalink):**
```
Notion Page         → Imalink Photo/PhotoText
Workspace           → Space
Public publishing   → Public visibility
Team access         → Authenticated visibility
```

**Styrker:**
- ✅ **Private-by-default** (exact samme filosofi)
- ✅ Workspace-konsept som skalerer
- ✅ Granulære permissions
- ✅ Veldig intuitiv delingsmodell

**Svakheter (for vårt formål):**
- ❌ Ikke laget for visuelt innhold
- ❌ Ingen metadata/EXIF håndtering
- ❌ Ingen deduplisering av assets
- ❌ Svak bildebehandling

**Imalink kan kopiere:**
- ✅ Private-by-default filosofi
- ✅ Workspace (Space) struktur
- ✅ Permissions-modell (view/edit)
- ✅ Invite workflow

**Imalink differensiering:**
- Optimalisert for visuelt innhold
- Content-addressable storage
- PhotoText narrative format
- EXIF/metadata-sentrert

---

### 1.4 Figma (Design collaboration)

**Target audience:** Designere, produktteam  
**Prising:** Gratis + $12-$45/bruker/måned  
**Brukere:** ~4 millioner (2023)

**Delingsfunksjoner:**
- ✅ Private files (kun deg)
- ✅ Team projects (delt workspace)
- ✅ Link sharing (view/edit permissions)
- ✅ Public files (showcase)
- ✅ Real-time collaboration

**Styrker:**
- View vs Edit permissions (som vi planlegger)
- Team = Space konsept
- **Profesjonelt, ikke sosialt** (exact samme filosofi)
- Meget godt onboarding

**Svakheter (for vårt formål):**
- ❌ Ingen metadata håndtering
- ❌ Raster images er sekundært (vector-fokus)

**Imalink kan kopiere:**
- ✅ View/Edit permission split
- ✅ Team-basert samarbeid
- ✅ Link sharing (kanskje i fremtiden)
- ✅ Profesjonell, ikke-sosial approach

---

### 1.5 Adobe Portfolio / Behance

**Target audience:** Kreative profesjonelle  
**Prising:** Inkludert i Creative Cloud ($54/måned)  
**Brukere:** Behance ~10 millioner

**Delingsfunksjoner:**
- ✅ Portfolio (public showcase)
- ✅ Work-in-progress (private)
- ✅ Client review (password-protected)
- ❌ Behance: Likes, comments, follows

**Styrker:**
- Case study format (lik PhotoText)
- Profesjonell presentasjon
- Creative Cloud integrasjon

**Svakheter:**
- ❌ Behance er **for sosialt** (likes driver alt)
- ❌ Ingen spaces/collaboration
- ❌ Adobe-økosystem lock-in
- ❌ Komprimering av bilder

**Imalink differensiering:**
- Ikke sosialt
- Standalone (ikke del av større suite)
- Content-addressable storage
- RAW support

---

### 1.6 Pixieset (Fotograf-klient sharing)

**Target audience:** Event/bryllupsfotografer  
**Prising:** $8-$40/måned  
**Brukere:** ~60,000 fotografer

**Delingsfunksjoner:**
- ✅ Client galleries (password-protected)
- ✅ Store front (public)
- ✅ Proofing (klient velger favoritter)
- ✅ Salg/nedlasting kontroll

**Styrker:**
- Fotografen kontrollerer alt
- Privat deling med klienter
- Godt salgsverktøy

**Svakheter:**
- ❌ Ingen story/narrative format
- ❌ **Ingen fotograf-til-fotograf samarbeid**
- ❌ Ingen spaces
- ❌ Fokus kun på klient-levering

**Imalink differensiering:**
- PhotoText storytelling
- Fotograf-samarbeid via Spaces
- Ikke primært salgsverktøy
- Metadata/EXIF fokus

---

## 2. Gap-analyse

### 2.1 Markedsgap

| Kategori | Eksisterende | Imalink fyller gap |
|----------|--------------|-------------------|
| **Fotograf → Klient** | SmugMug, Pixieset | ❌ Ikke vårt fokus |
| **Fotograf → Allmenheten** | 500px, Behance | ✅ Men uten sosiale features |
| **Fotograf → Fotograf** | ❌ **GAP** | ✅ Spaces |
| **Visual storytelling** | Medium (tekst-fokus) | ✅ PhotoText |
| **Professional collaboration** | Figma (design), Notion (tekst) | ✅ Men for visuelt innhold |

### 2.2 Unik posisjonering

```
Imalink = PhotoText narratives + Content-addressable storage + Workspace collaboration
```

**Ingen konkurrent kombinerer disse tre elementene.**

---

## 3. Delingsarkitektur - Design

### 3.1 Core prinsipper

1. **Private-by-default** - Alt innhold starter privat
2. **Explicit sharing** - Må aktivt velge å dele
3. **Granular control** - Fire nivåer av tilgang
4. **Author-centric** - Forfatteren eier og kontrollerer alt
5. **No social features** - Ingen likes, comments, feeds
6. **Audit trail** - Logg alle tilgangsendringer

### 3.2 Visibility levels

```python
class VisibilityLevel(Enum):
    PRIVATE = "private"          # Kun eier
    SPACE = "space"              # Medlemmer av spesifikke spaces
    AUTHENTICATED = "authenticated"  # Alle innloggede brukere
    PUBLIC = "public"            # Alle (også anonyme)
```

**Anvendelse:**
- `Photo.visibility`
- `PhotoTextDocument.visibility`

**Default:** `PRIVATE`

**Logikk:**
- `private`: Kun eier ser innholdet
- `space`: Kun medlemmer av spaces hvor innholdet er delt
- `authenticated`: Alle innloggede imalink-brukere (community-deling)
- `public`: Alle inkludert anonyme besøkende (SEO, markedsføring)

**Relasjon til Spaces:**
- Når `visibility = "space"`, må innholdet knyttes til ett eller flere spaces via `photo_space_memberships` tabell
- Space-medlemskap gir IKKE automatisk tilgang til eierens øvrige innhold
- Hvert innhold må eksplisitt deles til space(s)

### 3.3 Database-modeller

#### Space (Delt arbeidsrom)

```python
class Space(Base, TimestampMixin):
    """
    Shared workspace for photographer collaboration
    
    Spaces allow multiple users to see each other's content
    that has been explicitly shared to the space.
    
    Use cases:
    - Photography collective
    - Client project workspace
    - Museum/archive collaboration
    - Event coverage team
    """
    __tablename__ = "spaces"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Space ownership
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Visibility of space itself
    is_discoverable = Column(Boolean, default=False, nullable=False)
    # If true, other users can request to join
    
    # Relationships
    owner = relationship("User", back_populates="owned_spaces")
    members = relationship("SpaceMember", back_populates="space", cascade="all, delete-orphan")
```

#### SpaceMember (Medlemskap i space)

```python
class SpaceMember(Base, TimestampMixin):
    """
    Membership in a space
    
    Roles:
    - owner: Can delete space, manage members, share content
    - admin: Can manage members, share content
    - member: Can share content to space
    - viewer: Can only view shared content
    """
    __tablename__ = "space_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    space_id = Column(Integer, ForeignKey('spaces.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    role = Column(String(20), nullable=False, default='member')
    # Roles: owner, admin, member, viewer
    
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    space = relationship("Space", back_populates="members")
    user = relationship("User", back_populates="space_memberships")
    
    # Constraints
    __table_args__ = (
        # One membership per user per space
        UniqueConstraint('space_id', 'user_id', name='unique_space_membership'),
        CheckConstraint("role IN ('owner', 'admin', 'member', 'viewer')", name='valid_space_role'),
    )
```

#### PhotoSpaceMembership (Innhold delt til spaces)

```python
class PhotoSpaceMembership(Base, TimestampMixin):
    """
    Links photos to spaces when visibility = 'space'
    
    Allows photos to be in multiple spaces simultaneously.
    """
    __tablename__ = "photo_space_memberships"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    photo_id = Column(Integer, ForeignKey('photos.id', ondelete='CASCADE'), nullable=False, index=True)
    space_id = Column(Integer, ForeignKey('spaces.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Who added this photo to the space
    added_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    photo = relationship("Photo", back_populates="space_memberships")
    space = relationship("Space")
    added_by = relationship("User")
    
    # Constraints
    __table_args__ = (
        # Photo can only be in a space once
        UniqueConstraint('photo_id', 'space_id', name='unique_photo_space'),
    )
```

#### PhotoTextSpaceMembership (Dokumenter delt til spaces)

```python
class PhotoTextSpaceMembership(Base, TimestampMixin):
    """
    Links PhotoText documents to spaces when visibility = 'space'
    """
    __tablename__ = "phototext_space_memberships"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    document_id = Column(Integer, ForeignKey('phototext_documents.id', ondelete='CASCADE'), nullable=False, index=True)
    space_id = Column(Integer, ForeignKey('spaces.id', ondelete='CASCADE'), nullable=False, index=True)
    
    added_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    document = relationship("PhotoTextDocument", back_populates="space_memberships")
    space = relationship("Space")
    added_by = relationship("User")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('document_id', 'space_id', name='unique_document_space'),
    )
```

#### Endringer til Photo model

```python
class Photo(Base, TimestampMixin):
    # ... existing fields ...
    
    # Sharing controls
    visibility = Column(String(20), nullable=False, default='private', index=True)
    # Values: private, space, authenticated, public
    
    # Relationships
    space_memberships = relationship("PhotoSpaceMembership", back_populates="photo", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('private', 'space', 'authenticated', 'public')",
            name='valid_photo_visibility'
        ),
    )
```

#### Endringer til PhotoTextDocument model

```python
class PhotoTextDocument(Base, TimestampMixin):
    # ... existing fields ...
    
    # Sharing controls
    visibility = Column(String(20), nullable=False, default='private', index=True)
    # Values: private, space, authenticated, public
    
    # Relationships
    space_memberships = relationship("PhotoTextSpaceMembership", back_populates="document", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        # ... existing constraints ...
        CheckConstraint(
            "visibility IN ('private', 'space', 'authenticated', 'public')",
            name='valid_document_visibility'
        ),
    )
```

---

## 4. Tilgangskontroll-logikk

### 4.1 Photo access check

```python
def can_view_photo(photo: Photo, user: Optional[User], user_space_ids: Optional[List[int]] = None) -> bool:
    """
    Determine if user can view photo
    
    Rules:
    1. Owner can always see own photos
    2. Public photos visible to everyone (including anonymous)
    3. Authenticated photos visible to all logged-in users
    4. Space photos visible to space members
    5. Private photos only visible to owner
    """
    # Public - anyone can see
    if photo.visibility == "public":
        return True
    
    # Authenticated - all logged-in users
    if photo.visibility == "authenticated" and user is not None:
        return True
    
    # Must be authenticated for remaining checks
    if user is None:
        return False
    
    # Owner always sees own content
    if photo.user_id == user.id:
        return True
    
    # Space - check membership
    if photo.visibility == "space":
        if user_space_ids is None:
            # Fetch user's space IDs (should be cached in practice)
            user_space_ids = get_user_space_ids(user.id)
        
        # Get photo's space IDs
        photo_space_ids = [psm.space_id for psm in photo.space_memberships]
        
        # Check if any overlap
        if set(user_space_ids) & set(photo_space_ids):
            return True
    
    # Private - only owner
    return False
```

**Performance optimization:**
- Cache `user_space_ids` in session/Redis
- Index on `photo_space_memberships(photo_id)` and `photo_space_memberships(space_id)`
- For listing queries, pre-fetch user's space IDs once

def can_edit_photo(photo: Photo, user: User) -> bool:
    """
    Determine if user can edit photo
    
    Rules:
    1. Owner can always edit
    2. Space members cannot edit (view only)
    3. Only owner can change visibility or delete
    """
    # Only owner can edit
    return photo.user_id == user.id
```

### 4.2 Query filtering

```python
def get_photos_for_user(user: Optional[User], user_space_ids: Optional[List[int]] = None):
    """
    Get all photos user has access to
    
    For anonymous users: Only public
    For authenticated users: Own + authenticated + public + space photos
    """
    query = db.query(Photo)
    
    if user is None:
        # Anonymous - only public
        query = query.filter(Photo.visibility == "public")
    else:
        # Cache user's space IDs
        if user_space_ids is None:
            user_space_ids = get_user_space_ids(user.id)
        
        # Authenticated user sees:
        query = query.filter(
            or_(
                Photo.user_id == user.id,                    # Own photos
                Photo.visibility == "public",                # Public photos
                Photo.visibility == "authenticated",         # Authenticated photos
                and_(                                         # Space photos
                    Photo.visibility == "space",
                    Photo.id.in_(
                        select(PhotoSpaceMembership.photo_id).where(
                            PhotoSpaceMembership.space_id.in_(user_space_ids)
                        )
                    )
                )
            )
        )
    
    # Apply additional filters...
    return query.all()
```

---

## 5. Implementeringsplan

### Fase 1: Basic Visibility (2-3 uker) - PRIORITERT

**Scope:** Fire-nivå visibility system

**Visibility levels:**
- `private` - Kun eier
- `space` - Space-medlemmer (krever space-infrastruktur)
- `authenticated` - Alle innloggede brukere
- `public` - Alle inkludert anonyme

**Database changes:**
- Add `visibility` field to Photo (default='private', VARCHAR(20))
- Add `visibility` field to PhotoTextDocument (default='private', VARCHAR(20))
- CHECK constraint for valid values
- Migration script

**API changes:**
- Update Photo/PhotoText creation endpoints (accept optional visibility)
- Update Photo/PhotoText update endpoints (change visibility)
- Filter all GET endpoints by visibility + user
- Add `get_current_user_optional` dependency for anonymous access
- Endpoints support both authenticated and anonymous requests

**Access control:**
- `can_view_photo(photo, user, user_space_ids)` utility
- `can_edit_photo(photo, user)` utility (owner only)
- Repository methods accept `Optional[User]`

**Frontend changes:**
- Visibility dropdown UI (Private/Authenticated/Public)
- Space option disabled until Phase 3
- Warning når man publiserer
- Public gallery view (no auth required)
- Authenticated community gallery (requires login)

**Performance:**
- Index on visibility column
- Cache user_space_ids in session (for future Phase 3)

**Testing:**
- Owner sees all own content
- Anonymous sees only public
- Authenticated users see own + authenticated + public
- Changing visibility updates access immediately

**Deliverable:** Brukere kan publisere til community eller hele verden

---

### Fase 2: Spaces Infrastructure (4-5 uker)

**Scope:** Opprett delte workspaces

**Database changes:**
- Create `spaces` table
- Create `space_members` table
- Create `photo_space_memberships` table
- Create `phototext_space_memberships` table

**API changes:**
- Space CRUD operations
  - POST /api/v1/spaces (create)
  - GET /api/v1/spaces (list my spaces)
  - GET /api/v1/spaces/{id} (get space details)
  - PUT /api/v1/spaces/{id} (update)
  - DELETE /api/v1/spaces/{id} (delete)
- Space membership
  - POST /api/v1/spaces/{id}/members (invite user)
  - DELETE /api/v1/spaces/{id}/members/{user_id} (remove)
  - GET /api/v1/spaces/{id}/members (list members)
- Share to space
  - POST /api/v1/photos/{hash}/spaces (add to space)
  - DELETE /api/v1/photos/{hash}/spaces/{space_id} (remove from space)
  - GET /api/v1/photos/{hash}/spaces (list spaces photo is in)
  - Same for PhotoText documents
- Space content
  - GET /api/v1/spaces/{id}/photos (all photos shared to space)
  - GET /api/v1/spaces/{id}/documents (all documents shared to space)
- Enable `visibility=space` in Photo/PhotoText endpoints

**Access control:**
- Update `can_view_photo()` to check space memberships
- Cache `user_space_ids` in session/Redis
- Efficient JOIN queries with proper indexes

**Frontend changes:**
- Space creation wizard
- Space list view
- Space detail view (members + content)
- "Share to spaces" multi-select UI
- Member management
- Enable "Space" option in visibility dropdown

**Testing:**
- Space creation
- Invite/remove members
- Share content to multiple spaces
- All space members see shared content
- Non-members don't see content
- Space deletion doesn't delete content (orphan handling)
- Photo can be in multiple spaces

**Deliverable:** Gruppesamarbeid i delte rom

---

### Fase 3: Future Extensions

**Mulige fremtidige features (ikke planlagt nå):**
- Direct user-to-user sharing (individuell deling)
- Comments/annotations på bilder
- Activity feed for spaces

---

## 6. Sikkerhet

### 6.1 Prinsipper

1. **Default deny** - Ingen tilgang med mindre eksplisitt gitt
2. **User isolation** - Query må alltid sjekke tilgang
3. **No enumeration** - Ikke avslør eksistens av private ressurser
4. **Audit logging** - Logg alle tilgangsendringer
5. **Explicit revocation** - Enkel å fjerne tilgang

### 6.2 Trusler og mitigering

| Trussel | Mitigering |
|---------|-----------|
| **Unauthorized access** | Tilgangskontroll i alle endpoints |
| **Enumeration attacks** | 404 for både "ikke eksisterer" og "ingen tilgang" |
| **Token hijacking** | JWT expiry + refresh tokens |
| **Space takeover** | Kun owner kan slette space |
| **Content leak via API** | Filtrer hotpreview/coldpreview basert på tilgang |

### 6.3 Privacy

- **GDPR compliance:** User kan slette all sin data
- **Content ownership:** Bruker eier alltid sitt innhold
- **Data portability:** Export API for all brukerdata
- **Right to be forgotten:** Cascade delete ved bruker-sletting

---

## 7. Konkurransefortrinn

### 7.1 Tekniske fortrinn

1. **Content-addressable storage**
   - Automatic deduplisering
   - JPEG + RAW support
   - Ingen komprimering

2. **PhotoText narrative format**
   - Strukturert storytelling
   - Image collages
   - Ingen andre har dette

3. **Metadata-first approach**
   - Full EXIF støtte
   - GPS/tidsinformasjon
   - Corrections uten å endre original

4. **Workspace collaboration**
   - Spaces for team samarbeid
   - Granulære permissions
   - Ikke sosialt medium

### 7.2 Forretningsfortrinn

1. **Nisje-posisjonering**
   - Profesjonelle fotografer + kulturinstitusjoner
   - Ikke konkurrer direkte med SmugMug (klient-levering)
   - Ikke konkurrer med 500px (sosialt)

2. **Privacy-focused**
   - Private-by-default
   - Forfatter har full kontroll
   - Ingen algoritme

3. **Open for integrations**
   - API-first design
   - Kan integreres med andre verktøy
   - Kan bygge egne frontend

---

## 8. Risiko og utfordringer

### 8.1 Tekniske risikoer

| Risiko | Sannsynlighet | Impact | Mitigering |
|--------|---------------|--------|------------|
| Storage kostnader | Høy | Høy | Start med limit per bruker |
| Performance (query complexity) | Medium | Medium | Database indexes, caching |
| Skalerbarhet | Lav | Høy | Postgres skalerer godt, CDN for bilder |

### 8.2 Business risikoer

| Risiko | Sannsynlighet | Impact | Mitigering |
|--------|---------------|--------|------------|
| Liten brukerbase (network effects) | Høy | Høy | Start med nisje, bygg community |
| Discovery problem | Høy | Medium | Featured spaces, search, tags |
| Konkurranse fra etablerte | Medium | Medium | Differensierer med PhotoText + RAW |

### 8.3 Product risikoer

| Risiko | Sannsynlighet | Impact | Mitigering |
|--------|---------------|--------|------------|
| For komplekst (feature creep) | Medium | Høy | Start minimalt (3 faser) |
| Brukere vil ha sosiale features | Medium | Medium | Test med early adopters |
| Space-konsept ikke intuitivt | Lav | Medium | God onboarding, clear UX |

---

## 9. Go-to-Market strategi

### 9.1 Target segments

**Primær (Fase 1-2):**
- Profesjonelle fotografer (dokumentar, reportasje)
- Fotojournalister
- Museums/arkiv-fotografer

**Sekundær (Fase 3):**
- Photography collectives
- Universiteter/forskningsprosjekter
- Event coverage teams

### 9.2 Early adopter validering

**Before full implementation:**
1. Bygg Fase 1 (Basic Visibility)
2. Rekrutter 10-15 beta-testere:
   - 5 profesjonelle fotografer
   - 2-3 fotojournalister
   - 2 museums/arkiv-ansatte
3. Gi gratis tilgang i 3 måneder
4. Samle feedback:
   - Bruker de visibility features?
   - Ønsker de Spaces?
   - Hva mangler?

**Success criteria:**
- ✅ 70%+ aktive brukere etter 1 måned
- ✅ Minst 3 brukere publiserer offentlig
- ✅ Minst 2 brukere ber om Spaces
- ✅ NPS score > 40

**If criteria not met:** Pivot eller juster før Fase 2

### 9.3 Pricing (fremtidig)

**Freemium model:**
- Free tier: 5 GB storage, unlimited private photos
- Pro tier ($10/måned): 100 GB, spaces
- Team tier ($25/bruker/måned): Unlimited storage, priority support

---

## 10. Konklusjon

### 10.1 Skal vi fortsette?

**✅ JA - Her er hvorfor:**

1. **Markedsgap eksisterer**
   - Ingen kombinerer PhotoText + Collaboration + Content-addressable storage
   - Gap mellom sosiale plattformer og klient-verktøy

2. **Proven patterns**
   - Notion beviste workspace-modell
   - Figma beviste profesjonelt samarbeid
   - GitHub beviste private-by-default

3. **Differensiert tilbud**
   - PhotoText er unikt
   - RAW support er sjeldent
   - Privacy-fokus er populært

4. **Implementerbart**
   - Tre klare faser
   - Kan valideres inkrementelt
   - Teknisk gjennomførbart

### 10.2 Anbefalt fremgangsmåte

1. **Implementer Fase 1** (2-3 uker)
   - Basic visibility (private/public)
   - Deploy til beta-testere

2. **Valider konsept** (1 måned)
   - 10-15 beta-testere
   - Samle feedback
   - Mål success criteria

3. **Hvis validering OK:**
   - Implementer Fase 2 (Spaces)
   - Utvid beta-test
   - Iterér basert på feedback

4. **Hvis validering feiler:**
   - Analyser hvorfor
   - Pivot eller juster
   - Test på nytt

### 10.3 Neste steg

**Umiddelbart:**
1. Review dette dokumentet
2. Diskuter fase-plan
3. Bestem: Skal vi starte Fase 1?

**Hvis ja:**
1. Design database migration for visibility field
2. Implementer tilgangskontroll-logikk
3. Oppdater API endpoints
4. Bygg frontend UI for visibility toggle

---

## Appendiks A: Sammenligning-matrise

| Feature | Imalink | SmugMug | 500px | Notion | Figma | Pixieset |
|---------|---------|---------|-------|--------|-------|----------|
| Private-by-default | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Public publishing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Workspace/Spaces | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Direct collaboration | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Granular permissions | ✅ | ⚠️ | ❌ | ✅ | ✅ | ⚠️ |
| PhotoText/Stories | ✅ | ❌ | ❌ | ⚠️ | ❌ | ❌ |
| RAW support | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| No compression | ✅ | ✅ | ❌ | N/A | N/A | ⚠️ |
| Content-addressable | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| EXIF metadata | ✅ | ⚠️ | ⚠️ | ❌ | ❌ | ⚠️ |
| Social features | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| E-commerce | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |

**Legend:**
- ✅ Full support
- ⚠️ Partial support
- ❌ Not supported
- N/A Not applicable

---

## Appendiks B: Referanser

1. **SmugMug:** https://www.smugmug.com/ (Besøkt Nov 2025)
2. **500px:** https://500px.com/ (Besøkt Nov 2025)
3. **Notion:** https://www.notion.so/ (Besøkt Nov 2025)
4. **Figma:** https://www.figma.com/ (Besøkt Nov 2025)
5. **Pixieset:** https://pixieset.com/ (Besøkt Nov 2025)
6. **PhotoText:** https://github.com/kjelkols/phototext (Utviklet 2025)
7. **Imalink-core:** https://github.com/kjelkols/imalink-core (Utviklet 2025)

---

**Dokument versjon:** 1.0  
**Sist oppdatert:** 7. november 2025  
**Forfatter:** AI Analysis (GitHub Copilot) + Kjell Kolstad  
**Status:** Preliminary analysis - Awaiting decision on Fase 1 implementation
