# Frontend-to-Backend Data Transfer Process
## Raw EXIF Architecture - Backend-Driven Metadata Extraction

**Version:** 2.0  
**Date:** October 2025  
**Purpose:** Complete specification of raw EXIF data transfer and backend metadata processing  

---

## Overview

This document details the **frontend-driven architecture** where frontend handles all file operations and data processing, while backend focuses on metadata processing and database operations.

### Key Architecture Principles:
- ✅ **Frontend file management**: All file copying handled by frontend via File System Access API
- ✅ **User-chosen storage**: User selects storage directory in UI, backend just stores the name
- ✅ **Raw EXIF processing**: Frontend extracts raw EXIF bytes, backend processes with Python libraries  
- ✅ **No backend file operations**: Backend never reads, writes, or copies files
- ✅ **Clear separation**: Frontend = files/UI, Backend = metadata/database

---

## 1. Frontend Data Preparation

### 1.1 New Raw EXIF Data Structure
After frontend processing, data is structured with minimal metadata:

```typescript
// Frontend only extracts basic info + raw EXIF bytes
interface PhotoGroupRequest {
  hothash: string;                    // Content hash for duplicate detection
  hotpreview?: string;                // Base64 JPEG hotpreview
  width?: number;                     // Basic image dimensions (from canvas/Image)
  height?: number;                    // Basic image dimensions (from canvas/Image)
  
  // Backend will extract these from raw EXIF:
  taken_at?: undefined;               // Backend extracts from EXIF
  gps_latitude?: undefined;           // Backend extracts from EXIF  
  gps_longitude?: undefined;          // Backend extracts from EXIF
  
  // User metadata (optional)
  title?: string;
  description?: string;
  tags?: string[];
  rating?: number;
  user_rotation?: number;
  
  images: ImageCreateRequest[];       // Associated files with raw EXIF
}

interface ImageCreateRequest {
  filename: string;                   // e.g., "IMG_1234.jpg"
  hothash: string;                    // Links to PhotoGroup
  file_size?: number;                 // File size in bytes
  exif_data?: ArrayBuffer;            // RAW EXIF BYTES (binary data)
  import_session_id?: number;
}

// DEPRECATED - Frontend no longer parses these:
interface OldExifMetadata {
  // These fields are now extracted by backend from raw EXIF bytes
  taken_at: "Backend extracts this";
  gps_latitude: "Backend extracts this";
  camera_make: "Backend extracts this";
  // ... all other EXIF fields extracted by Python/piexif
}
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

## 2. Raw EXIF HTTP Request from Frontend

### 2.1 New API Endpoint Call (v2.0)
```javascript
// Frontend sends minimal data + raw EXIF bytes
const photoGroupRequest: PhotoGroupRequest = {
  hothash: "a1b2c3d4e5f6...",               // Content hash for duplicate detection
  hotpreview: "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...", // Hotpreview
  width: 4000,                              // Basic dimensions from canvas
  height: 3000,                             // Basic dimensions from canvas
  
  // Backend extracts these from raw EXIF:
  // taken_at: undefined,                   // Backend will populate
  // gps_latitude: undefined,               // Backend will populate  
  // gps_longitude: undefined,              // Backend will populate
  // camera_make: undefined,                // Backend will populate
  
  images: [
    {
      filename: "IMG_1234.CR2",
      hothash: "a1b2c3d4e5f6...",          // Links to PhotoGroup
      file_size: 45678912,
      exif_data: rawExifArrayBuffer,        // 1327 bytes of raw EXIF binary data
      import_session_id: 123
    },
    {
      filename: "IMG_1234.JPG", 
      hothash: "a1b2c3d4e5f6...",          // Links to PhotoGroup
      file_size: 8765432,
      exif_data: rawExifArrayBuffer,        // 1327 bytes of raw EXIF binary data
      import_session_id: 123
    }
  ]
};

// DEPRECATED - Old batch structure no longer used:
// const oldBatchRequest: BatchImportRequest = {
//   photo_groups: [...] // Frontend no longer groups or parses EXIF
// };

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

@router.post("/", response_model=PhotoGroupResponse)
async def create_photo_group_with_raw_exif(
    request: PhotoGroupRequest,
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Create PhotoGroup with raw EXIF processing
    Backend extracts metadata from raw EXIF bytes using Python piexif
    """
    try:
        # Backend processes raw EXIF bytes to extract metadata
        enhanced_photo_group = await photo_service.create_photo_group_with_metadata_extraction(request)
        
        return PhotoGroupResponse(
            id=enhanced_photo_group.id,
            hothash=enhanced_photo_group.hothash,
            # Backend-extracted metadata populated:
            taken_at=enhanced_photo_group.taken_at,      # From EXIF DateTime
            gps_latitude=enhanced_photo_group.gps_latitude,  # From GPS coords
            gps_longitude=enhanced_photo_group.gps_longitude, # From GPS coords
            camera_make=enhanced_photo_group.camera_make,    # From EXIF Make
            camera_model=enhanced_photo_group.camera_model,  # From EXIF Model
            images_created=len(enhanced_photo_group.images)
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

# DEPRECATED: Frontend no longer sends parsed EXIF metadata
# class ExifMetadata(BaseModel): # Frontend parsing removed
#     width: Optional[int] = None  # Now extracted by backend from raw EXIF
#     taken_at: Optional[str] = None  # Now extracted by backend from raw EXIF
#     gps_latitude: Optional[float] = None  # Now extracted by backend from raw EXIF

# NEW: Raw EXIF request structure
class PhotoGroupRequest(BaseModel):
    hothash: str = Field(..., description="Content hash for duplicate detection")
    hotpreview: Optional[str] = Field(None, description="Base64 JPEG hotpreview")
    width: Optional[int] = Field(None, description="Basic width from canvas/Image")
    height: Optional[int] = Field(None, description="Basic height from canvas/Image")
    
    # User metadata (optional)
    title: Optional[str] = Field(None, description="User-provided title")
    description: Optional[str] = Field(None, description="User-provided description") 
    tags: Optional[List[str]] = Field(None, description="User-provided tags")
    rating: Optional[int] = Field(None, description="User rating 1-5")
    user_rotation: Optional[int] = Field(None, description="User rotation angle")
    
    images: List[ImageCreateRequest] = Field(..., description="Associated image files")

class ImageCreateRequest(BaseModel):
    filename: str = Field(..., description="Original filename")
    hothash: str = Field(..., description="Links to PhotoGroup")
    file_size: Optional[int] = Field(None, description="File size in bytes")  
    exif_data: Optional[bytes] = Field(None, description="Raw EXIF binary data (1327 bytes)")
    import_session_id: Optional[int] = Field(None, description="Import session reference")

# RESPONSE: Backend returns enhanced PhotoGroup with extracted metadata
class PhotoGroupResponse(BaseModel):
    id: int = Field(..., description="Created PhotoGroup ID")
    hothash: str = Field(..., description="Content hash")
    # Backend-extracted metadata:
    taken_at: Optional[str] = Field(None, description="Extracted from EXIF DateTime")
    gps_latitude: Optional[float] = Field(None, description="Extracted from GPS coordinates")
    gps_longitude: Optional[float] = Field(None, description="Extracted from GPS coordinates")
    camera_make: Optional[str] = Field(None, description="Extracted from EXIF Make")
    camera_model: Optional[str] = Field(None, description="Extracted from EXIF Model")
    images_created: int = Field(..., description="Number of associated images created")
    files: List[FileMetadata] = Field(..., description="All files in group")

class BatchImportRequest(BaseModel):
    import_session_id: int = Field(..., description="Import session ID")
    photo_groups: List[PhotoGroup] = Field(..., description="Photo groups to process")
```

---

## 4. Backend Raw EXIF Service Processing

### 4.1 PhotoService.create_photo_group_with_metadata_extraction()
```python
# File: fase1/src/services/photo_service.py
from typing import Optional
from schemas.requests.photo_group_requests import PhotoGroupRequest
from services.importing.image_processor import ImageFileProcessor
from models.photo import Photo
from models.image import ImageFile

async def create_photo_group_with_metadata_extraction(
    self, 
    request: PhotoGroupRequest
) -> Photo:
    """
    Create PhotoGroup with backend EXIF metadata extraction
    Uses Python piexif to process raw EXIF bytes from frontend
    """
    # Step 1: Create base PhotoGroup with frontend data
    photo_group = Photo(
        hothash=request.hothash,
        hotpreview=request.hotpreview,
        width=request.width,
        height=request.height,
        # Metadata will be populated from raw EXIF:
        taken_at=None,
        gps_latitude=None,
        gps_longitude=None
    )
    
    # Step 2: Extract metadata from raw EXIF bytes
    images_with_exif = [img for img in request.images if img.exif_data]
    if images_with_exif:
        # Use ImageProcessor to extract metadata from raw EXIF
        extracted_metadata = await self.image_processor.extract_metadata_from_raw_exif(
            images_with_exif[0].exif_data  # Use first image with EXIF
        )
        
        # Enhance PhotoGroup with extracted metadata
        photo_group.taken_at = extracted_metadata.get('taken_at')
        photo_group.gps_latitude = extracted_metadata.get('gps_latitude') 
        photo_group.gps_longitude = extracted_metadata.get('gps_longitude')
        photo_group.camera_make = extracted_metadata.get('camera_make')
        photo_group.camera_model = extracted_metadata.get('camera_model')
    
    # Step 3: Save PhotoGroup and associated Images
    saved_photo_group = await self.photo_repository.create(photo_group)
    
    # Step 4: Create associated Image records
    for image_request in request.images:
        image = Image(
            filename=image_request.filename,
            hothash=image_request.hothash,
            file_size=image_request.file_size,
            photo_id=saved_photo_group.id,
            import_session_id=image_request.import_session_id
        )
        await self.image_repository.create(image)
    
    return saved_photo_group
    result = BatchImportResult()
    
    # Begin database transaction
    try:
        with self.db.begin():
            for photo_group in request.photo_groups:
                try:
                    # Process individual photo group
                    group_result = await self._process_single_photo_group(
```

### 4.2 ImageProcessor.extract_metadata_from_raw_exif()
```python
# File: fase1/src/services/importing/image_processor.py
import piexif
from typing import Dict, Any, Optional

class ImageProcessor:
    async def extract_metadata_from_raw_exif(self, raw_exif_bytes: bytes) -> Dict[str, Any]:
        """
        Extract structured metadata from raw EXIF binary data
        Uses Python piexif library for robust EXIF processing
        """
        try:
            # Parse raw EXIF bytes using piexif
            exif_dict = piexif.load(raw_exif_bytes)
            
            metadata = {}
            
            # Extract GPS coordinates with proper decimal conversion
            if 'GPS' in exif_dict and exif_dict['GPS']:
                gps_info = exif_dict['GPS']
                
                # Extract latitude
                if piexif.GPSIFD.GPSLatitude in gps_info:
                    lat_dms = gps_info[piexif.GPSIFD.GPSLatitude]
                    lat_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
                    metadata['gps_latitude'] = self._dms_to_decimal(lat_dms, lat_ref)
                
                # Extract longitude  
                if piexif.GPSIFD.GPSLongitude in gps_info:
                    lng_dms = gps_info[piexif.GPSIFD.GPSLongitude] 
                    lng_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()
                    metadata['gps_longitude'] = self._dms_to_decimal(lng_dms, lng_ref)
            
            # Extract date/time
            if '0th' in exif_dict and piexif.ImageIFD.DateTime in exif_dict['0th']:
                datetime_str = exif_dict['0th'][piexif.ImageIFD.DateTime].decode()
                metadata['taken_at'] = self._parse_exif_datetime(datetime_str)
            
            # Extract camera info
            if '0th' in exif_dict:
                if piexif.ImageIFD.Make in exif_dict['0th']:
                    metadata['camera_make'] = exif_dict['0th'][piexif.ImageIFD.Make].decode().strip()
                if piexif.ImageIFD.Model in exif_dict['0th']:
                    metadata['camera_model'] = exif_dict['0th'][piexif.ImageIFD.Model].decode().strip()
            
            return metadata
            
        except Exception as e:
            print(f"Failed to extract EXIF metadata: {e}")
            return {}
    
    def _dms_to_decimal(self, dms_tuple, ref) -> float:
        """Convert GPS DMS coordinates to decimal degrees"""
        degrees, minutes, seconds = dms_tuple
        decimal = degrees[0]/degrees[1] + minutes[0]/(minutes[1]*60) + seconds[0]/(seconds[1]*3600)
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal
    
    def _parse_exif_datetime(self, datetime_str: str) -> str:
        """Parse EXIF datetime to ISO format"""
        # Convert "2024:04:27 14:55:20" to "2024-04-27T14:55:20"
        return datetime_str.replace(':', '-', 2).replace(' ', 'T')
```

### 4.3 Raw EXIF Architecture Benefits

#### 4.3.1 Reliability & Consistency
- **Python EXIF Processing**: Uses mature piexif library instead of JavaScript parsing
- **GPS Coordinate Accuracy**: Fixed decimal conversion eliminates frontend parsing errors
- **Robust Error Handling**: Backend can gracefully handle malformed EXIF data
- **Cross-Browser Consistency**: No dependency on browser EXIF implementations

#### 4.3.2 Performance & Scalability  
- **Reduced Frontend Complexity**: Frontend only extracts raw bytes (1327 bytes)
- **Backend Intelligence**: Complex metadata processing handled by powerful Python libraries
- **Efficient Data Transfer**: Raw bytes more compact than parsed JSON structures
- **Centralized Processing**: Single point for EXIF handling reduces inconsistencies

#### 4.3.3 Separation of Concerns
- **Frontend**: File handling, UI, basic image operations (dimensions, hotpreviews)
- **Backend**: Complex metadata extraction, database operations, business logic
- **Clear Interface**: Raw EXIF bytes provide clean contract between frontend/backend

## 5. Data Flow Summary

### 5.1 Old Architecture (Deprecated)
```
Frontend: Parse EXIF → Extract metadata → Send JSON → Backend: Store data
Problems: Browser inconsistencies, GPS parsing errors, complex frontend code
```

### 5.2 New Raw EXIF Architecture (v2.0)
```
Frontend: Extract raw EXIF bytes → Send binary data → Backend: Parse with piexif → Extract metadata → Enhance PhotoGroup → Store enhanced data
Benefits: Reliability, consistency, accuracy, separation of concerns
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

## 6. Testing & Validation

### 6.1 Raw EXIF Extraction Testing
```javascript
// Frontend: Test raw EXIF byte extraction
// File: frontend/test-raw-exif-flow.js
import { extractRawExifBytesFromFile } from './src/lib/image-processor/raw-exif-extractor.js';

async function testRawExifExtraction(file) {
    const rawExifBytes = await extractRawExifBytesFromFile(file);
    console.log(`Extracted ${rawExifBytes.byteLength} bytes of raw EXIF data`);
    // Should output: "Extracted 1327 bytes of raw EXIF data"
    
    // Send to backend for processing
    const response = await fetch('/api/v1/photos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            hothash: "test123",
            images: [{
                filename: file.name,
                hothash: "test123", 
                exif_data: Array.from(new Uint8Array(rawExifBytes))
            }]
        })
    });
    
    const result = await response.json();
    console.log('Backend extracted metadata:', result);
    // Should show: GPS coordinates, camera info, datetime, etc.
}
```

### 6.2 Backend EXIF Processing Testing
```python
# Backend: Test metadata extraction from raw EXIF
# File: fase1/test_raw_exif_processing.py
from services.importing.image_processor import ImageFileProcessor

async def test_backend_exif_processing():
    processor = ImageProcessor()
    
    # Test with 1327 bytes of raw EXIF data
    with open('test_image.jpg', 'rb') as f:
        # Extract EXIF bytes (matches frontend extraction)
        raw_exif = extract_exif_from_jpeg(f.read())
    
    # Process with backend
    metadata = await processor.extract_metadata_from_raw_exif(raw_exif)
    
    print(f"GPS: {metadata.get('gps_latitude')}, {metadata.get('gps_longitude')}")
    print(f"Camera: {metadata.get('camera_make')} {metadata.get('camera_model')}")
    print(f"Date: {metadata.get('taken_at')}")
    
    # Expected output:
    # GPS: 25.140028, 121.51293944444444
    # Camera: HUAWEI VOG-L29
    # Date: 2024-04-27T14:55:20
    
    # Create Photo object
    photo = Photo(
        hothash=photo_group.hothash,              # Primary key
        hotpreview=hotpreview_binary,             # Binary hotpreview data
        
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
Canvas hotpreview → Base64 string → Binary hotpreview
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