# ImaLink Frontend-Driven Import Flow Documentation
## Technical Specification of Client-Side Import Architecture

**Version:** 2.0  
**Date:** October 2025  
**Purpose:** Complete documentation of frontend-driven import flow from local files to database  

---

## Overview

This document provides a detailed technical specification of ImaLink's frontend-driven import system. All file processing, metadata extraction, and thumbnail generation happens in the browser using JavaScript/TypeScript. The backend serves purely as a data API for storing processed results. The process runs sequentially (not as background tasks) for simplicity and reliability.

---

## 1. Import Flow Architecture

```
┌─────────────────────────────────────────────┐
│              Frontend (Browser)             │
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │ File System     │  │ Processing      │   │
│  │ Access API      │  │ Engine          │   │
│  │                 │  │                 │   │
│  │ • Directory     │  │ • EXIF Extract  │   │
│  │   Scanning      │  │ • RAW/JPEG Pair │   │
│  │ • File Reading  │  │ • Hash Generate │   │
│  │ • Binary Data   │  │ • Thumbnail Gen │   │
│  └─────────────────┘  └─────────────────┘   │
│           │                     │           │
│           └──────────┬──────────┘           │
│                      │                      │
│           ┌─────────────────┐               │
│           │ Import Manager  │               │
│           │                 │               │
│           │ • Progress UI   │               │
│           │ • Error Handle  │               │
│           │ • API Calls     │               │
│           └─────────────────┘               │
└─────────────────┬───────────────────────────┘
                  │ HTTP REST API
                  │
┌─────────────────▼───────────────────────────┐
│              Backend (FastAPI)              │
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │ REST API        │  │ Database        │   │
│  │                 │  │                 │   │
│  │ • Photos CRUD   │  │ • Photos        │   │
│  │ • Images CRUD   │  │ • Images        │   │
│  │ • Sessions      │  │ • ImportSessions│   │
│  │ • Authors       │  │ • Authors       │   │
│  └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 2. Detailed Import Process Flow

### 2.1 Phase 1: User Interaction and File Selection (Frontend)

#### **User Interface:**
```typescript
// Frontend UI allows user to:
// 1. Select directory or files using File System Access API
// 2. Configure import settings (author, description, etc.)
// 3. Start import process
```

#### **Directory/File Selection:**
```javascript
// Using File System Access API (modern browsers)
async function selectDirectory(): Promise<FileSystemDirectoryHandle> {
  const dirHandle = await window.showDirectoryPicker({
    mode: 'read'
  });
  return dirHandle;
}

// Alternative: File input for older browsers
function selectFiles(): Promise<FileList> {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = 'image/*,.cr2,.cr3,.nef,.arw,.orf,.dng,.raf,.rw2';
    input.onchange = () => resolve(input.files);
    input.click();
  });
}
```

### 2.2 Phase 2: Import Session Creation (Frontend → Backend)

#### **Frontend Action:**
```javascript
// Create import session to track progress
const importSession = await ImportSessionsApi.startImport({
  source_description: userDescription,
  source_path: "Client-side import", // Not actual path for security
  total_files_estimated: selectedFiles.length
});

const importId = importSession.import_id;
```

#### **Backend API Handler:**
```python
# File: fase1/src/api/v1/import_sessions.py
@router.post("/start", response_model=ImportStartResponse)
async def start_import(request: ImportStartRequest):
    # Create session record for tracking
    import_session = ImportSession(
        source_path=request.source_path,
        source_description=request.source_description,
        status="in_progress",
        started_at=datetime.utcnow(),
        total_files_found=request.total_files_estimated or 0
    )
    
    # No background task - frontend handles processing
    return ImportStartResponse(
        import_id=import_session.id,
        message="Import session created",
        status="in_progress"
    )
```

### 2.3 Phase 3: File Discovery and Scanning (Frontend JavaScript)

#### **Recursive Directory Scanning:**
```javascript
async function scanDirectoryForImages(dirHandle: FileSystemDirectoryHandle): Promise<File[]> {
  const imageFiles: File[] = [];
  
  // Supported image extensions
  const SUPPORTED_EXTENSIONS = new Set([
    '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp',  // Standard
    '.cr2', '.cr3', '.nef', '.arw', '.orf', '.dng', '.raf', '.rw2'  // RAW
  ]);
  
  async function processDirectory(dirHandle: FileSystemDirectoryHandle) {
    for await (const [name, handle] of dirHandle.entries()) {
      if (handle.kind === 'file') {
        const file = await handle.getFile();
        const extension = getFileExtension(file.name).toLowerCase();
        
        if (SUPPORTED_EXTENSIONS.has(extension)) {
          imageFiles.push(file);
        }
      } else if (handle.kind === 'directory') {
        // Recursive scanning
        await processDirectory(handle);
      }
    }
  }
  
  await processDirectory(dirHandle);
  return imageFiles;
}
```

#### **Update Session with File Count:**
```javascript
// Update backend with actual file count
await ImportSessionsApi.updateSession(importId, {
  total_files_found: imageFiles.length
});
```

### 2.4 Phase 4: RAW/JPEG Pairing (Frontend JavaScript)

#### **File Grouping Logic:**
```javascript
interface FileGroup {
  basename: string;
  files: File[];
  primaryFile: File;  // Preferred file for processing (JPEG over RAW)
}

function groupRAWJPEGPairs(files: File[]): FileGroup[] {
  const groups = new Map<string, File[]>();
  
  // Group files by basename (filename without extension)
  for (const file of files) {
    const basename = getBasename(file.name);
    
    if (!groups.has(basename)) {
      groups.set(basename, []);
    }
    groups.get(basename)!.push(file);
  }
  
  // Convert to FileGroup objects with primary file selection
  return Array.from(groups.entries()).map(([basename, files]) => {
    // Prefer JPEG over RAW for primary processing
    const jpegFile = files.find(f => isJPEGFile(f.name));
    const primaryFile = jpegFile || files[0];
    
    return {
      basename,
      files,
      primaryFile
    };
  });
}

function getBasename(filename: string): string {
  return filename.replace(/\.[^/.]+$/, ""); // Remove extension
}

function isJPEGFile(filename: string): boolean {
  const ext = getFileExtension(filename).toLowerCase();
  return ext === '.jpg' || ext === '.jpeg';
}
```

### 2.5 Phase 5: Sequential File Processing (Frontend JavaScript)

#### **Main Processing Loop:**
```javascript
async function processImport(importId: number, fileGroups: FileGroup[]): Promise<void> {
  let processedCount = 0;
  
  for (const group of fileGroups) {
    try {
      // Update progress in UI
      updateProgressUI(processedCount, fileGroups.length, group.primaryFile.name);
      
      // Process this photo group
      const success = await processPhotoGroup(importId, group);
      
      if (success) {
        // Update backend progress
        await ImportSessionsApi.incrementImagesImported(importId);
      } else {
        await ImportSessionsApi.incrementErrors(importId);
      }
      
      processedCount++;
      
      // Update session progress
      await ImportSessionsApi.updateProgress(importId, {
        files_processed: processedCount,
        current_file: group.primaryFile.name
      });
      
    } catch (error) {
      console.error(`Error processing ${group.basename}:`, error);
      await ImportSessionsApi.incrementErrors(importId);
    }
  }
  
  // Mark import as completed
  await ImportSessionsApi.completeImport(importId);
}
```

### 2.6 Phase 6: Photo Group Processing (Frontend JavaScript)

#### **Individual Photo Processing:**
```javascript
async function processPhotoGroup(importId: number, group: FileGroup): Promise<boolean> {
  try {
    // Step 1: Generate content hash from primary file
    const hothash = await generateContentHash(group.primaryFile);
    
    // Step 2: Check for duplicates
    const existingPhoto = await PhotosApi.getByHash(hothash);
    if (existingPhoto) {
      await ImportSessionsApi.incrementDuplicatesSkipped(importId);
      return true; // Skip duplicate
    }
    
    // Step 3: Extract EXIF metadata
    const exifData = await extractEXIFData(group.primaryFile);
    
    // Step 4: Generate hotpreview thumbnail
    const hotpreview = await generateHotpreview(group.primaryFile);
    
    // Step 5: Create Photo in backend
    const photo = await PhotosApi.create({
      hothash,
      hotpreview,
      width: exifData.width,
      height: exifData.height,
      taken_at: exifData.taken_at,
      gps_latitude: exifData.gps_latitude,
      gps_longitude: exifData.gps_longitude,
      // ... other EXIF fields
      import_session_id: importId
    });
    
    // Step 6: Create Image records for each file
    for (const file of group.files) {
      const exifBlob = await extractRawEXIF(file);
      
      await ImagesApi.create({
        filename: file.name,
        file_size: file.size,
        exif_data: exifBlob,
        hothash,
        import_session_id: importId
      });
    }
    
    return true;
    
  } catch (error) {
    console.error('Error processing photo group:', error);
    return false;
  }
}
```

### 2.7 Phase 7: Metadata Extraction (Frontend JavaScript)

#### **EXIF Data Extraction:**
```javascript
// Using ExifReader library (client-side EXIF parsing)
import ExifReader from 'exifreader';

async function extractEXIFData(file: File): Promise<PhotoMetadata> {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const tags = ExifReader.load(arrayBuffer);
    
    return {
      width: tags.ImageWidth?.value || null,
      height: tags.ImageLength?.value || null,
      taken_at: parseDateTimeOriginal(tags.DateTimeOriginal?.description),
      gps_latitude: parseGPSCoordinate(tags.GPSLatitude, tags.GPSLatitudeRef),
      gps_longitude: parseGPSCoordinate(tags.GPSLongitude, tags.GPSLongitudeRef),
      gps_altitude: tags.GPSAltitude?.value || null,
      focal_length: tags.FocalLength?.value || null,
      aperture: tags.FNumber?.value || null,
      iso: tags.ISOSpeedRatings?.value || null,
      exposure_time: tags.ExposureTime?.description || null,
      camera_make: tags.Make?.description || null,
      camera_model: tags.Model?.description || null,
      lens_model: tags.LensModel?.description || null
    };
  } catch (error) {
    console.warn('EXIF extraction failed:', error);
    return {}; // Return empty metadata on failure
  }
}

async function extractRawEXIF(file: File): Promise<Uint8Array> {
  // Extract raw EXIF binary data for storage
  const arrayBuffer = await file.arrayBuffer();
  // Implementation depends on EXIF library capabilities
  return new Uint8Array(arrayBuffer); // Simplified
}
```

#### **Content Hash Generation:**
```javascript
// Generate perceptual hash for duplicate detection
async function generateContentHash(file: File): Promise<string> {
  try {
    // Create image for processing
    const img = await loadImageFromFile(file);
    
    // Simple content hash based on resized image data
    // (In production, use proper perceptual hashing)
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = 64;
    canvas.height = 64;
    ctx.drawImage(img, 0, 0, 64, 64);
    
    const imageData = ctx.getImageData(0, 0, 64, 64);
    const hash = await crypto.subtle.digest('SHA-256', imageData.data.buffer);
    
    return Array.from(new Uint8Array(hash))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
      
  } catch (error) {
    // Fallback to filename-based hash
    return await hashString(file.name + file.size);
  }
}
```

#### **Hotpreview Generation:**
```javascript
async function generateHotpreview(file: File): Promise<string> {
  try {
    const img = await loadImageFromFile(file);
    
    // Create thumbnail canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Calculate thumbnail dimensions (max 400px)
    const maxSize = 400;
    let { width, height } = calculateThumbnailSize(img.width, img.height, maxSize);
    
    canvas.width = width;
    canvas.height = height;
    
    // Draw resized image
    ctx.drawImage(img, 0, 0, width, height);
    
    // Convert to base64 JPEG
    return canvas.toDataURL('image/jpeg', 0.8);
    
  } catch (error) {
    console.warn('Hotpreview generation failed:', error);
    return ''; // Return empty string on failure
  }
}

function loadImageFromFile(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
}
```

---

## 3. API Communication Pattern

### 3.1 RESTful Backend APIs (Data Only)

#### **Photos API:**
```javascript
// frontend/src/lib/api/photos.ts
export class PhotosApi {
  static async create(photoData: PhotoCreateRequest): Promise<Photo> {
    const response = await fetch('/api/v1/photos/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(photoData)
    });
    return response.json();
  }
  
  static async getByHash(hothash: string): Promise<Photo | null> {
    const response = await fetch(`/api/v1/photos/${hothash}`);
    return response.ok ? response.json() : null;
  }
}
```

#### **Images API:**
```javascript
// frontend/src/lib/api/images.ts
export class ImagesApi {
  static async create(imageData: ImageCreateRequest): Promise<Image> {
    const response = await fetch('/api/v1/images/', {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(imageData)
    });
    return response.json();
  }
}
```

#### **Import Sessions API:**
```javascript
// frontend/src/lib/api/imports.ts
export class ImportSessionsApi {
  static async startImport(data: ImportStartRequest): Promise<ImportStartResponse> {
    const response = await fetch('/api/v1/import_sessions/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
  
  static async updateProgress(importId: number, progress: ProgressUpdate): Promise<void> {
    await fetch(`/api/v1/import_sessions/${importId}/progress`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(progress)
    });
  }
  
  static async incrementImagesImported(importId: number): Promise<void> {
    await fetch(`/api/v1/import_sessions/${importId}/increment/imported`, {
      method: 'POST'
    });
  }
  
  static async completeImport(importId: number): Promise<void> {
    await fetch(`/api/v1/import_sessions/${importId}/complete`, {
      method: 'POST'
    });
  }
}
```

---

## 4. Data Flow Summary

### 4.1 Frontend Responsibilities (JavaScript/TypeScript)
- **File System Access**: Directory/file selection using Web APIs
- **File Processing**: Reading file contents into memory
- **EXIF Extraction**: Parsing metadata using client-side libraries
- **Image Processing**: Thumbnail generation using Canvas API
- **Content Hashing**: Generating perceptual hashes for duplicates
- **RAW/JPEG Pairing**: Grouping related files by basename
- **Progress Management**: UI updates and user feedback
- **API Communication**: REST calls to backend for data storage
- **Error Handling**: User-friendly error messages and recovery

### 4.2 Backend Responsibilities (Python/FastAPI)
- **Data API**: CRUD operations for Photos, Images, ImportSessions
- **Data Validation**: Input validation and sanitization
- **Database Management**: Transaction handling and data integrity
- **Session Tracking**: Import progress and statistics
- **Authentication**: User authentication and authorization (future)
- **Data Export**: API endpoints for data export and backup

---

## 5. Technology Stack

### 5.1 Frontend Technologies
```javascript
// Core Technologies:
- JavaScript/TypeScript (ES2022+)
- Svelte/SvelteKit (UI Framework)
- File System Access API (Directory scanning)
- Canvas API (Image processing)
- Web Crypto API (Hashing)
- ExifReader library (EXIF parsing)

// Required Browser Features:
- File System Access API (Chrome 86+, Edge 86+)
- Canvas API (All modern browsers)
- Web Crypto API (All modern browsers)
- ArrayBuffer support (All modern browsers)
```

### 5.2 Backend Technologies
```python
# Core Technologies:
- Python 3.11+
- FastAPI (REST API framework)
- SQLAlchemy (Database ORM)
- SQLite (Database)
- Pydantic (Data validation)

# Libraries:
- Pillow (Server-side image processing, if needed)
- python-multipart (File upload handling)
```

---

## 6. Browser Compatibility and Fallbacks

### 6.1 File System Access API Support
```javascript
// Modern browsers (Chrome 86+, Edge 86+)
if ('showDirectoryPicker' in window) {
  // Use File System Access API for directory scanning
  const dirHandle = await window.showDirectoryPicker();
} else {
  // Fallback: File input with multiple selection
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.webkitdirectory = true; // Webkit directory selection
}
```

### 6.2 Processing Limitations
- **Memory Limits**: Large RAW files may hit browser memory limits
- **Processing Speed**: JavaScript processing slower than native code
- **File Access**: Limited to user-selected files for security
- **Concurrency**: Single-threaded JavaScript execution

---

## 7. Error Handling Strategy

### 7.1 File Processing Errors
```javascript
// Graceful degradation for unsupported files
try {
  const exifData = await extractEXIFData(file);
} catch (error) {
  console.warn(`EXIF extraction failed for ${file.name}:`, error);
  // Continue with empty metadata
  const exifData = {};
}
```

### 7.2 Network Errors
```javascript
// Retry logic for API calls
async function apiCallWithRetry(apiCall: () => Promise<any>, maxRetries = 3): Promise<any> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await new Promise(resolve => setTimeout(resolve, attempt * 1000));
    }
  }
}
```

### 7.3 User Experience
- **Progress Indicators**: Visual feedback for long operations
- **Error Messages**: Clear, actionable error descriptions
- **Recovery Options**: Skip problematic files and continue
- **Cancel Support**: Allow user to stop import process

---

## 8. Performance Characteristics

### 8.1 Processing Model
- **Sequential Processing**: One file at a time to avoid memory issues
- **Single-threaded**: JavaScript main thread handles all processing
- **Memory Management**: Process and release files individually
- **Progress Feedback**: Real-time UI updates

### 8.2 Expected Performance
```javascript
// Typical processing speeds (estimated):
// - JPEG files: ~10-50 files/second (depending on size)
// - RAW files: ~1-10 files/second (larger, more complex)
// - Network API calls: ~10-100 requests/second
// - Overall throughput: ~5-20 photos/second for mixed content
```

### 8.3 Scalability Considerations
- **Large Collections**: 50K+ files will take significant time
- **Memory Usage**: One file in memory at a time
- **Browser Limits**: May hit JavaScript execution time limits
- **User Experience**: Need progress indicators and pause/resume

---

## 9. Security Considerations

### 9.1 File Access Security
- **User Consent**: Files only accessible after explicit user selection
- **No File System Access**: Cannot read arbitrary files from disk
- **Sandboxed Processing**: All processing happens in browser sandbox
- **No Server-Side Files**: Backend never accesses user's file system

### 9.2 Data Transmission
- **Metadata Only**: Only extracted metadata sent to server
- **No Original Files**: Original image files never uploaded
- **Base64 Thumbnails**: Hotpreviews sent as base64 strings
- **HTTPS Required**: All API communication encrypted

---

## 10. Future Enhancements

### 10.1 Performance Improvements
- **Web Workers**: Move processing to background threads
- **Streaming Processing**: Process files as they're selected
- **Batch API Calls**: Group multiple operations in single request
- **Caching**: Cache processed metadata for repeated imports

### 10.2 Advanced Features
- **Resume Capability**: Save progress and resume interrupted imports
- **Parallel Processing**: Process multiple files simultaneously
- **Advanced Hashing**: Better perceptual hash algorithms
- **RAW Processing**: More sophisticated RAW file handling

---

This document represents the current frontend-driven import architecture designed for reliability and simplicity over maximum performance. The sequential processing approach ensures stability while the frontend-centric design works well with remote backend deployments.