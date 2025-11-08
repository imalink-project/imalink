# ImaLink Documentation

## 📚 Active Documentation

Essential documents for development and API integration:

- **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API documentation (2100+ lines)
  - All endpoints with request/response examples
  - Authentication, visibility levels, error handling
  - Photo, PhotoText, Authors, Import Sessions, etc.

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Deployment workflow
  - Local development setup
  - Production deployment to trollfjell.com
  - Database migrations with Alembic

- **[FRONTEND_VISIBILITY_IMPLEMENTATION.md](./FRONTEND_VISIBILITY_IMPLEMENTATION.md)** - Frontend integration guide
  - Phase 1 visibility implementation (4 levels)
  - PhotoText-Photo synchronization
  - UI recommendations and code examples

- **[IMALINK_WHITE_PAPER.md](./IMALINK_WHITE_PAPER.md)** - System vision and philosophy
  - Core principles and architecture overview
  - Target users and key differentiators

## 🗂️ Organized Documentation

### [`multiuser/`](./multiuser/)
Multi-user architecture strategies and analysis:
- User administration patterns
- Clean start strategy for multi-user
- User groups and coordination

### [`features/`](./features/)
Specific feature documentation:
- Database stats endpoint
- (Future feature docs go here)

### [`archive/`](./archive/)
Historical planning and implementation documents:

#### [`archive/planning/`](./archive/planning/)
- `OPPSUMMERING_START_PRODUKSJON.md` - Production readiness checklist
- `SHARING_ARCHITECTURE_ANALYSIS.md` - Sharing architecture analysis
- `FRONTEND_INTEGRATION.md` - Old frontend guide (superseded by FRONTEND_VISIBILITY_IMPLEMENTATION.md)

#### [`archive/implementation/`](./archive/implementation/)
- `HYBRID_HOTHASH_IMPLEMENTATION_PLAN.md` - ✅ Completed: Hybrid ID implementation
- `PHOTO_AND_IMAGEFILE_MODEL.md` - Photo vs ImageFile architecture details
- `PHOTO_COLLECTION_SYSTEM.md` - Collection system details
- `PHOTO_SEARCH_IMPLEMENTATION.md` - Search implementation details
- `PHOTO_SEARCH_RULES.md` - Search rules and filters

## 🏗️ Architecture Overview

ImaLink follows a clean layered architecture:

```
API Layer (FastAPI)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Models (SQLAlchemy ORM)
    ↓
PostgreSQL Database
```

### Key Concepts

**Photo vs ImageFile:**
- `Photo` = The visual subject/moment (what users see)
- `ImageFile` = Physical file on disk (can have multiple per photo)
- Photos are identified by `hothash` (SHA256 of 150x150 thumbnail)

**Visibility System (Phase 1):**
- `private` - Owner only (default)
- `space` - Space members (Phase 2 - not yet functional)
- `authenticated` - All logged-in users
- `public` - Everyone including anonymous

**Author System:**
- Authors are **shared metadata tags** (not user-scoped)
- Used to identify who took a photo
- Photo ownership via `Photo.user_id`, not Author
- All users can view all authors

**User Ownership:**
- Most resources owned by users: `Photo.user_id`, `ImageFile.user_id`, etc.
- Complete data isolation between users
- Exception: Authors (shared metadata)

## 📖 Quick Links

- **Start here:** [API_REFERENCE.md](./API_REFERENCE.md) for API usage
- **Deploying?** [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Frontend dev?** [FRONTEND_VISIBILITY_IMPLEMENTATION.md](./FRONTEND_VISIBILITY_IMPLEMENTATION.md)
- **Understanding the vision?** [IMALINK_WHITE_PAPER.md](./IMALINK_WHITE_PAPER.md)

## 🔄 Recent Updates

**November 8, 2025:**
- ✅ Author simplification: Authors are now shared metadata tags
- ✅ Visibility Phase 1: 4-level visibility system implemented
- ✅ PhotoText-Photo sync: Documents automatically sync visibility to referenced photos
- ✅ Anonymous access: Public content viewable without authentication
- ✅ Documentation reorganized into logical structure
