# ImaLink Fase 1 - Komplett Arkitekturdokumentasjon

## 📋 Oversikt

ImaLink Fase 1 er et robuste image management system bygget med moderne arkitekturprinsipper. Systemet følger **Clean Architecture** med tydelig separasjon av lag og ansvar.

## 🏗️ Arkitektur Oversikt

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                     │
│  /api/v1/images, /api/v1/import_sessions, /api/v1/authors  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Service Layer                            │
│     ImageService, ImportSessionService, AuthorService      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  Repository Layer                          │
│   ImageRepository, ImportSessionRepository, AuthorRepository│
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Model Layer                               │
│         Image, ImportSession, Author (SQLAlchemy)          │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Prosjektstruktur

```
fase1/
├── src/                          # Hovedkildekode
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── api/                      # API endepunkter (Controller lag)
│   │   └── v1/                   # Version 1 av API
│   │       ├── images.py         # Image CRUD operasjoner
│   │       ├── import_sessions.py # Import session operasjoner
│   │       └── authors.py        # Author management
│   │
│   ├── services/                 # Business Logic lag
│   │   ├── image_service_new.py         # Image forretningslogikk
│   │   ├── import_session_service.py    # Import session forretningslogikk
│   │   ├── import_sessions_background_service.py # Background import prosessering
│   │   ├── author_service.py            # Author forretningslogikk  
│   │   ├── archive_service.py           # Arkivering og lagring
│   │   └── importing/
│   │       └── image_processor.py       # EXIF og metadata prosessering
│   │
│   ├── repositories/             # Data Access lag
│   │   ├── image_repository.py          # Image database operasjoner
│   │   ├── import_session_repository.py # Import session database operasjoner
│   │   └── author_repository.py         # Author database operasjoner
│   │
│   ├── models/                   # Database modeller (SQLAlchemy)
│   │   ├── base.py              # Base model og mixins
│   │   ├── mixins.py            # Gjenbrukbare model mixins
│   │   ├── image.py             # Image model
│   │   ├── import_session.py    # Import session model
│   │   └── author.py            # Author model
│   │
│   ├── schemas/                  # API schemas (Pydantic)
│   │   ├── common.py            # Delte response strukturer
│   │   ├── image_schemas.py     # Image API schemas
│   │   ├── requests/            # Request modeller
│   │   │   ├── author_requests.py
│   │   │   ├── import_session_requests.py
│   │   │   └── image_requests.py
│   │   └── responses/           # Response modeller
│   │       ├── author_responses.py
│   │       ├── import_session_responses.py
│   │       └── image_responses.py
│   │
│   ├── core/                    # Kjernefunksjonalitet
│   │   ├── config.py           # Applikasjonskonfigurasjon
│   │   ├── dependencies.py     # Dependency injection
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── database/               # Database konfigurasjon
│   │   └── connection.py       # Database connection og setup
│   │
│   └── utils/                  # Hjelpefunksjoner
│       ├── file_utils.py       # Fil og path utilities  
│       └── datetime_utils.py   # Dato/tid utilities
│
├── tests/                      # Unit tests og integrasjonstester
│   ├── test_exif.py          # EXIF handling tests
│   ├── test_exif_full.py     # Complete EXIF test suite
│   ├── test_image_processor.py # Image processing tests
│   └── test_routes.py        # API route tests
├── python_demos/             # Simple Python demo scripts  
│   ├── README.md             # Demo documentation
│   ├── health_demo.py        # Server health check demo
│   ├── author_demo.py        # Complete author CRUD demo
│   ├── api_demo_suite.py     # All API endpoints demo
│   ├── cli_tester.py         # Command-line demo tool
│   ├── database_debug_demo.py # Database inspection demo
│   └── run_all_demos.py      # Run all demos
├── scripts/                  # Utility scripts
│   ├── reset_database.py     # Database reset utility
│   ├── maintenance/          # Database maintenance
│   ├── migrations/           # Database migrations
│   └── debug/               # Debug utilities
├── docs/                     # Detailed documentation
│   ├── finpuss_todo.md      # Project todo items
│   ├── REFACTORING_COMPLETE.md # Refactoring notes
│   └── RELEASE_NOTES.md     # Release documentation
└── pyproject.toml           # Python project configuration
```

## 🎯 Lag og Ansvar

### 1. **API Layer** (`api/v1/`)
**Ansvar**: HTTP request/response håndtering, input validering, output formattering

- Mottar HTTP requests
- Validerer input data med Pydantic schemas  
- Kaller passende service methods
- Formaterer response data
- Håndterer HTTP status koder og exceptions

**Eksempel**:
```python
@router.get("/", response_model=PaginatedResponse[ImageResponse])
async def list_images(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    author_id: Optional[int] = Query(None),
    image_service: ImageService = Depends(get_image_service)
):
    return await image_service.get_images(offset=offset, limit=limit, author_id=author_id)
```

### 2. **Service Layer** (`services/`)
**Ansvar**: Forretningslogikk, business rules, koordinering av repositories

- Implementerer forretningsregler
- Koordinerer flere repositories
- Håndterer kompleks logikk
- Returnerer strukturerte data til API lag

**Eksempel**:
```python
class ImageService:
    def __init__(self, db: Session):
        self.image_repo = ImageRepository(db)
        self.author_repo = AuthorRepository(db)
    
    async def get_images(self, offset: int = 0, limit: int = 100, author_id: Optional[int] = None):
        # Business logic her
        images = self.image_repo.get_images(offset=offset, limit=limit, author_id=author_id)
        total = self.image_repo.count_images(author_id=author_id)
        
        return create_paginated_response(images, total, offset, limit)
```

### 3. **Repository Layer** (`repositories/`)
**Ansvar**: Database access, CRUD operasjoner, query optimization

- SQLAlchemy query operations
- Database transaction håndtering
- Data access optimization  
- Raw data til/fra database

**Eksempel**:
```python  
class ImageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_images(self, offset: int = 0, limit: int = 100, author_id: Optional[int] = None):
        query = self.db.query(Image)
        if author_id:
            query = query.filter(Image.author_id == author_id)
        return query.offset(offset).limit(limit).all()
```

### 4. **Model Layer** (`models/`)
**Ansvar**: Database schema definisjon, ORM mapping

- SQLAlchemy model definisjonene
- Database relasjonene
- Constraints og indices
- Model methods og properties

## 📊 Database Schema

### Image Model
```python
class Image(Base, TimestampMixin):
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Unique identifier
    hothash = Column(String(64), unique=True, index=True, nullable=False)
    
    # File information
    original_filename = Column(String(255), nullable=False) 
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)
    file_format = Column(String(10))
    
    # Metadata
    width = Column(Integer)
    height = Column(Integer)
    taken_at = Column(DateTime)
    
    # GPS data
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    
    # Relations
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
```

### ImportSession Model
```python
class ImportSession(Base, TimestampMixin):
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Session info
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), default="in_progress")
    
    # Import details
    source_path = Column(Text, nullable=False)
    source_description = Column(Text)
    
    # Statistics
    total_files_found = Column(Integer, default=0)
    images_imported = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    
    # Archive system  
    archive_base_path = Column(Text)
    storage_name = Column(Text)  # imalink_YYYYMMDD_uuid format
    
    # File copying
    copy_files = Column(Boolean, default=True)
    files_copied = Column(Integer, default=0)
    files_copy_skipped = Column(Integer, default=0)
```

### Author Model
```python
class Author(Base, TimestampMixin):
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Author info
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    bio = Column(Text)
    
    # Relations
    images = relationship("Image", back_populates="author")
    imports = relationship("ImportSession", back_populates="default_author")
```

## 🚀 API Endepunkter

### Images API (`/api/v1/images`)

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/` | List images med paginering og filtering |
| GET | `/{image_id}` | Hent spesifikk image |
| POST | `/` | Opprett nytt image |
| PUT | `/{image_id}` | Oppdater image metadata |
| DELETE | `/{image_id}` | Slett image |
| GET | `/recent` | Hent nylig importerte images |
| GET | `/statistics/overview` | Image statistikk |
| GET | `/author/{author_id}` | Images for spesifikk author |

### Import Sessions API (`/api/v1/import_sessions`)

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| POST | `/` | Start ny import session |
| GET | `/` | List alle import sessions |
| GET | `/{session_id}` | Hent spesifikk session |
| GET | `/status/{session_id}` | Hent session status |
| POST | `/test-single` | Test enkelt fil import |

### Authors API (`/api/v1/authors`)

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/` | List authors med paginering |
| GET | `/{author_id}` | Hent spesifikk author |
| POST | `/` | Opprett ny author |
| PUT | `/{author_id}` | Oppdater author |  
| DELETE | `/{author_id}` | Slett author |
| GET | `/search/` | Søk i authors |
| GET | `/statistics/` | Author statistikk |

## 🗃️ Arkiv System

ImaLink implementerer et robust arkivsystem med følgende filosofi:

### Storage Structure
```
Archive Base Path: /path/to/archives/
└── imalink_YYYYMMDD_uuid/          # storage_name
    ├── 2024/                       # Bevart kildestruktur
    │   ├── january/
    │   │   ├── IMG_001.jpg         # Originale filnavn
    │   │   └── IMG_002.jpg
    │   └── february/
    │       └── DSC_1234.jpg
    ├── vacation/
    │   └── beach.jpg
    ├── images_manifest.json         # Fil metadata
    └── import_session.json          # Session metadata
```

### Naming Convention
- **storage_name**: `imalink_YYYYMMDD_uuid` format  
- **Portable**: Kan finnes ved UUID søk på hvilken som helst disk
- **Structured**: Bevarer opprinnelig katalogstruktur
- **Traceable**: JSON metadata for full sporbarhet

### Metadata Files

**images_manifest.json**:
```json
{
  "created_at": "2024-10-04T14:30:22",
  "total_files": 156,
  "total_size_bytes": 2847362847,
  "files": [
    {
      "original_path": "/source/2024/january/IMG_001.jpg",
      "relative_path": "2024/january/IMG_001.jpg",
      "archive_path": "/archive/imalink_20241004_abc123/2024/january/IMG_001.jpg",
      "hothash": "abcd1234efgh5678",
      "size_bytes": 2847362,
      "width": 4032,
      "height": 3024,
      "taken_at": "2024-01-15T10:30:00"
    }
  ]
}
```

**import_session.json**:
```json
{
  "import_session_id": 42,
  "storage_name": "imalink_20241004_abc123",
  "archive_base_path": "/path/to/archives",
  "created_at": "2024-10-04T14:30:22",
  "source_path": "/source/photos",
  "source_description": "Family photos from 2024",
  "started_at": "2024-10-04T14:25:00",
  "imalink_version": "fase1",
  "storage_philosophy": "Unique archive naming with imalink_YYYYMMDD_uuid format for easy discovery and portability"
}
```

## 🔧 Konfigurasjon og Dependencies

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./imalink.db

# Storage  
DEFAULT_ARCHIVE_BASE_PATH=/path/to/archives
POOL_QUALITY=85

# API
API_VERSION=v1
DEBUG=False
```

### Dependency Injection
Systemet bruker FastAPI's dependency injection for clean separation:

```python
# core/dependencies.py
def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    return ImageService(db)

def get_import_session_service(db: Session = Depends(get_db)) -> ImportSessionService:
    return ImportSessionService(db)

def get_author_service(db: Session = Depends(get_db)) -> AuthorService:
    return AuthorService(db)
```

## 🧪 Testing Strategy

### Testing Tools
1. **Streamlit Demo Hub** (`demos/streamlit/`) - Multi-page interactive testing system
   - Homepage with demo navigation (`main.py`)
2. **Python Demo Scripts** (`python_demos/`) - Simple stdout demonstrations:
   - Health Check (`health_demo.py`) - Server connectivity demo
   - Author CRUD (`author_demo.py`) - Complete author lifecycle demo
   - API Demo Suite (`api_demo_suite.py`) - All endpoints demo
   - Database Debug (`database_debug_demo.py`) - Database inspection demo
   - Demo Runner (`run_all_demos.py`) - Automated demo execution
3. **CLI Tester** (`python_demos/cli_tester.py`) - Command-line automation
4. **Unit Tests** (`tests/`) - Automated test suite

### Test Coverage
- ✅ API endpoint testing
- ✅ Service layer business logic
- ✅ Repository data access
- ✅ Model validation
- ✅ Integration testing
- ✅ Background task testing

## 📈 Performance Considerations

### Database Optimization
- Indices på ofte brukte felt (`hothash`, `author_id`, etc.)
- Efficient queries med SQLAlchemy
- Connection pooling
- Lazy loading av relations

### File Operations  
- Asynchronous background processing for imports
- Efficient file copying med `shutil.copy2`
- Batch operations for metadata extraction
- Error resilience og retry logic

### API Performance
- Paginering på alle list endepunkter
- Efficient serialization med Pydantic
- Structured response format
- Proper HTTP status codes

## 🛡️ Error Handling

### Custom Exceptions
```python
class NotFoundError(APIException):
    """Resource not found"""
    
class DuplicateImageError(APIException):
    """Duplicate image hash detected"""
    
class ValidationError(APIException):
    """Input validation failed"""
```

### Error Response Format
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Image with ID 123 not found",
    "details": {...}
  },
  "meta": {
    "timestamp": "2024-10-04T14:30:22Z",
    "request_id": "req_abc123"
  }
}
```

## 🔮 Fremtidige Utvidelser

### Planlagte Features
- **Authentication & Authorization**: JWT basert brukerautentisering
- **Advanced Search**: Full-text søk og tagging system  
- **Image Processing**: Automatic resizing og thumbnail generering
- **API Versioning**: Support for multiple API versioner
- **Caching**: Redis basert caching for performance
- **Monitoring**: Logging, metrics og health checks

### Scalability Considerations
- Microservice arkitektur splittet
- Database sharding for store datasett
- CDN integration for image serving
- Message queue for background tasks (RabbitMQ/Redis)
- Container orchestration med Kubernetes

## 📝 Development Guidelines

### Code Standards
- **Python**: PEP 8 compliance
- **Type Hints**: Mandatory for all functions
- **Documentation**: Docstrings for all public methods
- **Imports**: Absolute imports preferred
- **Error Handling**: Explicit exception handling

### Git Workflow  
- **Feature branches**: For all new features
- **Code review**: Required for main branch
- **Semantic versioning**: For releases
- **Conventional commits**: For clear history

### Architecture Principles
1. **Single Responsibility**: Each class has one clear purpose
2. **Dependency Inversion**: Depend on abstractions, not concretions  
3. **Interface Segregation**: Small, focused interfaces
4. **DRY**: Don't Repeat Yourself
5. **SOLID**: Follow SOLID principles consistently

---

*Denne dokumentasjonen er komplett og oppdateres løpende med systemets utvikling. For spørsmål eller forslag, kontakt development team.*