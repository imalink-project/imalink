# ImaLink Backend API Changes - November 12, 2025

**Critical updates for imalink-desktop and imalink-web**

---

## 🔴 BREAKING CHANGES

### 1. **POST /api/v1/photos/new-photo REMOVED**

**Status**: ❌ **DELETED - DO NOT USE**

**Reason**: Replaced by PhotoEgg-only architecture

**Migration**:
- **imalink-desktop**: Use `POST /api/v1/photos/photoegg` instead
- **imalink-web**: Use `POST /api/v1/photos/register-image` instead

---

### 2. **ImportSession is now REQUIRED for all photos**

**Field**: `import_session_id` in Photo

**Status**: Required for production, optional for tests

**Default behavior**: 
- If NOT provided → Auto-uses user's protected "Quick Add" session
- Every user gets a protected ImportSession on registration (cannot be deleted)
- Desktop app SHOULD create ImportSession per import batch
- Web app CAN omit import_session_id (uses default)

**Protected ImportSession**:
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Quick Add",
  "description": "Default import session for quick photo additions",
  "is_protected": true,  // NEW FIELD - cannot be deleted
  "created_at": "2025-11-12T10:00:00Z"
}
```

**API Changes**:
- `DELETE /api/v1/import-sessions/{id}` → Returns 400 if `is_protected=true`
- `PUT /api/v1/import-sessions/{id}` → Can update title/description even if protected

---

### 3. **Photo.category field added**

**New field**: `category` (string, optional, indexed)

**Purpose**: User-defined categorization (e.g., "work", "hobby", "family")

**Usage**:
```json
{
  "category": "vacation",  // NEW - optional user-defined category
  "rating": 4,
  "visibility": "private"
}
```

**Desktop app**: 
- Add category dropdown/input in photo metadata editor
- Allow bulk category assignment

**Web app**:
- Show category in photo grid (filter/group by category)
- Add category selector in upload dialog

---

## ✅ NEW ENDPOINTS

### 1. **POST /api/v1/photos/photoegg** (Desktop app - PRIMARY)

**Purpose**: Create photo from pre-processed PhotoEgg (replaces /new-photo)

**Flow**:
1. Desktop app selects files → Sends to LOCAL imalink-core
2. imalink-core returns PhotoEgg JSON
3. Desktop app → Backend POST /photoegg with PhotoEgg + metadata
4. Backend stores photo (NO image processing on server)

**Request**:
```json
POST /api/v1/photos/photoegg
Content-Type: application/json

{
  "photo_egg": {
    "hothash": "a6317d064f4d83ff419b9deaf35ba537...",
    "hotpreview_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "coldpreview_base64": null,
    "width": 4000,
    "height": 3000,
    "primary_filename": "IMG_1234.jpg",
    "taken_at": "2024-08-15T14:30:00Z",
    "camera_make": "Canon",
    "camera_model": "EOS R5",
    "gps_latitude": 59.9139,
    "gps_longitude": 10.7522,
    "has_gps": true,
    "iso": 400,
    "aperture": 2.8,
    "shutter_speed": "1/250",
    "focal_length": 50,
    "lens_model": "RF 50mm F1.2 L USM",
    "lens_make": "Canon"
  },
  "import_session_id": 5,  // RECOMMENDED - track import batch
  "image_file": {
    "filename": "IMG_1234.jpg",
    "file_path": "/Users/kjell/Photos/2024/IMG_1234.jpg",
    "file_size": 8234567,
    "file_format": "JPEG"
  },
  "rating": 0,
  "visibility": "private",
  "author_id": null,
  "category": null
}
```

**Response**: `201 Created` + PhotoEggResponse

**Desktop app implementation**:
```typescript
// 1. Process image locally with imalink-core
const photoegg = await localImalinkCore.processImage(filePath);

// 2. Send to backend
const response = await fetch('http://backend/api/v1/photos/photoegg', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    photo_egg: photoegg,
    import_session_id: currentImportSession.id,  // Track batch
    image_file: {
      filename: path.basename(filePath),
      file_path: filePath,
      file_size: fs.statSync(filePath).size,
      file_format: path.extname(filePath).substring(1).toUpperCase()
    },
    rating: 0,
    visibility: 'private'
  })
});
```

---

### 2. **POST /api/v1/photos/register-image** (Web app - CONVENIENCE)

**Purpose**: Quick web upload when user doesn't have desktop app

**Flow**:
1. Web app uploads raw image file
2. Backend → imalink-core (SERVER at https://core.trollfjell.com)
3. imalink-core → PhotoEgg
4. Backend stores photo

**⚠️ NOT RECOMMENDED FOR**: Batch imports (slow, file upload overhead)

**Request**:
```http
POST /api/v1/photos/register-image?rating=4&visibility=private
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <binary image data>
```

**Query parameters**:
- `import_session_id` (optional) - Defaults to protected "Quick Add"
- `rating` (optional, 0-5) - Star rating
- `visibility` (optional) - private|space|authenticated|public
- `author_id` (optional) - Photographer ID
- `coldpreview_size` (optional) - Size for larger preview (e.g., 2560)

**Response**: `201 Created` + PhotoEggResponse

**Web app implementation**:
```typescript
async function uploadPhoto(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    'http://backend/api/v1/photos/register-image?rating=4&visibility=private',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // NO Content-Type - browser sets it for multipart
      },
      body: formData
    }
  );
  
  if (!response.ok) {
    if (response.status === 503) {
      throw new Error('Image processing service unavailable');
    }
    throw new Error('Upload failed');
  }
  
  return await response.json();
}
```

---

## 📝 UPDATED SCHEMAS

### PhotoEggRequest (for POST /photoegg)

```typescript
interface PhotoEggRequest {
  photo_egg: PhotoEggCreate;      // PhotoEgg from imalink-core
  import_session_id?: number;     // Optional - defaults to protected session
  image_file?: ImageFileCreate;   // Optional - for desktop app file tracking
  rating?: number;                // 0-5 stars
  visibility?: string;            // private|space|authenticated|public
  author_id?: number;             // Optional photographer
  category?: string;              // NEW - user category
}
```

### PhotoEggCreate (from imalink-core)

```typescript
interface PhotoEggCreate {
  hothash: string;                    // SHA256 of hotpreview
  hotpreview_base64: string;          // 150x150px JPEG thumbnail (base64)
  coldpreview_base64?: string | null; // Optional larger preview
  hotpreview_width?: number;          // Actual hotpreview dimensions
  hotpreview_height?: number;
  coldpreview_width?: number | null;
  coldpreview_height?: number | null;
  primary_filename: string;           // Original filename
  width: number;                      // Original image dimensions
  height: number;
  taken_at?: string | null;           // ISO 8601 datetime
  camera_make?: string | null;
  camera_model?: string | null;
  gps_latitude?: number | null;
  gps_longitude?: number | null;
  has_gps: boolean;
  iso?: number | null;
  aperture?: number | null;
  shutter_speed?: string | null;
  focal_length?: number | null;
  lens_model?: string | null;
  lens_make?: string | null;
}
```

### PhotoEggResponse (returned by both endpoints)

```typescript
interface PhotoEggResponse {
  id: number;
  hothash: string;
  user_id: number;
  width: number;
  height: number;
  taken_at?: string | null;
  gps_latitude?: number | null;
  gps_longitude?: number | null;
  rating: number;
  category?: string | null;          // NEW
  visibility: string;
  created_at: string;
  updated_at: string;
  // Note: import_session_id may not be in response (optional field)
}
```

### ImportSession (updated)

```typescript
interface ImportSession {
  id: number;
  user_id: number;
  title: string;
  description?: string | null;
  is_protected: boolean;             // NEW - if true, cannot be deleted
  photo_count: number;
  created_at: string;
  updated_at: string;
}
```

---

## 🔧 IMPLEMENTATION CHECKLIST

### imalink-desktop

- [ ] **Remove** all references to `POST /api/v1/photos/new-photo`
- [ ] **Update** to use `POST /api/v1/photos/photoegg`
- [ ] **Create ImportSession** at start of each import batch
- [ ] **Pass import_session_id** when creating photos
- [ ] **Add category field** to photo metadata UI
- [ ] **Update PhotoEgg schema** to match latest imalink-core version
- [ ] **Handle protected ImportSession** (cannot delete "Quick Add")
- [ ] **Test** with actual image files and local imalink-core

### imalink-web

- [ ] **Implement** web upload using `POST /api/v1/photos/register-image`
- [ ] **Add category filter/selector** in photo grid
- [ ] **Show ImportSession** in photo details (read-only for web)
- [ ] **Handle 503 errors** when imalink-core is unavailable
- [ ] **Add upload progress** indicator (file upload can be slow)
- [ ] **Test** with various image formats (JPEG, PNG, etc.)
- [ ] **Verify** CORS settings allow multipart uploads
- [ ] **Update** photo list to show category

---

## 🚨 CRITICAL NOTES

### 1. **Image Processing Location**

**Desktop app flow**:
- ✅ Images processed LOCALLY (fast, no server load)
- ✅ Only metadata sent to server
- ✅ Original files stay on user's computer

**Web app flow**:
- ⚠️ Images uploaded to server (slow for large files)
- ⚠️ Server forwards to imalink-core for processing
- ⚠️ Original file NOT stored (only metadata + previews)

**Recommendation**: Use desktop app for batch imports, web for quick single uploads.

### 2. **imalink-core Endpoints**

**Desktop app**: 
- Connects to LOCAL imalink-core: `http://localhost:8001`
- Fast processing, no network latency

**Backend (for web uploads)**:
- Connects to SERVER imalink-core: `https://core.trollfjell.com`
- Configured in backend `.env`: `IMALINK_CORE_URL=https://core.trollfjell.com`

### 3. **Backward Compatibility**

**PhotoEgg v2.0 changes**:
- Added optional fields with defaults
- Old PhotoEggs (v1.0) still work
- Backend validates and fills missing fields

**If using older imalink-core**:
- Ensure it returns at least: `hothash`, `hotpreview_base64`, `width`, `height`, `primary_filename`
- All other fields can be null/missing

### 4. **Error Handling**

**POST /register-image specific errors**:
- `400` - Invalid image format or imalink-core processing failed
- `503` - imalink-core service unavailable (check server status)
- `422` - Missing required fields (file missing)

**Common errors (both endpoints)**:
- `401` - Unauthorized (missing/invalid token)
- `409` - Duplicate photo (same hothash already exists)

---

## 📊 Testing Recommendations

### Desktop app

```bash
# 1. Start local imalink-core
cd ~/imalink-core
uvicorn service.main:app --reload --port 8001

# 2. Test PhotoEgg endpoint
curl -X POST http://localhost:8000/api/v1/photos/photoegg \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @test_photoegg.json
```

### Web app

```bash
# 1. Ensure backend and imalink-core are running
# Backend: http://localhost:8000
# imalink-core: https://core.trollfjell.com

# 2. Test web upload
curl -X POST http://localhost:8000/api/v1/photos/register-image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_image.jpg" \
  -F "rating=4" \
  -F "visibility=private"
```

---

## 🔗 Additional Resources

- **Backend API Reference**: `docs/API_REFERENCE.md`
- **PhotoEgg Contract**: `docs/CONTRACTS.md`
- **imalink-core Repository**: https://github.com/kjelkols/imalink-core
- **Timeline API**: `docs/TIMELINE_API.md` (unchanged)

---

## 📞 Questions?

If you encounter issues implementing these changes, check:

1. **PhotoEgg schema mismatch**: Compare with imalink-core version
2. **Import session errors**: Ensure user has protected session (created on registration)
3. **CORS issues (web)**: Backend CORS allows multipart/form-data
4. **imalink-core connection**: Verify service is running and accessible

**Backend version**: Check `GET /api/v1/debug/routes` for available endpoints
**All tests passing**: 159 tests (including 8 new /register-image tests)
