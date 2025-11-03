# Photo and ImageFile Architecture

## Conceptual Model

### Photo = The Subject (Motivet)
A **Photo** represents **one unique photographic moment** - what the user sees in their gallery. This is the conceptual entity that users interact with: rate, tag, organize into stacks, and search for.

### ImageFile = Physical Representations
An **ImageFile** is a **physical file on disk** that can recreate the subject. One Photo can have multiple ImageFiles representing the same moment in different formats or processing stages.

## The Relationship

```
Photo (The Subject/Motiv)
├── ImageFile #1: IMG_1234.jpg     (JPEG - created the Photo)
├── ImageFile #2: IMG_1234.CR2     (RAW companion file)
├── ImageFile #3: IMG_1234_edit.tif (Edited version from Lightroom)
└── ImageFile #4: IMG_1234_print.jpg (Export for printing)
```

All these files belong to the **same Photo** because they represent the **same photographic moment**.

## Photo: Immutable Visual Identity

### Core Principle: "First File Wins"
When the first file is imported for a new photo:
1. **hotpreview** (150x150 thumbnail) is generated from this file
2. **hothash** (SHA256 of hotpreview) becomes the Photo's permanent ID
3. **exif_dict** is extracted from this file for presentation

**These values never change** - they establish the Photo's permanent identity.

### What Photo Stores

#### Visual Data (Immutable)
- `hotpreview` - 150x150px thumbnail (BLOB) - for gallery views
- `hothash` - SHA256 hash of hotpreview (Primary Key)
- `exif_dict` - Selected EXIF data for UI presentation (JSON)
- `width`, `height` - Image dimensions

#### Content Metadata (From EXIF)
- `taken_at` - When photo was captured
- `gps_latitude`, `gps_longitude` - GPS coordinates

#### User Metadata (Editable)
- `rating` - 1-5 star rating
- `author_id` - Photographer
- `tags` - User-applied tags
- `stack_id` - Optional photo stack membership

#### Corrections (Non-destructive)
- `timeloc_correction` - Time/location fixes
- `view_correction` - Display adjustments (rotation, crop, exposure)

#### Ownership & Organization
- `user_id` - Owner of this photo
- `import_session_id` - Which import batch this came from

#### Preview for Detail View
- `coldpreview_path` - Path to medium-size preview (800-1200px)

## ImageFile: Flexible File Collection

### What ImageFile Stores

#### File Information
- `filename` - Name and extension (e.g., "IMG_1234.jpg")
- `file_size` - Size in bytes
- `photo_hothash` - Link to parent Photo

#### Import Tracking (Per-File)
- `imported_time` - When THIS specific file was imported
- `imported_info` - Import context and original location (JSON)

#### Storage Locations (Current)
- `local_storage_info` - Where to find file locally (JSON)
- `cloud_storage_info` - Cloud storage details (JSON)

### File Types Supported

1. **JPEG** - Fast, compressed, ready-to-display
2. **RAW** (CR2, NEF, ARW, DNG, ORF, RW2) - Maximum quality, sensor data
3. **Edited formats** (TIF, TIFF, PSD) - Processed versions
4. **Export formats** - Any other format representing the same subject

## Key Design Principles

### 1. First File Defines Identity
The first imported file (master) establishes:
- Photo's visual identity (hotpreview → hothash)
- Presentation metadata (exif_dict)

**This is pragmatic and works well because:**
- JPEG and RAW from same camera capture have virtually identical EXIF for selected parameters
- hotpreview is "good enough" for gallery thumbnails
- Original EXIF can always be re-read from files when needed

### 2. EXIF Dict is for Presentation Only
`exif_dict` contains selected fields for UI display:
- Camera make/model
- Lens information
- Exposure settings (ISO, aperture, shutter speed)
- Flash status

**For detailed analysis**, read original EXIF directly from ImageFiles.

### 3. Import Order Doesn't Matter (Much)

#### Scenario A: JPEG First
```
1. Import IMG_1234.jpg → Photo created with JPEG's hotpreview/exif
2. Import IMG_1234.CR2 → Added as companion ImageFile
```

#### Scenario B: RAW First
```
1. Import IMG_1234.CR2 → Photo created with RAW's hotpreview/exif
2. Import IMG_1234.jpg → Added as companion ImageFile
```

Both scenarios work! The system is flexible about import order.

### 4. Edited Files are Additional ImageFiles
After importing originals (JPEG/RAW):
1. User edits in Lightroom/Photoshop
2. Exports edited version (TIF, PSD, etc.)
3. Edited file is added via `POST /image-files/add-to-photo`
4. System can use edited file for better quality coldpreview or export

**Edited files do NOT change:**
- Photo's hothash (remains based on original hotpreview)
- Photo's exif_dict (remains from master file)

### 5. Coldpreview Uses Best Available Source
While **hotpreview is immutable**, **coldpreview can be regenerated** from the best available file:

**Priority for coldpreview generation:**
1. Edited files (TIF, PSD) - highest quality, color-corrected
2. JPEG files - fast processing, good quality
3. RAW files - maximum quality, slower processing

**Priority for export/printing:**
1. Edited files - user's final vision
2. RAW files - maximum quality for processing
3. JPEG files - ready-to-use fallback

## Access Control and Ownership

### Photo Level (User-Facing)
- Every Photo has `user_id` - establishes ownership
- All Photo operations check user permissions
- Photos are exposed via REST API endpoints

### ImageFile Level (Internal Only)
- **NO `user_id` field** - ownership inherited from Photo
- **NO direct API access** - all operations via Photo
- Cascade deletion: When Photo is deleted, all ImageFiles are deleted
- Pure implementation detail for file management

## Database Relationships

```python
# Photo owns ImageFiles (cascade delete)
Photo.image_files → [ImageFile, ImageFile, ...]

# ImageFile belongs to one Photo
ImageFile.photo_hothash → Photo.hothash

# Import tracking at Photo level
Photo.import_session_id → ImportSession

# User owns Photos (not ImageFiles)
User.photos → [Photo, Photo, ...]
```

## Important Notes

### For Developers
1. **Never expose ImageFile directly via API** - always access through Photo
2. **Photo.hothash is immutable** - perfect for stable references, URLs, tags
3. **First imported file is master** - designs the Photo's identity
4. **Edited files are variants** - same subject, potentially different appearance

### For Users
1. **One Photo = One Moment** - regardless of how many files (JPEG, RAW, edited)
2. **First import matters** - determines thumbnail and presentation metadata
3. **Import originals first** - then add edited versions later
4. **Ratings/tags stay with Photo** - not individual files

### Edge Cases
**What if heavily edited version is imported first?**
- Photo gets identity from edited version (hotpreview/exif from edited file)
- Later import of originals adds them as ImageFiles
- Not ideal but system handles it
- **Best practice**: Import originals (JPEG/RAW) first, edited versions later

## Summary Table

| Aspect | Photo | ImageFile |
|--------|-------|-----------|
| **Represents** | Photographic moment/subject | Physical file on disk |
| **Identity** | hothash (from hotpreview) | id (auto-increment) |
| **Mutability** | User metadata editable | Immutable after creation |
| **Visual Data** | hotpreview (fixed), coldpreview (regenerable) | None |
| **EXIF** | exif_dict (presentation) | Original files have full EXIF |
| **Ownership** | user_id | Inherited from Photo |
| **API Access** | Full REST API | None (internal only) |
| **Deletion** | User can delete | Cascade from Photo |
| **Multiplicity** | One per subject | Many per Photo |

## Workflows

### Initial Import (JPEG + RAW)
```
POST /api/v1/image-files/new-photo
- Upload: IMG_1234.jpg + hotpreview + exif_dict
- System: Generate hothash from hotpreview
- System: Create Photo with provided data
- System: Create ImageFile linked to Photo
- Result: Photo with 1 ImageFile

POST /api/v1/image-files/add-to-photo
- Upload: IMG_1234.CR2 (specify photo_hothash)
- System: Create ImageFile linked to existing Photo
- Result: Photo with 2 ImageFiles (JPEG + RAW)
```

### Adding Edited Version
```
POST /api/v1/image-files/add-to-photo
- Upload: IMG_1234_edit.tif (specify photo_hothash)
- System: Create ImageFile linked to existing Photo
- Optional: Regenerate coldpreview from edited file
- Result: Photo with 3 ImageFiles (JPEG + RAW + edited)
```

### Using Best Quality for Export
```
GET /api/v1/photos/{hothash}/export
- System: Find best ImageFile (edited > RAW > JPEG)
- System: Read full file and return
- User: Gets highest quality version available
```
