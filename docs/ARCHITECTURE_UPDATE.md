# ImaLink Architecture v2.0 - Multi-User System

## 🏗️ System Overview

ImaLink v2.0 introduces a complete multi-user authentication system with user-scoped data isolation while maintaining the core image-first philosophy.

### Core Principles

1. **🔐 User Isolation**: Complete data separation between users
2. **🖼️ Image-First Architecture**: ImageFiles drive Photo creation
3. **🔗 Clear Upload Paths**: Distinct endpoints for new photos vs companion files
4. **🔒 JWT Authentication**: Secure token-based authentication
5. **📱 Frontend-Ready**: Clean API design for modern frontend frameworks

## 🗃️ Database Schema

### User System
```sql
-- Users table (new)
users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL, 
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME,
  updated_at DATETIME
)

-- All existing tables now have user_id foreign key:
-- photos.user_id -> users.id
-- authors.user_id -> users.id  
-- import_sessions.user_id -> users.id
```

### Core Image Schema
```sql
-- Photos: Visual representation and metadata
photos (
  hothash VARCHAR(64) PRIMARY KEY,        -- SHA256 of hotpreview
  user_id INTEGER REFERENCES users(id),   -- NEW: User ownership
  title VARCHAR(255),
  description TEXT,
  tags JSON,                              -- ["landscape", "sunset"]
  rating INTEGER,                         -- 1-5 stars
  taken_at DATETIME,                      -- From EXIF
  gps_latitude DECIMAL(10,8),            -- From EXIF
  gps_longitude DECIMAL(11,8),           -- From EXIF
  author_id INTEGER REFERENCES authors(id),
  created_at DATETIME,
  updated_at DATETIME
)

-- ImageFiles: Physical file records  
image_files (
  id INTEGER PRIMARY KEY,
  photo_hothash VARCHAR(64) REFERENCES photos(hothash),
  filename VARCHAR(255) NOT NULL,         -- "IMG_001.jpg"
  file_size INTEGER,                      -- Bytes
  hotpreview BLOB,                        -- Thumbnail binary data
  perceptual_hash VARCHAR(16),            -- For similarity search
  exif_dict JSON,                         -- Full EXIF data
  import_session_id INTEGER REFERENCES import_sessions(id),
  imported_time DATETIME,
  imported_info JSON,                     -- Import context
  local_storage_info JSON,               -- Storage details
  cloud_storage_info JSON,               -- Cloud storage details
  created_at DATETIME,
  updated_at DATETIME
)

-- Authors: Photographers (user-scoped)
authors (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),   -- NEW: User ownership
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  bio TEXT,
  created_at DATETIME,
  updated_at DATETIME
)

-- Import Sessions: Batch import tracking (user-scoped)  
import_sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),   -- NEW: User ownership
  name VARCHAR(255) NOT NULL,
  source_path TEXT,
  description TEXT,
  status VARCHAR(50) DEFAULT 'pending',
  total_files INTEGER DEFAULT 0,
  processed_files INTEGER DEFAULT 0,
  created_at DATETIME,
  updated_at DATETIME
)
```

## 🔄 Upload Flow Architecture

### Two Clear Upload Paths

#### Path 1: New Photo Upload
```
POST /api/v1/image-files/new-photo
├── Validate: hotpreview required
├── Generate: photo_hothash = SHA256(hotpreview) 
├── Check: Photo with hothash exists?
├── ❌ If exists → Error 409 "Use add-to-photo"
└── ✅ If new → Create Photo + ImageFile
```

#### Path 2: Companion File Upload  
```
POST /api/v1/image-files/add-to-photo
├── Validate: photo_hothash required
├── Check: Photo exists and user owns it?
├── ❌ If not found → Error 404 "Photo not found"
└── ✅ If found → Create ImageFile only
```

### Data Flow Example
```
1. User uploads IMG_001.jpg → new-photo
   ├── Creates Photo(hothash="abc123...")
   └── Creates ImageFile(filename="IMG_001.jpg", photo_hothash="abc123...")

2. User uploads IMG_001.CR3 → add-to-photo  
   └── Creates ImageFile(filename="IMG_001.CR3", photo_hothash="abc123...")

Result: One Photo with two ImageFiles (JPEG + RAW)
```

## 🔐 Authentication Architecture

### JWT Token Flow
```
1. POST /auth/register → Create user account
2. POST /auth/login → Get JWT token
3. All API calls → Include "Authorization: Bearer <token>"
4. Token validation → Extract user_id for data scoping
```

### User Isolation Strategy
```python
# Repository Pattern with User Scoping
class PhotoRepository:
    def get_photos(self, user_id: int, offset: int, limit: int):
        return self.db.query(Photo).filter(
            Photo.user_id == user_id
        ).offset(offset).limit(limit).all()
    
    def create(self, photo_data: PhotoCreateRequest, user_id: int):
        photo_data.user_id = user_id  # Force user ownership
        return super().create(photo_data)
```

### Security Layers
1. **API Layer**: JWT token validation
2. **Service Layer**: User context passing  
3. **Repository Layer**: user_id filtering
4. **Database Layer**: Foreign key constraints

## 📁 Project Structure

```
src/
├── main.py                    # FastAPI application entry
├── api/                       # API endpoints
│   ├── auth.py               # Authentication endpoints
│   ├── users.py              # User management  
│   ├── v1/
│   │   ├── photos.py         # Photo CRUD (user-scoped)
│   │   ├── image_files.py    # ImageFile upload endpoints
│   │   ├── authors.py        # Author CRUD (user-scoped)
│   │   └── import_sessions.py # Import tracking (user-scoped)
├── core/                      # Configuration and dependencies
│   ├── config.py             # App configuration
│   ├── dependencies.py       # Dependency injection
│   └── security.py           # JWT token handling
├── models/                    # SQLAlchemy models
│   ├── user.py               # User model
│   ├── photo.py              # Photo model (with user_id)
│   ├── image_file.py         # ImageFile model
│   ├── author.py             # Author model (with user_id)
│   └── import_session.py     # ImportSession model (with user_id)
├── repositories/              # Data access layer
│   ├── user_repository.py    # User data access
│   ├── photo_repository.py   # Photo data access (user-scoped)
│   ├── image_file_repository.py # ImageFile data access
│   ├── author_repository.py  # Author data access (user-scoped)
│   └── import_session_repository.py # ImportSession (user-scoped)
├── services/                  # Business logic layer
│   ├── auth_service.py       # Authentication logic
│   ├── user_service.py       # User management logic
│   ├── photo_service.py      # Photo business logic
│   ├── image_file_service.py # ImageFile processing logic
│   ├── author_service.py     # Author business logic
│   └── import_session_service.py # Import processing logic
├── schemas/                   # Pydantic models
│   ├── user.py               # User request/response models
│   ├── photo_schemas.py      # Photo request/response models
│   ├── image_file_schemas.py # ImageFile models
│   ├── image_file_upload_schemas.py # New upload schemas
│   ├── requests/             # Request models
│   └── responses/            # Response models
└── utils/                     # Utility functions
    ├── security.py           # Password hashing, JWT creation
    ├── image_utils.py        # Image processing utilities
    └── file_utils.py         # File handling utilities
```

## 🚀 API Design Philosophy

### RESTful + User-Scoped
```
GET    /api/v1/photos              # List user's photos
POST   /api/v1/photos              # Create photo (rare - use image-files)
GET    /api/v1/photos/{hothash}    # Get specific photo (user-owned)
PUT    /api/v1/photos/{hothash}    # Update photo metadata
DELETE /api/v1/photos/{hothash}    # Delete photo + all ImageFiles

POST   /api/v1/image-files/new-photo     # Create new photo with file
POST   /api/v1/image-files/add-to-photo  # Add file to existing photo
GET    /api/v1/image-files/{id}          # Get ImageFile details
```

### Clear Separation of Concerns
- **Photos**: Visual content and metadata
- **ImageFiles**: Physical file records and EXIF data
- **Authors**: Photographer information (user-scoped)
- **ImportSessions**: Batch import tracking (user-scoped)
- **Users**: Authentication and user management

### Frontend-Friendly Responses
```json
{
  "success": true,
  "message": "Photo created successfully", 
  "data": { /* actual response */ },
  "pagination": { /* if applicable */ }
}
```

## 🔄 Migration Path

### From v1.0 to v2.0
1. **Add User System**: Create users table, add user_id to existing tables
2. **Update Repositories**: Add user_id filtering to all queries
3. **Update Services**: Pass user context through service layer
4. **Update APIs**: Add authentication dependencies
5. **Create Upload Endpoints**: Split image upload into clear paths
6. **Test Isolation**: Verify complete user data separation

### Backward Compatibility
- Existing v1 endpoints maintained with deprecation warnings
- Legacy upload endpoint (`POST /image-files/`) still functional
- Migration scripts for existing data

## 📊 Performance Considerations

### Database Optimization
- **Indexes**: user_id on all user-scoped tables
- **Queries**: Always include user_id in WHERE clauses
- **Pagination**: Consistent offset/limit patterns
- **Joins**: Minimize cross-table queries

### Image Processing
- **Hotpreview**: Generated client-side, stored in database
- **Perceptual Hash**: Computed server-side for similarity search
- **EXIF**: Parsed client-side, stored as JSON

### Scalability
- **User Isolation**: Enables horizontal sharding by user_id
- **Stateless**: JWT tokens enable stateless authentication
- **Caching**: User-scoped caching strategies

This architecture provides a robust, scalable foundation for multi-user image management while maintaining the core simplicity and performance of the original ImaLink design.