# ImaLink API Reference v2.1

**Base URL**: `http://localhost:8000/api/v1`  
**Authentication**: JWT Bearer tokens required for all endpoints except auth/register and auth/login

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

---

## 🗂️ ImageFiles

ImageFiles represent physical image files. Multiple ImageFiles (e.g., RAW + JPEG) can belong to one Photo.

### List ImageFiles
```http
GET /api/v1/image-files?offset=0&limit=100
Authorization: Bearer <token>
```

**Query Parameters:**
- `offset` (int): Skip N files
- `limit` (int, max=1000): Number of files to return
- `photo_hothash` (string, optional): Filter by specific photo

### Get ImageFile Details
```http
GET /api/v1/image-files/{image_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 123,
  "filename": "IMG_001.jpg",
  "file_size": 2048576,
  "file_type": "jpeg",
  "width": 4000,
  "height": 3000,
  "photo_hothash": "abc123def456...",
  "exif_dict": {
    "Make": "Canon",
    "Model": "EOS R5",
    "DateTime": "2025:10:15 14:30:00"
  },
  "taken_at": "2025-10-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### Get Hotpreview Image
```http
GET /api/v1/image-files/{image_id}/hotpreview
Authorization: Bearer <token>
```

**Returns:** Binary image data (JPEG, 64x64px thumbnail)

**Response Headers:**
```
Content-Type: image/jpeg
Cache-Control: public, max-age=3600
```

### Create ImageFile with New Photo
```http
POST /api/v1/image-files/new-photo
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
    "Model": "EOS R5"
  },
  "taken_at": "2025-10-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "import_session_id": 5
}
```

**Description:** Upload a completely new, unique photo. Creates both ImageFile and Photo.

**Response** (`201 Created`):
```json
{
  "image_file_id": 123,
  "photo_hothash": "abc123def456...",
  "photo_created": true,
  "message": "ImageFile and Photo created successfully"
}
```

### Add ImageFile to Existing Photo
```http
POST /api/v1/image-files/add-to-photo
Authorization: Bearer <token>
Content-Type: application/json

{
  "photo_hothash": "abc123def456...",
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

**Description:** Add companion file (e.g., RAW) to existing photo. NO hotpreview needed.

**Response** (`201 Created`):
```json
{
  "image_file_id": 124,
  "photo_hothash": "abc123def456...",
  "photo_created": false,
  "message": "ImageFile added to existing Photo"
}
```

### Update ImageFile Storage Info
```http
PUT /api/v1/image-files/{image_file_id}/storage-info
Authorization: Bearer <token>
Content-Type: application/json

{
  "storage_path": "/mnt/photos/2025/10/IMG_001.jpg",
  "storage_type": "local",
  "checksum": "sha256:abc123..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Storage info updated",
  "data": {
    "id": 123,
    "storage_path": "/mnt/photos/2025/10/IMG_001.jpg",
    "storage_type": "local",
    "checksum": "sha256:abc123..."
  }
}
```

### Get ImageFile Storage Info
```http
GET /api/v1/image-files/{image_file_id}/storage-info
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 123,
  "storage_path": "/mnt/photos/2025/10/IMG_001.jpg",
  "storage_type": "local",
  "checksum": "sha256:abc123...",
  "last_verified": "2025-10-20T10:00:00Z"
}
```

### Upload New ImageFile (LEGACY - DEPRECATED)
```http
POST /api/v1/image-files
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "IMG_001.jpg",
  "file_size": 2048576,
  "file_type": "jpeg",
  "width": 4000,
  "height": 3000,
  "hotpreview": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "exif_dict": {
    "Make": "Canon",
    "Model": "EOS R5"
  },
  "taken_at": "2025-10-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522
}
```

**⚠️ DEPRECATED:** Use `/new-photo` or `/add-to-photo` instead for clearer intent.

**Response** (`201 Created`):
```json
{
  "id": 123,
  "filename": "IMG_001.jpg",
  "photo_hothash": "abc123def456...",
  "photo_created": true,
  "message": "ImageFile and Photo created successfully"
}
```

### Find Similar Images
```http
GET /api/v1/image-files/similar/{image_id}?threshold=5&limit=10
Authorization: Bearer <token>
```

**Query Parameters:**
- `threshold` (int, 0-16, default=5): Hamming distance threshold (lower = more similar)
- `limit` (int, 1-100, default=10): Maximum number of results

**Description:** Find visually similar images using perceptual hash comparison.

**Response:**
```json
[
  {
    "id": 125,
    "filename": "IMG_002.jpg",
    "photo_hothash": "def456abc123...",
    "hamming_distance": 2
  },
  {
    "id": 127,
    "filename": "IMG_003.jpg",
    "photo_hothash": "ghi789jkl012...",
    "hamming_distance": 4
  }
]
```

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

### Photo vs ImageFile
- **Photo**: Logical representation of an image with visual hash (hothash)
- **ImageFile**: Physical file (can have multiple per Photo, e.g., RAW + JPEG)

### PhotoStacks
- One-to-many relationship: each Photo can belong to at most ONE stack
- Used for UI organization only, doesn't modify Photo objects
- Common stack types: `panorama`, `burst`, `hdr`, `focus_stack`, `time_lapse`

### Hotpreview
- 300x300px JPEG thumbnail
- Auto-rotated based on EXIF orientation
- Stored as binary blob in database
- Used for fast gallery display

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

**Last Updated:** October 20, 2025  
**API Version:** 2.1  
**Backend Version:** Fase 1 (Multi-User + PhotoStacks)
