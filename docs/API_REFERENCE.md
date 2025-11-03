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

**IMPORTANT for Frontend Integration:**
- All POST/PUT requests must include: `Content-Type: application/json`
- All requests (except login/register) must include: `Authorization: Bearer <token>`
- Dates must be in ISO 8601 format: `"2025-10-15T14:30:00Z"`
- Base64 data can include data URL prefix or be raw: `"data:image/jpeg;base64,..."` or just the Base64 string

**Quick Start - Upload Your First Photo:**
```javascript
// 1. Get authentication token (do this once)
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'myuser', password: 'mypass' })
});
const { access_token } = await loginResponse.json();

// 2. Create 150x150px thumbnail (hotpreview) from your image
const canvas = document.createElement('canvas');
canvas.width = 150;
canvas.height = 150;
const ctx = canvas.getContext('2d');
ctx.drawImage(yourImage, 0, 0, 150, 150);
const hotpreview = canvas.toDataURL('image/jpeg', 0.85); // Includes data URL prefix

// 3. Upload the photo
const response = await fetch('http://localhost:8000/api/v1/photos/new-photo', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    filename: 'my_photo.jpg',
    hotpreview: hotpreview,  // Can include "data:image/jpeg;base64," prefix
    file_size: 2048576,
    exif_dict: { Make: 'Canon', Model: 'EOS R5' }  // Optional
  })
});

const result = await response.json();
console.log('Photo created:', result.photo_hothash);
```

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
### Update Photo Time/Location Correction

**Endpoint:** `PATCH /api/v1/photos/{hothash}/timeloc-correction`

**Authentication:** Required (JWT token)

**Description:** Apply non-destructive corrections to photo timestamp and GPS location. Original EXIF data is preserved; corrections override display values only.

**Path Parameters:**
- `hothash` (string, required) - Photo's unique hotpreview hash

**Request Body:**
```json
{
  "taken_at": "2024-03-15T14:30:00Z",  // ISO 8601 format, optional
  "gps_latitude": 59.9139,              // decimal degrees, optional
  "gps_longitude": 10.7522,             // decimal degrees, optional
  "correction_reason": "Camera clock was 2 hours ahead"  // optional, user note
}
```

**Special Behavior - Restore from EXIF:**
Send `null` as entire request body to restore all values from original EXIF:
```json
null
```
This will:
1. Delete the `timeloc_correction` JSON (set to `null`)
2. Re-parse `ImageFile.exif_dict` for original values
3. Update `Photo.taken_at`, `gps_latitude`, `gps_longitude` with EXIF values (or `null`/`0` if not found)

**Response (200 OK):**
```json
{
  "hothash": "abc123...",
  "taken_at": "2024-03-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "timeloc_correction": {
    "taken_at": "2024-03-15T14:30:00Z",
    "gps_latitude": 59.9139,
    "gps_longitude": 10.7522,
    "correction_reason": "Camera clock was 2 hours ahead",
    "corrected_at": "2024-10-22T10:15:00Z",
    "corrected_by": 1
  }
}
```

**Response after null request (200 OK):**
```json
{
  "hothash": "abc123...",
  "taken_at": "2024-03-15T12:30:00Z",  // restored from EXIF
  "gps_latitude": 59.9139,              // restored from EXIF
  "gps_longitude": 10.7522,             // restored from EXIF
  "timeloc_correction": null            // correction removed
}
```

**Error Responses:**
- `404 Not Found` - Photo not found
- `401 Unauthorized` - No valid token
- `422 Unprocessable Entity` - Invalid data format

**Implementation Notes:**
1. **First correction**: `timeloc_correction` is created with provided fields + metadata
2. **Update correction**: Existing `timeloc_correction` is updated (merge with new fields)
3. **Restore from EXIF**: `timeloc_correction` set to `null`, Photo fields restored from `ImageFile.exif_dict`

**Database Schema:**
```python
# Photo model fields affected:
taken_at: datetime | None           # Display value (EXIF or corrected)
gps_latitude: float | None          # Display value (EXIF or corrected)
gps_longitude: float | None         # Display value (EXIF or corrected)
timeloc_correction: JSON | None     # Correction metadata + values

# timeloc_correction JSON structure:
{
  "taken_at": "2024-03-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "correction_reason": "User explanation",
  "corrected_at": "2024-10-22T10:15:00Z",  # auto-set
  "corrected_by": 1                         # user_id, auto-set
}
```

**Backend Logic:**

```python
# Scenario 1: NULL request - Restore from EXIF
if request_body is None:
    photo.timeloc_correction = None
    photo.taken_at = parse_exif_datetime(image_file.exif_dict) or None
    photo.gps_latitude = parse_exif_gps_lat(image_file.exif_dict) or 0.0
    photo.gps_longitude = parse_exif_gps_lon(image_file.exif_dict) or 0.0

# Scenario 2: First correction or update
else:
    correction = photo.timeloc_correction or {}
    if request.taken_at is not None:
        correction["taken_at"] = request.taken_at
        photo.taken_at = request.taken_at
    if request.gps_latitude is not None:
        correction["gps_latitude"] = request.gps_latitude
        photo.gps_latitude = request.gps_latitude
    if request.gps_longitude is not None:
        correction["gps_longitude"] = request.gps_longitude
        photo.gps_longitude = request.gps_longitude
    if request.correction_reason:
        correction["correction_reason"] = request.correction_reason
    
    correction["corrected_at"] = datetime.utcnow()
    correction["corrected_by"] = current_user.id
    photo.timeloc_correction = correction
```

---

### Update Photo View Correction

**Endpoint:** `PATCH /api/v1/photos/{hothash}/view-correction`

**Authentication:** Required (JWT token)

**Description:** Store frontend display preferences for rotation, cropping, and exposure adjustments. **No server-side image processing** - these are rendering hints for clients only.

**Path Parameters:**
- `hothash` (string, required) - Photo's unique hotpreview hash

**Request Body:**
```json
{
  "rotation": 90,           // 0, 90, 180, 270 degrees, optional
  "relative_crop": {        // Normalized coordinates 0.0-1.0, optional
    "x": 0.1,               // Left edge (0.0 = left, 1.0 = right)
    "y": 0.1,               // Top edge (0.0 = top, 1.0 = bottom)
    "width": 0.8,           // Width (0.0-1.0)
    "height": 0.8           // Height (0.0-1.0)
  },
  "exposure_adjust": 0.5    // -2.0 to +2.0, optional
}
```

**Validation Rules:**
- `rotation`: Must be 0, 90, 180, or 270
- `relative_crop.x`: 0.0 ≤ x < 1.0
- `relative_crop.y`: 0.0 ≤ y < 1.0
- `relative_crop.width`: 0.0 < width ≤ 1.0
- `relative_crop.height`: 0.0 < height ≤ 1.0
- `x + width ≤ 1.0` (crop must stay within image bounds)
- `y + height ≤ 1.0` (crop must stay within image bounds)
- `exposure_adjust`: -2.0 ≤ value ≤ 2.0

**Special Behavior - Reset to Defaults:**
Send `null` as entire request body to remove all view corrections:
```json
null
```

**Response (200 OK):**
```json
{
  "hothash": "abc123...",
  "view_correction": {
    "rotation": 90,
    "relative_crop": {
      "x": 0.1,
      "y": 0.1,
      "width": 0.8,
      "height": 0.8
    },
    "exposure_adjust": 0.5,
    "corrected_at": "2024-10-22T10:20:00Z",
    "corrected_by": 1
  }
}
```

**Response after null request (200 OK):**
```json
{
  "hothash": "abc123...",
  "view_correction": null
}
```

**Error Responses:**
- `404 Not Found` - Photo not found
- `401 Unauthorized` - No valid token
- `422 Unprocessable Entity` - Invalid data format or out-of-range values

**Implementation Notes:**
1. Backend **only stores** the JSON - no image processing
2. Frontend applies these settings during rendering
3. Relative crop uses normalized coordinates for resolution independence
4. `null` request removes all view corrections

**Database Schema:**
```python
# Photo model field:
view_correction: JSON | None

# view_correction JSON structure:
{
  "rotation": 90,
  "relative_crop": {
    "x": 0.1,
    "y": 0.1,
    "width": 0.8,
    "height": 0.8
  },
  "exposure_adjust": 0.5,
  "corrected_at": "2024-10-22T10:20:00Z",  # auto-set
  "corrected_by": 1                         # user_id, auto-set
}
```

**Frontend Rendering Example:**

```python
# Apply view corrections to image display
if photo.view_correction:
    vc = photo.view_correction
    
    # 1. Apply rotation
    if vc.get("rotation"):
        image = image.rotate(vc["rotation"])
    
    # 2. Apply relative crop (convert to pixel coordinates)
    if crop := vc.get("relative_crop"):
        width, height = image.size
        x = int(crop["x"] * width)
        y = int(crop["y"] * height)
        w = int(crop["width"] * width)
        h = int(crop["height"] * height)
        image = image.crop((x, y, x + w, y + h))
    
    # 3. Apply exposure adjustment
    if exp := vc.get("exposure_adjust"):
        enhancer = ImageEnhance.Brightness(image)
        # exposure -2.0 to +2.0 maps to brightness 0.5 to 1.5
        brightness = 1.0 + (exp * 0.25)
        image = enhancer.enhance(brightness)
```

**Backend Logic:**

```python
# Scenario 1: NULL request - Remove corrections
if request_body is None:
    photo.view_correction = None

# Scenario 2: Update corrections
else:
    correction = photo.view_correction or {}
    
    if request.rotation is not None:
        if request.rotation not in [0, 90, 180, 270]:
            raise ValidationError("rotation must be 0, 90, 180, or 270")
        correction["rotation"] = request.rotation
    
    if request.relative_crop is not None:
        crop = request.relative_crop
        # Validate bounds
        if not (0 <= crop.x < 1 and 0 <= crop.y < 1):
            raise ValidationError("crop x,y must be 0-1")
        if not (0 < crop.width <= 1 and 0 < crop.height <= 1):
            raise ValidationError("crop width,height must be 0-1")
        if crop.x + crop.width > 1 or crop.y + crop.height > 1:
            raise ValidationError("crop exceeds image bounds")
        correction["relative_crop"] = crop
    
    if request.exposure_adjust is not None:
        if not (-2.0 <= request.exposure_adjust <= 2.0):
            raise ValidationError("exposure_adjust must be -2.0 to +2.0")
        correction["exposure_adjust"] = request.exposure_adjust
    
    correction["corrected_at"] = datetime.utcnow()
    correction["corrected_by"] = current_user.id
    photo.view_correction = correction
```

---

## 🏷️ Photo Tags

Photo tags enable flexible organization and search using user-defined keywords. Tags are user-scoped (each user has their own vocabulary) and support many-to-many relationships with photos.

### List All Tags

**Endpoint:** `GET /api/v1/tags`

**Authentication:** Required (JWT token)

**Description:** Get all tags for current user with photo counts.

**Query Parameters:**
- `sort_by` (string, optional) - Sort order: `name` (default), `count`, `created_at`
- `order` (string, optional) - Sort direction: `asc` (default), `desc`

**Response (200 OK):**
```json
{
  "tags": [
    {
      "id": 1,
      "name": "landscape",
      "photo_count": 245,
      "created_at": "2024-10-20T10:00:00Z",
      "updated_at": "2024-10-22T15:30:00Z"
    },
    {
      "id": 2,
      "name": "sunset",
      "photo_count": 89,
      "created_at": "2024-10-20T11:30:00Z",
      "updated_at": "2024-10-22T14:20:00Z"
    }
  ],
  "total": 2
}
```

**Implementation Notes:**
- Returns only tags belonging to current user
- `photo_count` is calculated via COUNT on `photo_tags` association table
- Tags without photos are still included (count = 0)

---

### Tag Autocomplete

**Endpoint:** `GET /api/v1/tags/autocomplete`

**Authentication:** Required (JWT token)

**Description:** Get tag suggestions for autocomplete while typing. Fast prefix-matching search.

**Query Parameters:**
- `q` (string, required) - Search query (minimum 1 character)
- `limit` (integer, optional) - Max results (default: 10, max: 50)

**Response (200 OK):**
```json
{
  "suggestions": [
    {
      "id": 1,
      "name": "landscape",
      "photo_count": 245
    },
    {
      "id": 15,
      "name": "land",
      "photo_count": 12
    }
  ]
}
```

**Example Usage:**
```http
GET /api/v1/tags/autocomplete?q=land&limit=5
```

**Implementation Notes:**
- Case-insensitive prefix matching: `q=land` matches "landscape", "landmark", "land"
- Results ordered by photo count (descending) for most relevant suggestions
- Only returns user's own tags

---

### Add Tags to Photo

**Endpoint:** `POST /api/v1/photos/{hothash}/tags`

**Authentication:** Required (JWT token)

**Description:** Add one or more tags to a photo. Tags are created automatically if they don't exist. Duplicate tags are silently ignored.

**Path Parameters:**
- `hothash` (string, required) - Photo's unique hotpreview hash

**Request Body:**
```json
{
  "tags": ["landscape", "sunset", "norway"]
}
```

**Alternative (single tag):**
```json
{
  "tags": ["vacation"]
}
```

**Response (200 OK):**
```json
{
  "hothash": "abc123...",
  "tags": [
    {
      "id": 1,
      "name": "landscape"
    },
    {
      "id": 2,
      "name": "sunset"
    },
    {
      "id": 3,
      "name": "norway"
    }
  ],
  "added": 3,
  "skipped": 0
}
```

**Response with duplicates (200 OK):**
```json
{
  "hothash": "abc123...",
  "tags": [
    {
      "id": 1,
      "name": "landscape"
    },
    {
      "id": 2,
      "name": "sunset"
    }
  ],
  "added": 1,
  "skipped": 1,
  "message": "Tag 'landscape' was already applied to this photo"
}
```

**Error Responses:**
- `404 Not Found` - Photo not found
- `401 Unauthorized` - No valid token
- `422 Unprocessable Entity` - Invalid tag format

**Validation Rules:**
- Tag names are normalized to lowercase
- Tag names must be 1-50 characters
- Only alphanumeric, space, hyphen, underscore allowed
- Leading/trailing whitespace is trimmed

**Implementation Notes:**
1. Check if tags exist in user's tag vocabulary
2. Create new tags if needed (user-scoped)
3. Create associations in `photo_tags` table
4. Skip if association already exists (no error)
5. Return updated list of all tags for photo

---

### Remove Tag from Photo

**Endpoint:** `DELETE /api/v1/photos/{hothash}/tags/{tag_name}`

**Authentication:** Required (JWT token)

**Description:** Remove a specific tag from a photo. The tag itself remains in the database for reuse.

**Path Parameters:**
- `hothash` (string, required) - Photo's unique hotpreview hash
- `tag_name` (string, required) - Tag name to remove (case-insensitive)

**Response (200 OK):**
```json
{
  "hothash": "abc123...",
  "removed_tag": "landscape",
  "remaining_tags": [
    {
      "id": 2,
      "name": "sunset"
    },
    {
      "id": 3,
      "name": "norway"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found` - Photo or tag not found
- `401 Unauthorized` - No valid token

**Implementation Notes:**
- Only removes association in `photo_tags` table
- Tag remains in `tags` table (can be reused)
- Case-insensitive tag name matching

---

### Delete Tag Completely

**Endpoint:** `DELETE /api/v1/tags/{tag_id}`

**Authentication:** Required (JWT token)

**Description:** Permanently delete a tag and remove it from all photos. Use with caution.

**Path Parameters:**
- `tag_id` (integer, required) - Tag ID to delete

**Response (200 OK):**
```json
{
  "deleted_tag": "landscape",
  "photos_affected": 245,
  "message": "Tag 'landscape' deleted from 245 photos"
}
```

**Error Responses:**
- `404 Not Found` - Tag not found or doesn't belong to user
- `401 Unauthorized` - No valid token

**Implementation Notes:**
- Cascade deletes all `photo_tags` associations
- Only allows deletion of user's own tags

---

### Rename Tag

**Endpoint:** `PUT /api/v1/tags/{tag_id}`

**Authentication:** Required (JWT token)

**Description:** Rename a tag. The new name applies to all photos using this tag.

**Path Parameters:**
- `tag_id` (integer, required) - Tag ID to rename

**Request Body:**
```json
{
  "new_name": "seascape"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "old_name": "landscape",
  "new_name": "seascape",
  "photo_count": 245,
  "updated_at": "2024-10-22T16:45:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Tag not found or doesn't belong to user
- `409 Conflict` - Tag with new name already exists for user
- `401 Unauthorized` - No valid token
- `422 Unprocessable Entity` - Invalid tag name format

---

### Search Photos by Tags

**Endpoint:** `GET /api/v1/photos`

**Authentication:** Required (JWT token)

**Description:** Search photos using tag filters. Supports AND/OR logic for multiple tags.

**Query Parameters:**
- `tags` (string, optional) - Comma-separated tag names: `tags=landscape,sunset`
- `tag_logic` (string, optional) - Logic operator: `AND` (default) or `OR`
- `offset` (integer, optional) - Pagination offset (default: 0)
- `limit` (integer, optional) - Results per page (default: 50, max: 500)

**Example - Photos with ALL specified tags:**
```http
GET /api/v1/photos?tags=landscape,norway&tag_logic=AND
```

**Example - Photos with ANY specified tag:**
```http
GET /api/v1/photos?tags=sunset,sunrise&tag_logic=OR
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "hothash": "abc123...",
      "tags": [
        {"id": 1, "name": "landscape"},
        {"id": 3, "name": "norway"}
      ],
      "taken_at": "2024-08-15T18:30:00Z",
      ...
    }
  ],
  "total": 42,
  "offset": 0,
  "limit": 50
}
```

**Implementation Notes:**

**AND Logic (default):**
```sql
-- Photo must have ALL specified tags
SELECT p.* FROM photos p
INNER JOIN photo_tags pt1 ON p.hothash = pt1.photo_hothash
INNER JOIN tags t1 ON pt1.tag_id = t1.id AND t1.name = 'landscape'
INNER JOIN photo_tags pt2 ON p.hothash = pt2.photo_hothash  
INNER JOIN tags t2 ON pt2.tag_id = t2.id AND t2.name = 'norway'
WHERE p.user_id = ?
```

**OR Logic:**
```sql
-- Photo must have AT LEAST ONE specified tag
SELECT DISTINCT p.* FROM photos p
INNER JOIN photo_tags pt ON p.hothash = pt.photo_hothash
INNER JOIN tags t ON pt.tag_id = t.id
WHERE p.user_id = ? AND t.name IN ('sunset', 'sunrise')
```

---

### Database Schema

```python
# models/tag.py
class Tag(Base, TimestampMixin):
    """User-scoped tag for photo categorization"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(50), nullable=False)  # Lowercase normalized
    
    # Unique constraint per user
    __table_args__ = (
        Index('idx_user_tag', 'user_id', 'name', unique=True),
    )
    
    user = relationship("User", back_populates="tags")
    photos = relationship("Photo", secondary="photo_tags", back_populates="tags")

# Association table (many-to-many)
class PhotoTag(Base):
    """Association between Photos and Tags"""
    __tablename__ = "photo_tags"
    
    photo_hothash = Column(String(64), ForeignKey('photos.hothash'), 
                           primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), 
                    primary_key=True, index=True)
    tagged_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite index for reverse lookup
    __table_args__ = (
        Index('idx_tag_photos', 'tag_id', 'photo_hothash'),
    )

# Photo model addition
class Photo(Base):
    # ... existing fields ...
    tags = relationship("Tag", secondary="photo_tags", back_populates="photos")
```

**Key Design Decisions:**
1. **User-scoped**: `(user_id, name)` unique constraint prevents duplicates per user
2. **Normalized**: Tag strings stored once, reused across photos (efficient)
3. **Case-insensitive**: All tag names converted to lowercase
4. **Timestamped**: `tagged_at` tracks when tag was applied to photo
5. **Indexed**: Fast lookups via `idx_user_tag` and `idx_tag_photos`

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

**Returns:** JPEG image (150x150px thumbnail) as binary data

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
  "hotpreview": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "file_size": 2048576,
  "exif_dict": {
    "Make": "Canon",
    "Model": "EOS R5",
    "DateTime": "2025:10:15 14:30:00",
    "ImageWidth": 4000,
    "ImageHeight": 3000
  },
  "taken_at": "2025-10-15T14:30:00Z",
  "gps_latitude": 59.9139,
  "gps_longitude": 10.7522,
  "import_session_id": 5,
  "imported_info": {
    "original_path": "/path/to/original.jpg"
  },
  "local_storage_info": {
    "path": "/storage/photos/IMG_001.jpg"
  }
}
```

**Description:** Create a new Photo with its first ImageFile. This is the primary way to add new photos to the system.

**Required Fields:**
- `filename` (string): Original filename with extension
- `hotpreview` (string): Base64-encoded JPEG thumbnail (150x150px recommended)
  - Can be with data URL prefix: `"data:image/jpeg;base64,<data>"`
  - Or just the Base64 data: `"<base64_data>"`
  - Used to generate the Photo's unique `hothash` (SHA256)

**Optional Fields:**
- `file_size` (integer): File size in bytes
- `exif_dict` (object): Parsed EXIF metadata as JSON
  - Should include `ImageWidth` and `ImageHeight` if available
  - All other EXIF tags as key-value pairs
- `taken_at` (datetime): When photo was taken (ISO 8601 format)
- `gps_latitude` (float): GPS latitude (-90 to 90)
- `gps_longitude` (float): GPS longitude (-180 to 180)
- `import_session_id` (integer): ID of import session
- `imported_info` (object): Import context (original path, source, etc.)
- `local_storage_info` (object): Local storage metadata
- `cloud_storage_info` (object): Cloud storage metadata

**Response** (`201 Created`):
```json
{
  "image_file_id": 123,
  "photo_hothash": "abc123def456789...",
  "photo_created": true,
  "success": true,
  "message": "New photo created successfully",
  "filename": "IMG_001.jpg",
  "file_size": 2048576
}
```

**Error Responses:**
- `409 Conflict` - Photo with this hotpreview already exists (duplicate)
  ```json
  {
    "detail": "Photo with this image already exists. Use POST /photos/{hothash}/files to add companion files."
  }
  ```
- `400 Bad Request` - Validation error
  ```json
  {
    "detail": "Validation error: <error details>"
  }
  ```
- `422 Unprocessable Entity` - Invalid field values
- `500 Internal Server Error` - Server error (check logs for details)

### Add ImageFile to Existing Photo
```http
POST /api/v1/photos/{hothash}/files
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "IMG_001.CR2",
  "file_size": 25000000,
  "import_session_id": 5,
  "imported_info": {
    "original_path": "/path/to/original.CR2"
  },
  "local_storage_info": {
    "path": "/storage/photos/IMG_001.CR2"
  }
}
```

**Description:** Add a companion ImageFile (e.g., RAW, different resolution) to an existing Photo. No hotpreview needed since the Photo already exists.

**Path Parameters:**
- `hothash` (string): The 64-character hash of the existing Photo

**Required Fields:**
- `filename` (string): Filename with extension

**Optional Fields:**
- `file_size` (integer): File size in bytes
- `import_session_id` (integer): ID of import session
- `imported_info` (object): Import context
- `local_storage_info` (object): Local storage metadata
- `cloud_storage_info` (object): Cloud storage metadata

**Note:** The `photo_hothash` field is NOT sent in the request body - it's taken from the URL path parameter.

**Use Cases:**
- Adding RAW file when JPEG already imported
- Adding different resolution of same photo
- Adding edited version to original

**Response** (`201 Created`):
```json
{
  "image_file_id": 124,
  "photo_hothash": "abc123def456789...",
  "photo_created": false,
  "success": true,
  "message": "Image file added to existing photo successfully",
  "filename": "IMG_001.CR2",
  "file_size": 25000000
}
```

**Error Responses:**
- `404 Not Found` - Photo with this hothash doesn't exist
  ```json
  {
    "detail": "Photo with hothash 'abc123...' not found. Use POST /photos/new-photo to create new photo."
  }
  ```
- `400 Bad Request` - Validation error
- `422 Unprocessable Entity` - Invalid field values
- `500 Internal Server Error` - Server error

### Troubleshooting Photo Upload

**Problem: Getting 500 Internal Server Error**

Check the server logs for detailed error messages. Common issues:

1. **Invalid hotpreview data:**
   ```
   ERROR: Validation error creating photo: Invalid hotpreview Base64 data
   ```
   - Solution: Ensure hotpreview is valid Base64-encoded JPEG
   - Must be at least 10 bytes after decoding
   - Can include or exclude `data:image/jpeg;base64,` prefix

2. **Missing required fields:**
   ```
   ERROR: Request data details - filename: None, hotpreview_size: 0
   ```
   - Solution: Both `filename` and `hotpreview` are required

3. **Invalid datetime format:**
   ```
   ERROR: Invalid datetime format for taken_at
   ```
   - Solution: Use ISO 8601 format: `"2025-10-15T14:30:00Z"`

**Problem: Getting 409 Conflict (Duplicate)**

This means a Photo with the same hotpreview already exists.
- The system generates a unique `hothash` from the hotpreview
- If you want to add another file for the same photo (e.g., RAW), use `POST /photos/{hothash}/files`

**Problem: Getting 422 Validation Error**

Check the response detail for specific field validation errors:
- `gps_latitude` must be between -90 and 90
- `gps_longitude` must be between -180 and 180
- `file_size` must be >= 0
- `filename` must be 1-255 characters

**Debug Logging:**

Server logs will show:
```
DEBUG: Creating new photo for user 123
DEBUG: Request data: filename=IMG_001.jpg, has_hotpreview=True, file_size=2048576, has_exif=True
```

If you see:
```
ERROR: Unexpected error creating photo with file: <details>
```

This indicates a server-side issue. Check:
- Database connection
- File permissions
- Server configuration

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
- 150x150px JPEG thumbnail
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

## 📊 System & Monitoring

### Get Database Statistics
Get comprehensive statistics about database tables, storage usage, and disk space.

```http
GET /api/v1/database-stats
```

**Authentication:** ❌ **Not required** - This endpoint is intended for system monitoring.

**Response** (`200 OK`):
```json
{
  "tables": {
    "photos": {
      "name": "photos",
      "record_count": 45,
      "size_bytes": 4612096,
      "size_mb": 4.4
    },
    "image_files": {
      "name": "image_files",
      "record_count": 45,
      "size_bytes": 92160,
      "size_mb": 0.09
    },
    "users": {
      "name": "users",
      "record_count": 2,
      "size_bytes": 8192,
      "size_mb": 0.01
    },
    "authors": {
      "name": "authors",
      "record_count": 3,
      "size_bytes": 12288,
      "size_mb": 0.01
    },
    "tags": {
      "name": "tags",
      "record_count": 15,
      "size_bytes": 24576,
      "size_mb": 0.02
    },
    "import_sessions": {
      "name": "import_sessions",
      "record_count": 1,
      "size_bytes": 4096,
      "size_mb": 0.0
    },
    "photo_stacks": {
      "name": "photo_stacks",
      "record_count": 0,
      "size_bytes": 0,
      "size_mb": 0.0
    }
  },
  "coldstorage": {
    "path": "/mnt/c/temp/00imalink_data/coldpreviews",
    "total_files": 45,
    "total_size_bytes": 6656400,
    "total_size_mb": 6.35,
    "total_size_gb": 0.01
  },
  "database_file": "/mnt/c/temp/00imalink_data/imalink.db",
  "database_size_bytes": 8392704,
  "database_size_mb": 8.0
}
```

**Response Fields:**

- `tables`: Dictionary of table statistics
  - `name`: Table name
  - `record_count`: Number of records in table
  - `size_bytes`: Approximate size on disk in bytes
  - `size_mb`: Approximate size on disk in megabytes

- `coldstorage`: Cold storage (coldpreview files) statistics
  - `path`: Storage directory path
  - `total_files`: Number of coldpreview files
  - `total_size_bytes`: Total size in bytes
  - `total_size_mb`: Total size in megabytes
  - `total_size_gb`: Total size in gigabytes

- `database_file`: Path to database file
- `database_size_bytes`: Total database file size in bytes
- `database_size_mb`: Total database file size in megabytes

**Use Cases:**
- System monitoring dashboards
- Storage space alerts
- Database maintenance scheduling
- Performance analysis
- Capacity planning

**Example - Python:**
```python
import requests

response = requests.get("http://localhost:8000/api/v1/database-stats")
stats = response.json()

print(f"Total photos: {stats['tables']['photos']['record_count']}")
print(f"Database size: {stats['database_size_mb']} MB")
print(f"Coldstorage size: {stats['coldstorage']['total_size_gb']} GB")
```

**Example - cURL:**
```bash
curl http://localhost:8000/api/v1/database-stats
```

**Notes:**
- Table sizes are approximate for SQLite (uses dbstat when available)
- Coldstorage includes all coldpreview files (800-1200px JPEG previews)
- Read-only operation with minimal overhead - safe to call frequently

---

**Last Updated:** October 24, 2025  
**API Version:** 2.1 (100% Photo-Centric)  
**Backend Version:** Fase 1 (Multi-User + PhotoStacks + Photo-Centric API)
