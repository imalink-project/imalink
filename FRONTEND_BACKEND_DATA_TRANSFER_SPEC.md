# Frontend-to-Backend Data Transfer Process
## Detailed Step-by-Step Photo Group Processing

**Version:** 1.0  
**Date:** October 2025  
**Purpose:** Complete specification of data transfer and server-side processing  

---

## Overview

This document details the exact process of transferring processed image data from frontend to backend, and how the backend creates Photo and Image objects from this data. The frontend sends structured JSON data with EXIF metadata and hotpreviews, while the backend handles database operations.

---

## 1. Frontend Data Preparation

### 1.1 Photo Group Structure
After frontend processing, each photo group is structured as:

```typescript
interface PhotoGroup {
  basename: string;           // e.g., "IMG_1234"
  hothash: string;           // Content hash for duplicate detection
  hotpreview: string;        // Base64 JPEG thumbnail (primary file only)
  exifData: ExifMetadata;    // Extracted EXIF from primary file
  files: FileMetadata[];     // All files in group (RAW + JPEG)
}

interface FileMetadata {
  filename: string;          // e.g., "IMG_1234.CR2"
  fileSize: number;          // Size in bytes
  fileType: string;          // e.g., "CR2", "JPEG"
  exifBlob: string;          // Base64-encoded raw EXIF data
}

interface ExifMetadata {
  width?: number;
  height?: number;
  taken_at?: string;         // ISO datetime string
  gps_latitude?: number;
  gps_longitude?: number;
  gps_altitude?: number;
  focal_length?: number;
  aperture?: number;
  iso?: number;
  exposure_time?: string;
  camera_make?: string;
  camera_model?: string;
  lens_model?: string;
}
```

### 1.2 Batch Request Construction
Frontend groups multiple photo groups into a batch request:

```typescript
interface BatchImportRequest {
  import_session_id: number;
  photo_groups: PhotoGroup[];
}
```

---

## 2. HTTP Request from Frontend

### 2.1 API Endpoint Call
```javascript
// Frontend sends batch of photo groups
const batchRequest: BatchImportRequest = {
  import_session_id: 123,
  photo_groups: [
    {
      basename: "IMG_1234",
      hothash: "a1b2c3d4e5f6...",
      hotpreview: "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
      exifData: {
        width: 4000,
        height: 3000,
        taken_at: "2024-04-27T23:49:34.000Z",
        gps_latitude: 59.9139,
        gps_longitude: 10.7522,
        camera_make: "Canon",
        camera_model: "EOS R5"
      },
      files: [
        {
          filename: "IMG_1234.CR2",
          fileSize: 45678912,
          fileType: "CR2",
          exifBlob: "base64encodedexifdata..."
        },
        {
          filename: "IMG_1234.JPG",
          fileSize: 8765432,
          fileType: "JPEG",
          exifBlob: "base64encodedexifdata..."
        }
      ]
    },
    // ... more photo groups
  ]
};

// Send to backend
const response = await fetch('/api/v1/photos/batch', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(batchRequest)
});
```

---

## 3. Backend API Endpoint Handler

### 3.1 FastAPI Endpoint
```python
# File: fase1/src/api/v1/photos.py
from schemas.requests.batch_import_requests import BatchImportRequest
from schemas.responses.batch_import_responses import BatchImportResponse

@router.post("/batch", response_model=BatchImportResponse)
async def batch_import_photos(
    request: BatchImportRequest,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Process batch of photo groups from frontend
    """
    try:
        result = await photo_service.process_batch_import(request)
        return BatchImportResponse(
            photos_created=result.photos_created,
            images_created=result.images_created,
            duplicates_skipped=result.duplicates_skipped,
            errors=result.errors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.2 Request Schema Validation
```python
# File: fase1/src/schemas/requests/batch_import_requests.py
from pydantic import BaseModel, Field
from typing import List, Optional

class FileMetadata(BaseModel):
    filename: str = Field(..., description="Original filename with extension")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File type (JPEG, CR2, etc.)")
    exif_blob: str = Field(..., description="Base64-encoded raw EXIF data")

class ExifMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    taken_at: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    focal_length: Optional[float] = None
    aperture: Optional[float] = None
    iso: Optional[int] = None
    exposure_time: Optional[str] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None

class PhotoGroup(BaseModel):
    basename: str = Field(..., description="Base filename without extension")
    hothash: str = Field(..., description="Content hash for duplicate detection")
    hotpreview: str = Field(..., description="Base64 JPEG thumbnail")
    exif_data: ExifMetadata = Field(..., description="Extracted EXIF metadata")
    files: List[FileMetadata] = Field(..., description="All files in group")

class BatchImportRequest(BaseModel):
    import_session_id: int = Field(..., description="Import session ID")
    photo_groups: List[PhotoGroup] = Field(..., description="Photo groups to process")
```

---

## 4. Service Layer Processing

### 4.1 PhotoService.process_batch_import()
```python
# File: fase1/src/services/photo_service.py
from typing import List
from schemas.requests.batch_import_requests import BatchImportRequest, PhotoGroup
from models.photo import Photo
from models.image import Image

class BatchImportResult:
    def __init__(self):
        self.photos_created = 0
        self.images_created = 0
        self.duplicates_skipped = 0
        self.errors = []

async def process_batch_import(self, request: BatchImportRequest) -> BatchImportResult:
    """
    Process batch of photo groups from frontend
    """
    result = BatchImportResult()
    
    # Begin database transaction
    try:
        with self.db.begin():
            for photo_group in request.photo_groups:
                try:
                    # Process individual photo group
                    group_result = await self._process_single_photo_group(
                        photo_group, 
                        request.import_session_id
                    )
                    
                    # Accumulate results
                    result.photos_created += group_result.photos_created
                    result.images_created += group_result.images_created
                    result.duplicates_skipped += group_result.duplicates_skipped
                    
                except Exception as e:
                    result.errors.append(f"Error processing {photo_group.basename}: {str(e)}")
                    continue
        
        return result
        
    except Exception as e:
        self.db.rollback()
        raise Exception(f"Batch import failed: {str(e)}")
```

### 4.2 Single Photo Group Processing
```python
async def _process_single_photo_group(
    self, 
    photo_group: PhotoGroup, 
    import_session_id: int
) -> BatchImportResult:
    """
    Process a single photo group (RAW + JPEG pair or single file)
    
    Steps:
    1. Check for duplicate using hothash
    2. Create Photo object with EXIF metadata and hotpreview
    3. Create Image objects for each file in group
    4. Link Images to Photo via hothash
    """
    result = BatchImportResult()
    
    # Step 1: Check for duplicate
    existing_photo = self.photo_repo.get_by_hash(photo_group.hothash)
    if existing_photo:
        result.duplicates_skipped = 1
        return result
    
    # Step 2: Create Photo object
    photo = await self._create_photo_from_group(photo_group, import_session_id)
    self.db.add(photo)
    result.photos_created = 1
    
    # Step 3: Create Image objects for each file
    for file_metadata in photo_group.files:
        image = await self._create_image_from_file(
            file_metadata, 
            photo_group.hothash,
            import_session_id
        )
        self.db.add(image)
        result.images_created += 1
    
    return result
```

---

## 5. Photo Object Creation

### 5.1 Photo Creation from Group Data
```python
async def _create_photo_from_group(
    self, 
    photo_group: PhotoGroup, 
    import_session_id: int
) -> Photo:
    """
    Create Photo object from frontend photo group data
    """
    
    # Convert base64 hotpreview to binary
    hotpreview_binary = self._decode_base64_image(photo_group.hotpreview)
    
    # Parse datetime if present
    taken_at = None
    if photo_group.exif_data.taken_at:
        taken_at = datetime.fromisoformat(photo_group.exif_data.taken_at.replace('Z', '+00:00'))
    
    # Create Photo object
    photo = Photo(
        hothash=photo_group.hothash,              # Primary key
        hotpreview=hotpreview_binary,             # Binary thumbnail data
        
        # Image dimensions
        width=photo_group.exif_data.width,
        height=photo_group.exif_data.height,
        
        # EXIF metadata
        taken_at=taken_at,
        gps_latitude=photo_group.exif_data.gps_latitude,
        gps_longitude=photo_group.exif_data.gps_longitude,
        gps_altitude=photo_group.exif_data.gps_altitude,
        focal_length=photo_group.exif_data.focal_length,
        aperture=photo_group.exif_data.aperture,
        iso=photo_group.exif_data.iso,
        exposure_time=photo_group.exif_data.exposure_time,
        camera_make=photo_group.exif_data.camera_make,
        camera_model=photo_group.exif_data.camera_model,
        lens_model=photo_group.exif_data.lens_model,
        
        # Tracking info
        import_session_id=import_session_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    return photo

def _decode_base64_image(self, base64_string: str) -> bytes:
    """
    Convert base64 image string to binary data
    """
    # Remove data URL prefix if present
    if base64_string.startswith('data:image/'):
        base64_string = base64_string.split(',')[1]
    
    # Decode base64 to binary
    return base64.b64decode(base64_string)
```

---

## 6. Image Object Creation

### 6.1 Image Creation from File Metadata
```python
async def _create_image_from_file(
    self,
    file_metadata: FileMetadata,
    hothash: str,
    import_session_id: int
) -> Image:
    """
    Create Image object from file metadata
    """
    
    # Decode raw EXIF data
    exif_binary = base64.b64decode(file_metadata.exif_blob) if file_metadata.exif_blob else None
    
    # Create Image object
    image = Image(
        # File information
        filename=file_metadata.filename,
        file_size=file_metadata.file_size,
        
        # Raw EXIF data (binary blob)
        exif_data=exif_binary,
        
        # Relationships
        hothash=hothash,                    # Links to Photo (foreign key)
        import_session_id=import_session_id,
        
        # Timestamps
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    return image
```

---

## 7. Database Transaction Handling

### 7.1 Transaction Management
```python
# Service layer handles transactions
async def process_batch_import(self, request: BatchImportRequest) -> BatchImportResult:
    """
    Process entire batch in single transaction for consistency
    """
    result = BatchImportResult()
    
    # Single transaction for entire batch
    try:
        # Process all photo groups
        for photo_group in request.photo_groups:
            # Individual photo processing
            group_result = await self._process_single_photo_group(photo_group, request.import_session_id)
            
            # Accumulate results
            result.photos_created += group_result.photos_created
            result.images_created += group_result.images_created
            result.duplicates_skipped += group_result.duplicates_skipped
        
        # Commit entire batch
        self.db.commit()
        
    except Exception as e:
        # Rollback entire batch on any error
        self.db.rollback()
        raise Exception(f"Batch processing failed: {str(e)}")
    
    return result
```

### 7.2 Error Handling Strategy
```python
# Different error handling levels:

# 1. Individual file errors - Skip file, continue processing
try:
    image = await self._create_image_from_file(file_metadata, hothash, import_session_id)
    self.db.add(image)
except Exception as e:
    result.errors.append(f"Failed to process file {file_metadata.filename}: {str(e)}")
    continue  # Skip this file, continue with others

# 2. Photo group errors - Skip group, continue processing
try:
    group_result = await self._process_single_photo_group(photo_group, import_session_id)
except Exception as e:
    result.errors.append(f"Failed to process photo group {photo_group.basename}: {str(e)}")
    continue  # Skip this group, continue with others

# 3. Batch errors - Fail entire batch, rollback transaction
try:
    # Process all groups
    self.db.commit()
except Exception as e:
    self.db.rollback()
    raise Exception(f"Batch import failed: {str(e)}")
```

---

## 8. Database Operations Flow

### 8.1 Step-by-Step Database Operations
```sql
-- For each photo group processed:

-- Step 1: Check for duplicate
SELECT * FROM photos WHERE hothash = 'a1b2c3d4e5f6...';

-- Step 2: Insert Photo (if not duplicate)
INSERT INTO photos (
    hothash, hotpreview, width, height, taken_at,
    gps_latitude, gps_longitude, gps_altitude,
    focal_length, aperture, iso, exposure_time,
    camera_make, camera_model, lens_model,
    import_session_id, created_at, updated_at
) VALUES (
    'a1b2c3d4e5f6...', '<binary_hotpreview_data>', 4000, 3000, '2024-04-27 23:49:34',
    59.9139, 10.7522, NULL,
    24.0, 2.8, 100, '1/125',
    'Canon', 'EOS R5', 'RF24-70mm F2.8 L IS USM',
    123, '2025-10-08 12:00:00', '2025-10-08 12:00:00'
);

-- Step 3: Insert Images (for each file in group)
INSERT INTO images (
    filename, file_size, exif_data,
    hothash, import_session_id,
    created_at, updated_at
) VALUES (
    'IMG_1234.CR2', 45678912, '<binary_exif_data>',
    'a1b2c3d4e5f6...', 123,
    '2025-10-08 12:00:00', '2025-10-08 12:00:00'
);

INSERT INTO images (
    filename, file_size, exif_data,
    hothash, import_session_id,
    created_at, updated_at
) VALUES (
    'IMG_1234.JPG', 8765432, '<binary_exif_data>',
    'a1b2c3d4e5f6...', 123,
    '2025-10-08 12:00:00', '2025-10-08 12:00:00'
);

-- Step 4: Update import session statistics
UPDATE import_sessions 
SET images_imported = images_imported + 1,
    files_processed = files_processed + 2
WHERE id = 123;
```

---

## 9. Response Back to Frontend

### 9.1 Success Response
```python
# Successful batch processing response
return BatchImportResponse(
    photos_created=150,        # Number of Photo objects created
    images_created=275,        # Number of Image objects created (RAW + JPEG)
    duplicates_skipped=25,     # Number of duplicate photos skipped
    errors=[                   # Any individual file/group errors
        "Failed to process file IMG_9999.CR2: Corrupted EXIF data",
        "Failed to process photo group IMG_8888: Invalid hothash"
    ],
    processing_time_ms=2500    # Time taken for batch processing
)
```

### 9.2 Frontend Response Handling
```javascript
// Frontend processes batch response
const response = await fetch('/api/v1/photos/batch', { ... });
const result = await response.json();

// Update UI with results
updateImportProgress({
    photosCreated: result.photos_created,
    imagesCreated: result.images_created,
    duplicatesSkipped: result.duplicates_skipped,
    errors: result.errors
});

// Update import session statistics
await ImportSessionsApi.updateSession(importId, {
    images_imported_increment: result.photos_created,
    duplicates_skipped_increment: result.duplicates_skipped,
    errors_increment: result.errors.length
});
```

---

## 10. Complete Data Flow Summary

### 10.1 Frontend → Backend Data Flow
1. **Frontend**: Process files → Extract EXIF → Generate hothash → Create hotpreview
2. **Frontend**: Group RAW/JPEG pairs → Structure PhotoGroup objects
3. **Frontend**: Batch multiple PhotoGroups → Send BatchImportRequest
4. **Backend**: Validate request → Process each PhotoGroup
5. **Backend**: Check duplicates → Create Photo → Create Images
6. **Backend**: Commit transaction → Return BatchImportResponse
7. **Frontend**: Update UI → Update import session statistics

### 10.2 Key Data Transformations
```
File (binary) → EXIF (JSON) → Photo (database record)
File (binary) → Raw EXIF (base64) → Image (database record)
Image content → Hothash (string) → Primary key relationship
Canvas thumbnail → Base64 string → Binary hotpreview
```

### 10.3 Database Relationships Created
```
ImportSession (1) ←→ (N) Photo
Photo (1) ←→ (N) Image  [via hothash foreign key]
ImportSession (1) ←→ (N) Image
```

This process ensures that all frontend-processed data is correctly stored in the backend database with proper relationships and referential integrity maintained throughout the batch import process.

---

## 11. Performance Considerations

### 11.1 Batch Size Optimization
- **Recommended batch size**: 50-100 photo groups per request
- **Maximum payload size**: ~10MB per batch (considering hotpreviews)
- **Transaction timeout**: Configure appropriate database timeout for large batches

### 11.2 Memory Management
- **Backend**: Process groups sequentially to limit memory usage
- **Database**: Use batch INSERT operations where possible
- **Binary data**: Stream large binary data (hotpreviews, EXIF) efficiently

This detailed specification ensures clear understanding of the complete data flow from frontend processing to backend storage.