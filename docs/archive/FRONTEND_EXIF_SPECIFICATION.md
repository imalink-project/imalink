# Frontend EXIF Processing Specification

## Overview

Frontend applications are responsible for extracting EXIF metadata from image files and sending it to the ImaLink API as a structured JSON object. This approach provides better performance and avoids binary data handling on the server side.

## EXIF JSON Structure

When creating ImageFiles via `POST /api/v1/image-files`, include the parsed EXIF data in the `exif_dict` field as a JSON object.

### Required Structure

```json
{
  "exif_dict": {
    "date_taken": "2025-01-12 17:11:26",
    "gps": {
      "latitude": 23.600653611111113,
      "longitude": 58.39307361111111
    },
    "image_info": {
      "width": 4000,
      "height": 3000
    },
    "exposure": {
      "iso": 200,
      "f_number": 2.8,
      "shutter_speed": "1/125",
      "focal_length": 50.0
    },
    "camera": {
      "make": "Canon",
      "model": "EOS R6",
      "lens_model": "RF 24-105mm F4L IS USM"
    }
  }
}
```

## Field Priorities

### **Priority 1: Essential Metadata (Required for Photo creation)**
- `date_taken` - When the photo was taken (ISO format: `YYYY-MM-DD HH:MM:SS`)
- `gps.latitude` - GPS latitude in decimal degrees (positive = North, negative = South)  
- `gps.longitude` - GPS longitude in decimal degrees (positive = East, negative = West)
- `image_info.width` - Image width in pixels
- `image_info.height` - Image height in pixels

### **Priority 2: Exposure Data (Important for photography apps)**
- `exposure.iso` - ISO sensitivity (integer)
- `exposure.f_number` - F-stop/aperture (float, e.g., 2.8)
- `exposure.shutter_speed` - Shutter speed (string, e.g., "1/125" or "2.5s")
- `exposure.focal_length` - Focal length in mm (float)
- `exposure.exposure_compensation` - Exposure compensation in stops (float)

### **Priority 3: Camera Information (Nice to have)**
- `camera.make` - Camera manufacturer (string)
- `camera.model` - Camera model (string)
- `camera.lens_model` - Lens model (string, if available)
- `camera.serial_number` - Camera serial number (string, if available)

## Implementation Guidelines

### 1. Date/Time Handling
- Extract from EXIF `DateTimeOriginal` (tag 36867) or `DateTime` (tag 306)
- Convert to ISO format: `YYYY-MM-DD HH:MM:SS`
- Use UTC or local time consistently within your application

```javascript
// Example: JavaScript/Exif.js
const dateOriginal = EXIF.getTag(img, "DateTimeOriginal");
if (dateOriginal) {
  // Convert "2025:01:12 17:11:26" to "2025-01-12 17:11:26"
  const dateTaken = dateOriginal.replace(/:/g, '-').replace(/-/g, ':', 2);
}
```

### 2. GPS Coordinate Conversion
- Extract GPS latitude/longitude in DMS (Degrees, Minutes, Seconds) format
- Convert to decimal degrees: `degrees + (minutes/60) + (seconds/3600)`
- Apply hemisphere correction (South = negative latitude, West = negative longitude)

```javascript
// Example: Convert GPS DMS to decimal
function dmsToDecimal(degrees, minutes, seconds, direction) {
  let decimal = degrees + (minutes / 60) + (seconds / 3600);
  if (direction === 'S' || direction === 'W') {
    decimal = -decimal;
  }
  return decimal;
}
```

### 3. Image Dimensions
- Extract from EXIF `ImageWidth` and `ImageLength` tags
- Fallback to actual image dimensions if EXIF data is missing

### 4. Error Handling
- **All fields are optional** - missing EXIF data should result in `null` or omitted fields
- **Silent failures** - don't warn users about missing EXIF data
- **Graceful degradation** - send partial EXIF data if some fields fail to parse

### 5. Example Implementation (JavaScript)

```javascript
function extractExifData(imageFile) {
  return new Promise((resolve) => {
    EXIF.getData(imageFile, function() {
      const exifDict = {};
      
      // Date taken
      const dateOriginal = EXIF.getTag(this, "DateTimeOriginal") || EXIF.getTag(this, "DateTime");
      if (dateOriginal) {
        exifDict.date_taken = dateOriginal.replace(/:/g, '-', 2);
      }
      
      // GPS coordinates
      const lat = EXIF.getTag(this, "GPSLatitude");
      const latRef = EXIF.getTag(this, "GPSLatitudeRef");
      const lon = EXIF.getTag(this, "GPSLongitude");
      const lonRef = EXIF.getTag(this, "GPSLongitudeRef");
      
      if (lat && lon) {
        exifDict.gps = {
          latitude: dmsToDecimal(lat[0], lat[1], lat[2], latRef),
          longitude: dmsToDecimal(lon[0], lon[1], lon[2], lonRef)
        };
      }
      
      // Image dimensions
      const width = EXIF.getTag(this, "ImageWidth") || EXIF.getTag(this, "PixelXDimension");
      const height = EXIF.getTag(this, "ImageLength") || EXIF.getTag(this, "PixelYDimension");
      if (width || height) {
        exifDict.image_info = { width, height };
      }
      
      // Camera info
      const make = EXIF.getTag(this, "Make");
      const model = EXIF.getTag(this, "Model");
      if (make || model) {
        exifDict.camera = { make, model };
      }
      
      resolve(exifDict);
    });
  });
}
```

## Common EXIF Tag Reference

| Field | EXIF Tag | Tag Number | Type |
|-------|----------|------------|------|
| Date Taken | DateTimeOriginal | 36867 | String |
| Date Taken (fallback) | DateTime | 306 | String |
| GPS Latitude | GPSLatitude | 2 | Array[3] |
| GPS Latitude Ref | GPSLatitudeRef | 1 | String |
| GPS Longitude | GPSLongitude | 4 | Array[3] |
| GPS Longitude Ref | GPSLongitudeRef | 3 | String |
| Image Width | ImageWidth | 256 | Integer |
| Image Height | ImageLength | 257 | Integer |
| Camera Make | Make | 271 | String |
| Camera Model | Model | 272 | String |
| ISO Speed | ISOSpeedRatings | 34855 | Integer |
| F-Number | FNumber | 33437 | Rational |
| Shutter Speed | ExposureTime | 33434 | Rational |
| Focal Length | FocalLength | 37386 | Rational |

## Testing

Test your EXIF extraction with various image types:
- JPEG with full EXIF data
- JPEG without EXIF data  
- RAW files (CR2, NEF, etc.)
- Images with GPS data
- Images without GPS data
- Portrait vs landscape orientations

## Libraries

### Recommended EXIF Libraries by Platform:
- **JavaScript**: exif.js, piexifjs
- **Python**: Pillow (PIL), exifread
- **Swift/iOS**: ImageIO framework
- **Java/Android**: ExifInterface
- **C#/.NET**: MetadataExtractor

## API Integration

Send the extracted EXIF data in the ImageFile creation request:

```json
POST /api/v1/image-files
{
  "filename": "IMG_1234.jpg",
  "file_size": 2048576,
  "hotpreview": "base64-encoded-hotpreview-data",
  "exif_dict": {
    "date_taken": "2025-01-12 17:11:26",
    "gps": {
      "latitude": 23.600653611111113,
      "longitude": 58.39307361111111
    },
    "image_info": {
      "width": 4000,
      "height": 3000
    }
  }
}
```

The server will automatically extract `taken_at`, `gps_latitude`, `gps_longitude`, `width`, and `height` from this structure and populate the Photo model fields accordingly.