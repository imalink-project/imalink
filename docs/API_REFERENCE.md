# ImaLink API Reference v2.1 (Photo-Centric)

**Base URL**: `http://localhost:8000/api/v1`  
**Authentication**: JWT Bearer tokens required for all endpoints except auth/register and auth/login

**Important Change in v2.1:** The ImageFiles API has been removed. All ImageFile operations are now performed through the Photos API for a cleaner, more intuitive interface. See the [ImageFiles section](#️-imagefiles) for migration details.

---

## 🔐 Authentication

### Register New User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepass123",
  "display_name": "John Doe"
}
```

**Response** (`201 Created`):
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "display_name": "John Doe",
  "is_active": true,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepass123"
}
```

**Response** (`200 OK`):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "display_name": "John Doe",
    "is_active": true
  }
}
```

### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

---

## 👤 Users

### Get Current User Profile
```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

### Update Current User Profile
```http
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "display_name": "John Updated",
  "email": "john.new@example.com"
}
```

### Change Password
```http
POST /api/v1/users/me/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "oldpass123",
  "new_password": "newpass456"
}
```

### Delete Account
```http
DELETE /api/v1/users/me
Authorization: Bearer <token>
```

---

## 📸 Photos

All photo operations are scoped to the authenticated user.

### List Photos
```http
GET /api/v1/photos?offset=0&limit=100
Authorization: Bearer <token>
```

**Query Parameters:**
- `offset` (int, default=0): Skip N photos
- `limit` (int, default=100, max=1000): Number of photos to return

**Response:**
```json
{
  "data": [
    {
      "hothash": "abc123def456...",
      "width": 4000,
      "height": 3000,
      "taken_at": "2025-10-15T14:30:00Z",
      "gps_latitude": 59.9139,
      "gps_longitude": 10.7522,
      "rating": 4,
      "author_id": 1,
      "stack_id": null,
      "created_at": "2025-10-20T10:00:00Z",
      "updated_at": "2025-10-20T10:00:00Z"
    }
  ],
  "meta": {
    "total": 250,
    "offset": 0,
    "limit": 100,
    "page": 1,
    "pages": 3
  }
}
```

### Search Photos
```http
POST /api/v1/photos/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "sunset beach",
  "rating_min": 3,
  "rating_max": 5,
  "taken_after": "2025-01-01T00:00:00Z",
  "taken_before": "2025-12-31T23:59:59Z",
  "author_id": 1,
  "offset": 0,
  "limit": 50
}
```

### Get Photo by Hash
```http
GET /api/v1/photos/{hothash}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "hothash": "abc123def456...",
  "width": 4000,
  "height": 3000,
  "taken_at": "2025-10-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "rating": 4,
  "author_id": 1,
  "author": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "stack_id": null,
  "image_files": [
    {
      "id": 123,
      "filename": "IMG_001.jpg",
      "file_size": 2048576,
      "file_type": "jpeg"
    }
  ],
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### Update Photo Metadata
```http
PUT /api/v1/photos/{hothash}
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 5,
  "author_id": 2,
  "gps_latitude": 60.0,
  "gps_longitude": 11.0
}
```

### Delete Photo
```http
DELETE /api/v1/photos/{hothash}
Authorization: Bearer <token>
```

**Note:** Deletes the Photo record and all associated ImageFiles.

### Get Photo Hotpreview
```http
GET /api/v1/photos/{hothash}/hotpreview
Authorization: Bearer <token>
```

**Returns:** JPEG image (64x64 thumbnail) as binary data

**Response Headers:**
```
Content-Type: image/jpeg
Content-Disposition: inline; filename=hotpreview_{hothash}.jpg
Cache-Control: public, max-age=3600
```

### Upload/Update Photo Coldpreview
```http
PUT /api/v1/photos/{hothash}/coldpreview
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image file>
```

**Description:** Upload or update medium-size preview (800-1200px) for a photo.

**Response:**
```json
{
  "status": "success",
  "message": "Coldpreview uploaded successfully",
  "data": {
    "hothash": "abc123def456...",
    "coldpreview_path": "/path/to/coldpreview.jpg"
  }
}
```

### Get Photo Coldpreview
```http
GET /api/v1/photos/{hothash}/coldpreview?width=800&height=600
Authorization: Bearer <token>
```

**Query Parameters:**
- `width` (int, optional, 100-2000): Target width for dynamic resizing
- `height` (int, optional, 100-2000): Target height for dynamic resizing

**Returns:** JPEG image (medium-size preview) as binary data

**Response Headers:**
```
Content-Type: image/jpeg
Content-Disposition: inline; filename=coldpreview_{hothash}.jpg
Cache-Control: public, max-age=3600
```

### Delete Photo Coldpreview
```http
DELETE /api/v1/photos/{hothash}/coldpreview
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Coldpreview deleted successfully"
}
```

### Get Photo's Stack
```http
GET /api/v1/photos/{hothash}/stack
Authorization: Bearer <token>
```

**Description:** Get the PhotoStack containing this photo (if any).

**Response:** PhotoStackSummary object or `null` if photo doesn't belong to a stack.

```json
{
  "id": 5,
  "name": "Sunset Series",
  "stack_type": "burst",
  "photo_count": 8,
  "cover_photo_hothash": "abc123def456...",
  "created_at": "2025-10-20T10:00:00Z"
}
```

### Create Photo with ImageFile
```http
POST /api/v1/photos/new-photo
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "IMG_001.jpg",
  "file_size": 2048576,
  "file_type": "jpeg",
  "width": 4000,
  "height": 3000,
  "hotpreview": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "perceptual_hash": "a1b2c3d4e5f6g7h8",
  "exif_dict": {
    "Make": "Canon",
    "Model": "EOS R5",
    "DateTime": "2025:10:15 14:30:00"
  },
  "taken_at": "2025-10-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "import_session_id": 5
}
```

**Description:** Create a new Photo with its first ImageFile. This is the primary way to add new photos to the system.

**Required Fields:**
- `filename`: Original filename
- `hotpreview`: Base64-encoded 300x300px JPEG thumbnail (used to generate hothash)

**Optional Fields:**
- `perceptual_hash`: If not provided, will be generated from hotpreview
- `file_size`, `file_type`, `width`, `height`: File metadata
- `exif_dict`: EXIF metadata dictionary
- `taken_at`, `gps_latitude`, `gps_longitude`: Photo metadata
- `import_session_id`: Link to import session

**Response** (`201 Created`):
```json
{
  "image_file_id": 123,
  "photo_hothash": "abc123def456...",
  "photo_created": true,
  "message": "ImageFile and Photo created successfully"
}
```

**Error Responses:**
- `409 Conflict` - Photo with this hotpreview already exists (duplicate)
- `400 Bad Request` - Missing required fields or invalid data
- `422 Unprocessable Entity` - Validation error

### Add ImageFile to Existing Photo
```http
POST /api/v1/photos/{hothash}/files
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "IMG_001.CR2",
  "file_size": 25000000,
  "file_type": "raw",
  "width": 5472,
  "height": 3648,
  "exif_dict": {
    "Make": "Canon",
    "Model": "EOS R5"
  },
  "taken_at": "2025-10-15T14:30:00Z",
  "import_session_id": 5
}
```

**Description:** Add a companion ImageFile (e.g., RAW, different resolution) to an existing Photo. No hotpreview needed since the Photo already exists.

**Use Cases:**
- Adding RAW file when JPEG already imported
- Adding different resolution of same photo
- Adding edited version to original

**Response** (`201 Created`):
```json
{
  "image_file_id": 124,
  "photo_hothash": "abc123def456...",
  "photo_created": false,
  "message": "ImageFile added to existing Photo"
}
```

**Error Responses:**
- `404 Not Found` - Photo with this hothash doesn't exist
- `422 Unprocessable Entity` - Validation error

---

## 🗂️ ImageFiles

**⚠️ IMPORTANT:** As of API v2.1, the ImageFiles API has been removed. All ImageFile operations are now performed through the Photos API.

### Migration Guide

**Old (Removed):**
```http
POST /api/v1/image-files/new-photo       ❌ REMOVED
POST /api/v1/image-files/add-to-photo    ❌ REMOVED
GET /api/v1/image-files/{id}             ❌ REMOVED
```

**New (Current):**
```http
POST /api/v1/photos/new-photo            ✅ Use this for new photos
POST /api/v1/photos/{hothash}/files      ✅ Use this to add files
GET /api/v1/photos/{hothash}             ✅ ImageFiles included in response
```

### Accessing ImageFiles

ImageFiles are now accessed exclusively through their parent Photo:

```http
GET /api/v1/photos/{hothash}
```

**Response includes ImageFiles:**
```json
{
  "hothash": "abc123def456...",
  "width": 4000,
  "height": 3000,
  "image_files": [
    {
      "id": 123,
      "filename": "IMG_001.jpg",
      "file_size": 2048576,
      "file_type": "jpeg"
    },
    {
      "id": 124,
      "filename": "IMG_001.CR2",
      "file_size": 25000000,
      "file_type": "raw"
    }
  ]
}
```

### Legacy Endpoints (Removed in v2.1)

The following endpoints were removed in API v2.1. All functionality has been moved to the Photos API.

**Removed Endpoints:**
- ❌ `GET /api/v1/image-files` - List ImageFiles
- ❌ `GET /api/v1/image-files/{id}` - Get ImageFile details
- ❌ `POST /api/v1/image-files` - Upload ImageFile (deprecated)
- ❌ `POST /api/v1/image-files/new-photo` - **Moved to** `POST /api/v1/photos/new-photo`
- ❌ `POST /api/v1/image-files/add-to-photo` - **Moved to** `POST /api/v1/photos/{hothash}/files`
- ❌ `GET /api/v1/image-files/{id}/hotpreview` - Use Photo hotpreview instead
- ❌ `GET /api/v1/image-files/similar/{id}` - Similar image search (to be reimplemented)

**Rationale:** ImageFiles are now treated as internal data structures that belong to Photos. All user-facing operations are performed through the Photos API, which provides a cleaner, more intuitive interface.

---

## 📚 Authors

Manage photographers/creators (can be different from system users).

### List Authors
```http
GET /api/v1/authors?offset=0&limit=100
Authorization: Bearer <token>
```

### Get Author
```http
GET /api/v1/authors/{author_id}
Authorization: Bearer <token>
```

### Create Author
```http
POST /api/v1/authors
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "bio": "Professional landscape photographer"
}
```

**Response** (`201 Created`):
```json
{
  "id": 1,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "bio": "Professional landscape photographer",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### Update Author
```http
PUT /api/v1/authors/{author_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Smith Updated",
  "bio": "Award-winning photographer"
}
```

### Delete Author
```http
DELETE /api/v1/authors/{author_id}
Authorization: Bearer <token>
```

---

## 📦 Import Sessions

Track bulk photo import operations.

### Create Import Session
```http
POST /api/v1/import-sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "source_path": "/media/sdcard/DCIM",
  "description": "Birthday party photos",
  "author_id": 1
}
```

**Response** (`201 Created`):
```json
{
  "id": 1,
  "source_path": "/media/sdcard/DCIM",
  "description": "Birthday party photos",
  "author_id": 1,
  "status": "pending",
  "total_files": 0,
  "processed_files": 0,
  "failed_files": 0,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### Get Import Session
```http
GET /api/v1/import-sessions/{import_id}
Authorization: Bearer <token>
```

### List Import Sessions
```http
GET /api/v1/import-sessions?offset=0&limit=50
Authorization: Bearer <token>
```

### Update Import Session Status
```http
PATCH /api/v1/import-sessions/{import_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "completed",
  "processed_files": 150,
  "failed_files": 2
}
```

### Delete Import Session
```http
DELETE /api/v1/import-sessions/{import_id}
Authorization: Bearer <token>
```

---

## 🗂️ PhotoStacks

Group photos for UI organization (panoramas, bursts, HDR brackets, etc.). Each photo can belong to at most one stack.

### List PhotoStacks
```http
GET /api/v1/photo-stacks?offset=0&limit=50
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "stack_type": "panorama",
      "cover_photo_hothash": "abc123...",
      "photo_count": 5,
      "created_at": "2025-10-20T10:00:00Z",
      "updated_at": "2025-10-20T10:00:00Z"
    }
  ],
  "meta": {
    "total": 15,
    "offset": 0,
    "limit": 50,
    "page": 1,
    "pages": 1
  }
}
```

### Get PhotoStack Details
```http
GET /api/v1/photo-stacks/{stack_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "stack_type": "panorama",
  "cover_photo_hothash": "abc123...",
  "photo_hothashes": ["abc123...", "def456...", "ghi789..."],
  "photo_count": 3,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### Create PhotoStack
```http
POST /api/v1/photo-stacks
Authorization: Bearer <token>
Content-Type: application/json

{
  "stack_type": "panorama",
  "cover_photo_hothash": "abc123..."
}
```

**Response** (`201 Created`):
```json
{
  "success": true,
  "message": "Photo stack created successfully",
  "stack": {
    "id": 1,
    "stack_type": "panorama",
    "cover_photo_hothash": "abc123...",
    "photo_hothashes": [],
    "photo_count": 0,
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-20T10:00:00Z"
  }
}
```

### Update PhotoStack
```http
PUT /api/v1/photo-stacks/{stack_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "stack_type": "burst",
  "cover_photo_hothash": "def456..."
}
```

### Delete PhotoStack
```http
DELETE /api/v1/photo-stacks/{stack_id}
Authorization: Bearer <token>
```

**Note:** Photos in the stack are not deleted, only the stack grouping.

### Add Photo to Stack
```http
POST /api/v1/photo-stacks/{stack_id}/photo
Authorization: Bearer <token>
Content-Type: application/json

{
  "photo_hothash": "xyz789..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Photo added to stack successfully",
  "stack": {
    "id": 1,
    "photo_hothashes": ["abc123...", "def456...", "xyz789..."],
    "photo_count": 3
  }
}
```

### Remove Photo from Stack
```http
DELETE /api/v1/photo-stacks/{stack_id}/photo/{photo_hothash}
Authorization: Bearer <token>
```

---

## 🐛 Debug Endpoints

**⚠️ Development only - disable in production!**

### System Status
```http
GET /api/v1/debug/status
```

### Database Stats
```http
GET /api/v1/debug/database-stats
```

### Database Schema
```http
GET /api/v1/debug/database-schema
```

### Reset Database
```http
POST /api/v1/debug/reset-database
```

### Clear Table
```http
DELETE /api/v1/debug/clear-table/{table_name}
```

---

## 📊 Common Response Structures

### Paginated Response
```json
{
  "data": [...],
  "meta": {
    "total": 1000,
    "offset": 0,
    "limit": 100,
    "page": 1,
    "pages": 10
  },
  "links": null
}
```

### Error Response
```json
{
  "detail": "Error message here",
  "status_code": 400
}
```

### Common HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Authenticated but not allowed
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource
- `500 Internal Server Error` - Server error

---

## 🔑 Authentication Headers

All protected endpoints require JWT token:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Token Lifetime:** 30 minutes (configurable)

**Refresh Strategy:** Re-login when token expires (refresh tokens not yet implemented)

---

## �� CORS

API accepts requests from:
- `http://localhost:*` (development)
- `http://127.0.0.1:*` (development)
- Configure `ALLOWED_ORIGINS` in production

---

## 📝 Notes

### User Isolation
All data operations are automatically scoped to the authenticated user. Users cannot access or modify other users' data.

### Photo vs ImageFile (Updated in v2.1)
- **Photo**: Logical representation of an image with visual data (hothash, dimensions, EXIF metadata, hotpreview, etc.)
- **ImageFile**: Physical file metadata (filename, file_size, file_type, storage info)
- **Relationship**: One Photo can have multiple ImageFiles (e.g., RAW + JPEG of the same shot)
- **API Access**: Photos are the primary user-facing resource. ImageFiles are accessed through Photos API only.

### 100% Photo-Centric API (v2.1)
As of v2.1, the API is 100% photo-centric:
- All ImageFile creation is done through Photos endpoints (`POST /photos/new-photo` and `POST /photos/{hothash}/files`)
- ImageFiles API has been removed
- ImageFiles are accessible only via Photo relationships (included in Photo responses)
- This provides a clearer, more intuitive API where Photos are the natural entry point

### PhotoStacks
- One-to-many relationship: each Photo can belong to at most ONE stack
- Used for UI organization only, doesn't modify Photo objects
- Common stack types: `panorama`, `burst`, `hdr`, `focus_stack`, `time_lapse`

### Hotpreview
- 300x300px JPEG thumbnail
- Auto-rotated based on EXIF orientation
- Stored as binary blob in database
- Used for fast gallery display and generating Photo hothash (SHA256)

---

## 🚀 Getting Started

1. **Register a user:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"demo","email":"demo@example.com","password":"demo123","display_name":"Demo User"}'
   ```

2. **Login to get token:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"demo","password":"demo123"}'
   ```

3. **Use token in requests:**
   ```bash
   curl -X GET http://localhost:8000/api/v1/photos \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

---

## 📋 Changelog

### v2.1 (October 21, 2025) - 100% Photo-Centric API
**Breaking Changes:**
- ❌ **Removed:** Entire ImageFiles API (`/api/v1/image-files/*`)
- ❌ **Removed:** `GET /api/v1/image-files/{id}` - Access ImageFiles via Photo responses
- ❌ **Removed:** `POST /api/v1/image-files/new-photo` 
- ❌ **Removed:** `POST /api/v1/image-files/add-to-photo`

**New Endpoints:**
- ✅ **Added:** `POST /api/v1/photos/new-photo` - Create Photo with initial ImageFile
- ✅ **Added:** `POST /api/v1/photos/{hothash}/files` - Add ImageFile to existing Photo

**Benefits:**
- Cleaner, more intuitive API
- Photos are the natural entry point for all operations
- ImageFiles accessible via Photo relationships
- Reduced API surface area

**Migration Guide:**
```bash
# Before v2.1:
POST /api/v1/image-files/new-photo

# After v2.1:
POST /api/v1/photos/new-photo

# Before v2.1:
POST /api/v1/image-files/add-to-photo
{
  "photo_hothash": "abc123...",
  "filename": "image.raw"
}

# After v2.1:
POST /api/v1/photos/abc123.../files
{
  "filename": "image.raw"
}
```

---

**Last Updated:** October 21, 2025  
**API Version:** 2.1 (100% Photo-Centric)  
**Backend Version:** Fase 1 (Multi-User + PhotoStacks + Photo-Centric API)
