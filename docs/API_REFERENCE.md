# ImaLink API Reference v2.0

**Base URL**: `http://localhost:8000/api/v1`  
**For WSL → Windows**: `http://172.x.x.x:8000/api/v1` (use `hostname -I` in WSL to find IP)

## 🔐 Authentication

ImaLink now uses JWT-based authentication with user isolation:

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com", 
  "password": "securepass123",
  "display_name": "John Doe"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepass123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "display_name": "John Doe"
  }
}
```

### Authenticated Requests
Include JWT token in Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 🖼️ ImageFile Upload - New Architecture

### Upload New Photo
Upload a completely new, unique photo:

```http
POST /image-files/new-photo
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "IMG_001.jpg",
  "hotpreview": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "file_size": 2048576,
  "exif_dict": {
    "DateTime": "2023:10:15 14:30:00",
    "Make": "Canon",
    "Model": "EOS R5"
  },
  "taken_at": "2023-10-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522
}
```

**Response:**
```json
{
  "image_file_id": 123,
  "filename": "IMG_001.jpg", 
  "file_size": 2048576,
  "photo_hothash": "abc123def456...",
  "photo_created": true,
  "success": true,
  "message": "New photo created successfully"
}
```

### Add Companion File
Add RAW/different format to existing photo:

```http
POST /image-files/add-to-photo
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "IMG_001.CR3",
  "photo_hothash": "abc123def456...",
  "file_size": 45678901,
  "exif_dict": {
    "DateTime": "2023:10:15 14:30:00",
    "Make": "Canon",
    "Model": "EOS R5"
  }
}
```

**Response:**
```json
{
  "image_file_id": 124,
  "filename": "IMG_001.CR3",
  "file_size": 45678901, 
  "photo_hothash": "abc123def456...",
  "photo_created": false,
  "success": true,
  "message": "Image file added to existing photo successfully"
}
```

## 📸 Photos API

### List User Photos
```http
GET /photos?offset=0&limit=50
Authorization: Bearer <token>
```

### Get Photo Details
```http
GET /photos/{hothash}
Authorization: Bearer <token>
```

### Update Photo Metadata
```http
PUT /photos/{hothash}
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 5,
  "author_id": 2
}
```

### Delete Photo (and all ImageFiles)
```http
DELETE /photos/{hothash}
Authorization: Bearer <token>
```

## � Photo Stacks API

Photo stacks organize photos into collections for UI purposes. Each photo can belong to at most one stack.

### List Photo Stacks
```http
GET /photo-stacks?offset=0&limit=50
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "stack_type": "album",
      "cover_photo_hothash": "abc123def456...",
      "photo_count": 15,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-16T14:20:00"
    }
  ],
  "meta": {
    "total": 1,
    "offset": 0,
    "limit": 50
  }
}
```

### Get Stack Details
```http
GET /photo-stacks/{stack_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "stack_type": "album",
  "cover_photo_hothash": "abc123def456...",
  "photo_hothashes": [
    "abc123def456...",
    "def456ghi789...",
    "ghi789jkl012..."
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-16T14:20:00"
}
```

### Create Photo Stack
```http
POST /photo-stacks
Authorization: Bearer <token>
Content-Type: application/json

{
  "stack_type": "album",
  "cover_photo_hothash": "abc123def456..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Photo stack created successfully",
  "stack": {
    "id": 1,
    "stack_type": "album", 
    "cover_photo_hothash": "abc123def456...",
    "photo_hothashes": [],
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

### Update Photo Stack
```http
PUT /photo-stacks/{stack_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "stack_type": "panorama",
  "cover_photo_hothash": "new_cover_hash..."
}
```

### Delete Photo Stack
```http
DELETE /photo-stacks/{stack_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Photo stack deleted successfully",
  "stack": null
}
```

### Add Photo to Stack
```http
POST /photo-stacks/{stack_id}/photo
Authorization: Bearer <token>
Content-Type: application/json

{
  "photo_hothash": "abc123def456..."
}
```

**Note:** If the photo is already in another stack, it will be moved to this stack.

**Response:**
```json
{
  "success": true,
  "message": "Photo added to stack successfully",
  "stack": {
    "id": 1,
    "photo_count": 3
  }
}
```

### Remove Photo from Stack
```http
DELETE /photo-stacks/{stack_id}/photo/{photo_hothash}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Photo removed from stack successfully",
  "stack": {
    "id": 1,
    "photo_count": 2
  }
}
```

### Get Photo Stack
```http
GET /photos/{photo_hothash}/stack
Authorization: Bearer <token>
```

**Response:** Returns the stack containing the photo, or null if photo is not in any stack.

```json
{
  "id": 1,
  "stack_type": "album",
  "cover_photo_hothash": "abc123def456",
  "photo_count": 24,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-16T14:20:00"
}
```

## �👤 Authors API

### List Authors
```http
GET /authors
Authorization: Bearer <token>
```

### Create Author
```http
POST /authors
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John Photographer",
  "email": "john@photo.com",
  "bio": "Professional landscape photographer"
}
```

### Update Author
```http
PUT /authors/{author_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John P. Photographer",
  "bio": "Award-winning landscape photographer"
}
```

## 📁 Import Sessions API

### List Import Sessions
```http
GET /import_sessions
Authorization: Bearer <token>
```

### Create Import Session
```http
POST /import_sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Europe Trip 2023",
  "source_path": "/external/photos/europe-2023",
  "description": "Photos from summer vacation"
}
```

## 👥 User Management

### Get Current User Profile
```http
GET /users/me
Authorization: Bearer <token>
```

### Change Password
```http
PUT /users/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "oldpass123",
  "new_password": "newpass456"
}
```

## 🔒 Data Isolation & Multi-User Architecture

### Symmetric User Ownership
All major data models have consistent user ownership:
```typescript
User.id ← Photo.user_id
User.id ← Author.user_id  
User.id ← ImportSession.user_id
User.id ← ImageFile.user_id
```

### Complete Data Isolation
- Users can only see their own photos, authors, import sessions, and image files
- Cross-user access is prevented at repository level with `user_id` filtering
- All API endpoints require authentication
- User statistics include counts for all owned resources

## 📝 Error Responses

### Authentication Errors
```json
{
  "detail": "Could not validate credentials",
  "status_code": 401
}
```

### Not Found
```json
{
  "detail": "Photo not found",
  "status_code": 404
}
```

### Duplicate Photo
```json
{
  "detail": "Photo with this image already exists. Use /add-to-photo endpoint instead.",
  "status_code": 409
}
```

## 📋 TypeScript Interfaces

### User
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  
  // Statistics
  photos_count: number;
  import_sessions_count: number;
  authors_count: number;
  image_files_count: number;
}
```

### Photo
```typescript
interface Photo {
  hothash: string;
  rating?: number;
  taken_at?: string;
  gps_latitude?: number;
  gps_longitude?: number;
  author_id?: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}
```

### ImageFile
```typescript
interface ImageFile {
  id: number;
  user_id: number;              // NEW: User ownership
  photo_hothash: string;
  filename: string;
  file_size?: number;
  has_hotpreview: boolean;
  perceptual_hash?: string;
  exif_dict?: Record<string, any>;
  import_session_id?: number;
  imported_time?: string;
  created_at: string;
}
```

### PhotoStack
```typescript
interface PhotoStackSummary {
  id: number;
  stack_type?: string;
  cover_photo_hothash?: string;
  photo_count: number;
  created_at: string;
  updated_at: string;
}

interface PhotoStackDetail {
  id: number;
  stack_type?: string;
  cover_photo_hothash?: string;
  photo_hothashes: string[];
  created_at: string;
  updated_at: string;
}

// API Request/Response Types
interface PhotoStackCreateRequest {
  stack_type?: string;
  cover_photo_hothash?: string;
}

interface PhotoStackUpdateRequest {
  stack_type?: string;
  cover_photo_hothash?: string;
}

interface PhotoStackAddPhotoRequest {
  photo_hothash: string;
}

interface PhotoStackOperationResponse {
  success: boolean;
  message: string;
  stack?: PhotoStackDetail;
}

interface PhotoStackPhotoResponse {
  success: boolean;
  message: string;
  stack?: PhotoStackDetail;
}
```

### Author
```typescript
interface Author {
  id: number;
  name: string;
  email?: string;
  bio?: string;
  user_id: number;
  created_at: string;
  updated_at: string;
}
```

---

## 🔗 Interactive Documentation

When server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

These provide interactive API testing and complete schema definitions.

---

## 🔧 Debug Endpoints

**⚠️ Development only - will be removed in production**

### GET /debug/status
Get API status and version info.

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```

### GET /debug/database-stats
Get database statistics.

**Response**:
```json
{
  "photos": 150,
  "image_files": 200,
  "authors": 10,
  "import_sessions": 20
}
```

---

## 💾 Storage Architecture

The hybrid storage architecture combines:
- **Hotpreview**: Thumbnails (150x150) stored in SQLite
- **Coldpreview**: Medium-size images (800-1200px) stored on filesystem
- **Directory Structure**: 2-level hash-based directories for performance
- **File Format**: JPEG with 85% quality for optimal size/quality balance

---

## 📸 Photos

Photos represent the logical image entities with metadata. Each photo has a unique `hothash`.

### GET /photos/
List all photos with pagination.

**Query Parameters:**
- `skip` (int, optional): Number of records to skip. Default: 0
- `limit` (int, optional): Max records to return. Default: 100

**Response**: `PaginatedResponse<PhotoResponse>`
```json
{
  "items": [
    {
      "hothash": "9e183676fb52ebe03ffa615080a99d3e3756751be7bc43bc3d275870d4ebe220",
      "width": 4000,
      "height": 3000,
      "hotpreview": "base64-encoded-thumbnail...",
      "coldpreview_path": "9e/18/9e183676fb52ebe03ffa615080a99d3e3756751be7bc43bc3d275870d4ebe220.jpg",
      "coldpreview_width": 1200,
      "coldpreview_height": 900,
      "coldpreview_size": 245760,
      "taken_at": "2024-04-27T10:30:15",
      "gps_latitude": 59.9139,
      "gps_longitude": 10.7522,
      "author_id": 1,
      "author": {
        "id": 1,
        "name": "John Doe"
      },
      "rating": 5,
      "has_gps": true,
      "has_raw_companion": false,
      "primary_filename": "IMG_001.jpg",
      "files": [
        {
          "id": 1,
          "filename": "IMG_001.jpg",
          "file_format": "JPEG",
          "file_size": 2048000
        }
      ],
      "created_at": "2024-04-27T12:00:00Z",
      "updated_at": "2024-04-27T12:00:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

### POST /photos/search
Search photos with filters.

**Request Body**: `PhotoSearchRequest`
```json
{
  "author_id": 1,
  "rating_min": 3,
  "rating_max": 5
}
```

**Response**: `PaginatedResponse<PhotoResponse>`

### GET /photos/{hothash}
Get a single photo by hothash.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: `PhotoResponse`

**🆕 October 2025 Update**: Response now includes `exif_dict` field with EXIF metadata from the master ImageFile.

**Example Response:**
```json
{
  "hothash": "a1b2c3d4e5f6789abcdef1234567890abcdef1234567890abcdef1234567890",
  "exif_dict": {
    "camera": "Canon EOS R5",
    "lens": "RF 24-70mm f/2.8L IS USM",
    "iso": 400,
    "aperture": "f/5.6",
    "shutter_speed": "1/125",
    "focal_length": "50mm"
  },
  "taken_at": "2024-10-19T15:30:45.123Z",
  "gps_latitude": 60.3913,
  "gps_longitude": 5.3221,
  "rating": 5,
  "has_gps": true,
  "primary_filename": "IMG_2024.jpg"
}
```

### GET /photos/{hothash}/hotpreview
Get the photo's thumbnail image (150x150 JPEG).

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: Binary image data (image/jpeg)

### PUT /photos/{hothash}
Update a photo's metadata.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Request Body**: `PhotoUpdateRequest`
```json
{
  "author_id": 2,
  "rating": 4
}
```

**Response**: `PhotoResponse`

### DELETE /photos/{hothash}
Delete a photo and all associated image files.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: 204 No Content

### PUT /photos/{hothash}/coldpreview
Upload or update a coldpreview image for a photo.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Request Body**: Multipart form data
- `file` (file): Image file for coldpreview (JPEG, PNG, etc.)

**Response**: Success response with coldpreview metadata
```json
{
  "success": true,
  "message": "Coldpreview uploaded successfully",
  "data": {
    "hothash": "abc123...",
    "width": 1200,
    "height": 800,
    "size": 234567,
    "path": "ab/cd/abc123....jpg"
  }
}
```

**Notes:**
- Coldpreview images are automatically resized to max 1200px dimension
- Images are saved as JPEG with 85% quality for optimal size/quality balance
- Server handles file storage and organization automatically
- Upload validates image format and content-type
- Returns metadata including dimensions and file size

### GET /photos/{hothash}/coldpreview
Get the coldpreview image for a photo with optional dynamic resizing.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Query Parameters:**
- `width` (int, optional): Target width for dynamic resizing (100-2000px)
- `height` (int, optional): Target height for dynamic resizing (100-2000px)

**Response**: Binary image data (image/jpeg)

**Examples:**
- `GET /photos/abc123/coldpreview` - Original coldpreview
- `GET /photos/abc123/coldpreview?width=800` - Resized to 800px width (maintains aspect ratio)
- `GET /photos/abc123/coldpreview?width=800&height=600` - Resized to fit 800x600 (maintains aspect ratio)

**Notes:**
- Returns 404 if no coldpreview exists for the photo
- Dynamic resizing is performed on-the-fly with caching headers
- Maintains original aspect ratio when resizing

### DELETE /photos/{hothash}/coldpreview
Delete the coldpreview for a photo.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: Success response
```json
{
  "success": true,
  "message": "Coldpreview deleted successfully"
}
```

**Notes:**
- Removes coldpreview file and metadata completely
- Returns 404 if no coldpreview exists for the photo
- Operation is idempotent - safe to call multiple times

---

## 🖼️ Image Files

ImageFiles are the actual file records. Multiple files can belong to one photo.

### GET /image-files/
List all image files with pagination.

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 100

**Response**: `PaginatedResponse<ImageFileResponse>`
```json
{
  "items": [
    {
      "id": 1,
      "filename": "IMG_001.jpg",
      "file_size": 2048000,
      "file_format": "JPEG",
      "width": 4000,
      "height": 3000,
      "color_space": "sRGB",
      "bit_depth": 8,
      "original_path": "/path/to/image.jpg",
      "archive_path": "/archive/2024/04/IMG_001.jpg",
      "hothash": "abc123...",
      "hotpreview": "base64encodedimage...",
      "photo_id": 1,
      "import_session_id": 1,
      "created_at": "2024-04-27T12:00:00",
      "updated_at": "2024-04-27T12:00:00"
    }
  ],
  "total": 200,
  "skip": 0,
  "limit": 100
}
```

### GET /image-files/{image_id}
Get a single image file by ID.

**Path Parameters:**
- `image_id` (int): The image file's ID

**Response**: `ImageFileResponse`

### GET /image-files/{image_id}/hotpreview
Get the image file's thumbnail (150x150 JPEG).

**Path Parameters:**
- `image_id` (int): The image file's ID

**Response**: Binary image data (image/jpeg)

### POST /image-files/
Create a new image file (import workflow).

**Request Body**: `ImageFileCreateRequest`
```json
{
  "filename": "IMG_001.jpg",
  "file_size": 2048000,
  "file_path": "/path/to/image.jpg",
  "hotpreview": "base64encodedJPEGdata...",
  "import_session_id": 1,
  "exif_data": {
    "Make": "Canon",
    "Model": "EOS R5",
    "DateTime": "2024:04:27 12:00:00"
  }
}
```

**Response**: `ImageFileResponse` (201 Created)

**Notes:**
- `hotpreview` must be base64-encoded JPEG (150x150)
- Server will generate `hothash` from hotpreview
- Server will create/update Photo entity automatically
- File will be archived to configured archive path

---

## 👤 Authors

### GET /authors/
List all authors.

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 100

**Response**: `PaginatedResponse<AuthorResponse>`
```json
{
  "items": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 100
}
```

### POST /authors/
Create a new author.

**Request Body**: `AuthorCreateRequest`
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com"
}
```

**Response**: `AuthorResponse` (201 Created)

### GET /authors/{author_id}
Get a single author by ID.

**Path Parameters:**
- `author_id` (int): The author's ID

**Response**: `AuthorResponse`

### PUT /authors/{author_id}
Update an author.

**Path Parameters:**
- `author_id` (int): The author's ID

**Request Body**: `AuthorUpdateRequest`
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com"
}
```

**Response**: `AuthorResponse`

### DELETE /authors/{author_id}
Delete an author.

**Path Parameters:**
- `author_id` (int): The author's ID

**Response**: 204 No Content

---

## 📦 Import Sessions

Import sessions track batch imports.

### GET /import-sessions/
List all import sessions.

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 100

**Response**: `PaginatedResponse<ImportSessionResponse>`
```json
{
  "items": [
    {
      "id": 1,
      "session_name": "2024-04-27 Import",
      "import_path": "/mnt/c/Photos/Import",
      "total_files": 150,
      "processed_files": 150,
      "failed_files": 0,
      "status": "completed",
      "created_at": "2024-04-27T12:00:00",
      "updated_at": "2024-04-27T14:00:00"
    }
  ],
  "total": 20,
  "skip": 0,
  "limit": 100
}
```

### POST /import-sessions/
Create a new import session.

**Request Body**: `ImportSessionCreateRequest`
```json
{
  "session_name": "My Import Session",
  "import_path": "/path/to/import/folder"
}
```

**Response**: `ImportSessionResponse` (201 Created)

### GET /import-sessions/{session_id}
Get a single import session by ID.

**Path Parameters:**
- `session_id` (int): The import session's ID

**Response**: `ImportSessionResponse`

---

## �🔧 Debug Endpoints

**⚠️ Development only - will be removed in production**

### GET /debug/status
Get API status and version info.

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```

### GET /debug/database-stats
Get database statistics.

**Response**:
```json
{
  "photos": 150,
  "image_files": 200,
  "authors": 10,
  "import_sessions": 20
}
```

### POST /debug/reset-database
Reset entire database (DELETE ALL DATA).

**Response**: 204 No Content

### POST /debug/clear-database
Clear all data but keep schema.

**Response**: 204 No Content

---

## 📊 Data Models

### Common Types

#### PaginatedResponse<T>
```typescript
{
  items: T[],
  total: number,
  skip: number,
  limit: number
}
```

### Photo Models

#### PhotoResponse
```typescript
{
  hothash: string,                    // SHA256 hash identifier
  
  // Visual presentation data
  hotpreview: string | null,          // Base64 encoded preview image
  width: number | null,               // Original image width in pixels
  height: number | null,              // Original image height in pixels
  
  // Coldpreview metadata
  coldpreview_path: string | null,    // Filesystem path to coldpreview file
  coldpreview_width: number | null,   // Coldpreview width
  coldpreview_height: number | null,  // Coldpreview height
  coldpreview_size: number | null,    // Coldpreview file size
  
  // Content metadata
  taken_at: string | null,            // When photo was taken (ISO 8601)
  gps_latitude: number | null,        // GPS latitude
  gps_longitude: number | null,       // GPS longitude
  exif_dict: object | null,           // 🆕 EXIF metadata from master image file
  
  // User metadata
  rating: number,                     // User rating (0-5 stars)
  
  // Timestamps
  created_at: string,                 // When photo was imported (ISO 8601)
  updated_at: string,                 // When photo was last updated (ISO 8601)
  
  // Relationships
  author: AuthorSummary | null,       // Photo author/photographer
  author_id: number | null,           // Author ID
  
  // Import information
  import_sessions: number[],          // All import sessions for this photo's files
  first_imported: string | null,      // Earliest import time (ISO 8601)
  last_imported: string | null,       // Latest import time (ISO 8601)
  
  // Computed properties
  has_gps: boolean,                   // Whether photo has GPS coordinates
  has_raw_companion: boolean,         // Whether photo has both JPEG and RAW files
  primary_filename: string | null,    // Primary filename for display
  files: ImageFileSummary[]          // Associated image files
}
```

#### PhotoSearchRequest
```typescript
{
  author_id?: number,
  rating_min?: number,
  rating_max?: number
}
```

#### PhotoUpdateRequest
```typescript
{
  author_id?: number,
  rating?: number
}
```

### ImageFile Models

#### ImageFileResponse
```typescript
{
  id: number,
  filename: string,
  file_size: number,          // bytes
  file_format: string | null, // "JPEG", "PNG", "DNG", etc.
  width: number | null,       // pixels
  height: number | null,      // pixels
  color_space: string | null, // "sRGB", "AdobeRGB", etc.
  bit_depth: number | null,   // 8, 16, etc.
  original_path: string,
  archive_path: string | null,
  hothash: string,
  hotpreview: string,         // base64 JPEG
  photo_id: number,
  import_session_id: number | null,
  created_at: string,
  updated_at: string
}
```

#### ImageFileCreateRequest
```typescript
{
  filename: string,
  file_size?: number,
  hotpreview: string,                    // base64 JPEG hotpreview (required)
  perceptual_hash?: string,              // auto-generated if not provided
  
  // EXIF metadata (frontend responsibility)
  exif_dict?: Record<string, any>,       // Complete EXIF data as JSON
  
  // 🆕 Frontend-extracted metadata (replaces backend EXIF parsing)
  taken_at?: string,                     // ISO 8601 datetime when photo was taken
  gps_latitude?: number,                 // GPS latitude (-90 to 90)
  gps_longitude?: number,                // GPS longitude (-180 to 180)
  
  // Import context
  import_session_id?: number,
  imported_info?: Record<string, any>,
  local_storage_info?: Record<string, any>,
  cloud_storage_info?: Record<string, any>
}
```

### PhotoStack Models

#### PhotoStackSummary
```typescript
{
  id: number,
  stack_type: string | null,          // "album", "panorama", "burst", "animation", etc.
  cover_photo_hothash: string | null, // Hash of cover photo
  photo_count: number,                // Number of photos in stack
  created_at: string,                 // ISO 8601
  updated_at: string                  // ISO 8601
}
```

#### PhotoStackDetail
```typescript
{
  id: number,
  stack_type: string | null,
  cover_photo_hothash: string | null,
  photo_hothashes: string[],          // Array of photo hashes in stack
  created_at: string,
  updated_at: string
}
```

#### PhotoStackCreateRequest
```typescript
{
  stack_type?: string,                // Max 50 characters
  cover_photo_hothash?: string        // Must exist and belong to user
}
```

#### PhotoStackUpdateRequest
```typescript
{
  stack_type?: string,
  cover_photo_hothash?: string
}
```

#### PhotoStackOperationResponse
```typescript
{
  success: boolean,
  message: string,
  stack?: PhotoStackDetail            // Present for create/update operations
}
```

### Author Models

#### AuthorResponse
```typescript
{
  id: number,
  name: string,
  email: string | null,
  created_at: string,
  updated_at: string
}
```

#### AuthorCreateRequest
```typescript
{
  name: string,
  email?: string
}
```

#### AuthorUpdateRequest
```typescript
{
  name?: string,
  email?: string
}
```

### ImportSession Models

#### ImportSessionResponse
```typescript
{
  id: number,
  session_name: string,
  import_path: string | null,
  total_files: number,
  processed_files: number,
  failed_files: number,
  status: "pending" | "processing" | "completed" | "failed",
  created_at: string,
  updated_at: string
}
```

#### ImportSessionCreateRequest
```typescript
{
  session_name: string,
  import_path?: string
}
```

---

## 🔄 Typical Workflows

### Import Images Workflow

1. **Create import session**:
   ```
   POST /import-sessions/
   {
     "session_name": "My Import",
     "import_path": "/path/to/images"
   }
   ```

2. **For each image file**:
   ```
   POST /image-files/
   {
     "filename": "IMG_001.jpg",
     "file_size": 2048000,
     "file_path": "/path/to/IMG_001.jpg",
     "hotpreview": "base64...",
     "import_session_id": 1
   }
   ```
   
   Server will:
   - Generate `hothash` from hotpreview
   - Create or find existing Photo by hothash
   - Link ImageFile to Photo
   - Archive file to configured location

3. **Verify import**:
   ```
   GET /import-sessions/1
   ```

### Display Photo Gallery

1. **Get all photos with thumbnails**:
   ```
   GET /photos/?limit=50
   ```

2. **For each photo, display hotpreview**:
   ```
   GET /photos/{hothash}/hotpreview
   ```
   Returns JPEG image directly

3. **Click on photo for details**:
   ```
   GET /photos/{hothash}
   ```
   Returns full metadata + associated image files

### Search Photos

```
POST /photos/search
{
  "rating_min": 4,
  "author_id": 1
}
```

### Organize Photos into Stacks

**Create a new photo stack:**
```
POST /photo-stacks/
{
  "stack_type": "album",
  "cover_photo_hothash": "abc123def456..."
}
```

**Add photos to stack (one at a time):**
```
POST /photo-stacks/1/photo
{
  "photo_hothash": "abc123def456..."
}
```

**Note:** If photo is already in another stack, it will be moved to this stack.

**List all stacks:**
```
GET /photo-stacks/?limit=20
```

**Get stack details with all photos:**
```
GET /photo-stacks/1
```

**Remove photo from stack:**
```
DELETE /photo-stacks/1/photo/abc123def456...
```

**Find which stack contains a photo:**
```
GET /photo-stacks/photo/abc123def456.../stacks
```

---

## 🐛 Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success (no body)
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

## � Schema Reference

### PhotoResponse

Complete photo object with all metadata and preview information.

**Fields:**
- `hothash` (string): Content-based hash identifier (SHA256 of hotpreview)
- `hotpreview` (string, optional): Base64-encoded thumbnail (150x150 JPEG)
- `width` (int, optional): Original image width in pixels
- `height` (int, optional): Original image height in pixels
- `coldpreview_path` (string, optional): Filesystem path to coldpreview file
- `coldpreview_width` (int, optional): Coldpreview width in pixels  
- `coldpreview_height` (int, optional): Coldpreview height in pixels
- `coldpreview_size` (int, optional): Coldpreview file size in bytes
- `taken_at` (datetime, optional): When photo was taken (from EXIF)
- `gps_latitude` (float, optional): GPS latitude coordinate
- `gps_longitude` (float, optional): GPS longitude coordinate
- `rating` (int): User rating (0-5 stars)
- `author_id` (int, optional): Author/photographer ID
- `author` (object, optional): Author details with id and name
- `import_session_id` (int, optional): Import session ID
- `has_gps` (bool): Whether photo has GPS coordinates
- `has_raw_companion` (bool): Whether photo has both JPEG and RAW files
- `primary_filename` (string, optional): Primary filename for display
- `files` (array): Associated ImageFile objects
- `created_at` (datetime): When photo was imported
- `updated_at` (datetime): When photo was last updated

---

## �🔗 Interactive Documentation

When server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

These provide interactive API testing and complete schema definitions.
