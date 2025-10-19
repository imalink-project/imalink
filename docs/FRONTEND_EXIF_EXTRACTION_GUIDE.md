# EXIF Extraction Guide for Frontend Developers

## Overview

This guide provides practical implementation details for extracting EXIF metadata from image files on the frontend. The extracted data should be converted to a standardized JSON format before sending to the ImaLink API.

## Key Principle: Frontend Responsibility

**Frontend extracts and processes EXIF → Backend receives clean JSON data**

- Frontend handles all binary EXIF parsing and calculations
- Backend receives standardized, ready-to-use values
- Original files remain unchanged for future processing

## GPS Coordinates: Critical Implementation Details

### GPS Data Structure in EXIF

EXIF stores GPS coordinates in DMS (Degrees, Minutes, Seconds) format:
- **Latitude**: Array of 3 rational numbers `[degrees, minutes, seconds]`
- **Latitude Reference**: 'N' (North) or 'S' (South)
- **Longitude**: Array of 3 rational numbers `[degrees, minutes, seconds]`  
- **Longitude Reference**: 'E' (East) or 'W' (West)

### Required Conversion: DMS → Decimal Degrees

**Formula**: `decimal = degrees + (minutes/60) + (seconds/3600)`

**Hemisphere Correction**:
- **South latitude**: Multiply by -1
- **West longitude**: Multiply by -1

### GPS Implementation Examples

#### JavaScript Example
```javascript
function dmsToDecimal(dmsArray, hemisphere) {
    if (!dmsArray || dmsArray.length !== 3) return null;
    
    const [deg, min, sec] = dmsArray;
    let decimal = deg + (min / 60) + (sec / 3600);
    
    // Apply hemisphere correction
    if (hemisphere === 'S' || hemisphere === 'W') {
        decimal = -decimal;
    }
    
    return decimal;
}

// Usage with exif.js
const lat = EXIF.getTag(image, "GPSLatitude");
const latRef = EXIF.getTag(image, "GPSLatitudeRef");
const lon = EXIF.getTag(image, "GPSLongitude"); 
const lonRef = EXIF.getTag(image, "GPSLongitudeRef");

const gpsData = {
    latitude: dmsToDecimal(lat, latRef),
    longitude: dmsToDecimal(lon, lonRef)
};
```

#### Python Example
```python
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def dms_to_decimal(dms_tuple, hemisphere):
    if not dms_tuple or len(dms_tuple) != 3:
        return None
    
    degrees, minutes, seconds = dms_tuple
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    
    if hemisphere in ['S', 'W']:
        decimal = -decimal
    
    return decimal

def extract_gps(image_path):
    with Image.open(image_path) as img:
        exif = img.getexif()
        
        if not exif:
            return None
            
        gps_info = {}
        for tag_id in exif:
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                gps_data = exif[tag_id]
                
                # Extract coordinates
                if 2 in gps_data and 1 in gps_data:  # Latitude
                    lat_dms = gps_data[2]
                    lat_ref = gps_data[1]
                    gps_info['latitude'] = dms_to_decimal(lat_dms, lat_ref)
                
                if 4 in gps_data and 3 in gps_data:  # Longitude
                    lon_dms = gps_data[4] 
                    lon_ref = gps_data[3]
                    gps_info['longitude'] = dms_to_decimal(lon_dms, lon_ref)
        
        return gps_info if gps_info else None
```

#### Swift Example (iOS)
```swift
import ImageIO
import CoreLocation

func extractGPSCoordinates(from imageData: Data) -> CLLocationCoordinate2D? {
    guard let source = CGImageSourceCreateWithData(imageData, nil),
          let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [String: Any],
          let gpsInfo = properties[kCGImagePropertyGPSDictionary as String] as? [String: Any] else {
        return nil
    }
    
    guard let latitudeArray = gpsInfo[kCGImagePropertyGPSLatitude as String] as? Double,
          let latitudeRef = gpsInfo[kCGImagePropertyGPSLatitudeRef as String] as? String,
          let longitudeArray = gpsInfo[kCGImagePropertyGPSLongitude as String] as? Double,
          let longitudeRef = gpsInfo[kCGImagePropertyGPSLongitudeRef as String] as? String else {
        return nil
    }
    
    var latitude = latitudeArray
    var longitude = longitudeArray
    
    // Apply hemisphere correction
    if latitudeRef == "S" { latitude = -latitude }
    if longitudeRef == "W" { longitude = -longitude }
    
    return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
}
```

## Recommended EXIF Fields

### Priority 1: Essential Metadata (Always Extract)

| Field Name | EXIF Tag | Description | Format |
|------------|----------|-------------|---------|
| `date_taken` | DateTimeOriginal (36867) | When photo was captured | "YYYY-MM-DD HH:MM:SS" |
| `gps.latitude` | GPSLatitude (2) + GPSLatitudeRef (1) | GPS latitude in decimal degrees | Float (-90 to +90) |
| `gps.longitude` | GPSLongitude (4) + GPSLongitudeRef (3) | GPS longitude in decimal degrees | Float (-180 to +180) |
| `image_info.width` | ImageWidth (256) or PixelXDimension | Image width in pixels | Integer |
| `image_info.height` | ImageLength (257) or PixelYDimension | Image height in pixels | Integer |

### Priority 2: Photography Metadata (Highly Recommended)

| Field Name | EXIF Tag | Description | Format |
|------------|----------|-------------|---------|
| `exposure.iso` | ISOSpeedRatings (34855) | ISO sensitivity | Integer (e.g., 200, 800) |
| `exposure.f_number` | FNumber (33437) | Aperture f-stop | Float (e.g., 2.8, 5.6) |
| `exposure.shutter_speed` | ExposureTime (33434) | Shutter speed | String (e.g., "1/125", "2.5s") |
| `exposure.focal_length` | FocalLength (37386) | Lens focal length in mm | Float (e.g., 50.0, 85.0) |
| `exposure.flash` | Flash (37385) | Flash fired status | Boolean or String |

### Priority 3: Camera Information (Optional but Useful)

| Field Name | EXIF Tag | Description | Format |
|------------|----------|-------------|---------|
| `camera.make` | Make (271) | Camera manufacturer | String (e.g., "Canon") |
| `camera.model` | Model (272) | Camera model | String (e.g., "EOS R6") |
| `camera.lens_model` | LensModel (42036) | Lens model | String (e.g., "RF 24-105mm F4L IS USM") |
| `camera.serial_number` | BodySerialNumber (42033) | Camera serial number | String |

### Priority 4: Additional Technical Data (Optional)

| Field Name | EXIF Tag | Description | Format |
|------------|----------|-------------|---------|
| `exposure.exposure_mode` | ExposureMode (34850) | Auto/Manual/Program | String or Integer |
| `exposure.metering_mode` | MeteringMode (37383) | Metering pattern used | String or Integer |
| `exposure.white_balance` | WhiteBalance (37384) | WB setting | String or Integer |
| `image_info.orientation` | Orientation (274) | Image orientation | Integer (1-8) |
| `image_info.color_space` | ColorSpace (40961) | Color space (sRGB/Adobe RGB) | String |

## Complete JSON Structure Example

```json
{
  "exif_dict": {
    "date_taken": "2025-01-12 17:11:26",
    "gps": {
      "latitude": 59.9139,
      "longitude": 10.7522,
      "altitude": 12.5
    },
    "image_info": {
      "width": 6000,
      "height": 4000,
      "orientation": 1,
      "color_space": "sRGB"
    },
    "exposure": {
      "iso": 400,
      "f_number": 5.6,
      "shutter_speed": "1/250",
      "focal_length": 85.0,
      "exposure_compensation": 0.0,
      "flash": false,
      "exposure_mode": "Manual",
      "metering_mode": "Matrix",
      "white_balance": "Auto"
    },
    "camera": {
      "make": "Nikon",
      "model": "D850",
      "lens_model": "AF-S NIKKOR 85mm f/1.8G",
      "serial_number": "12345678"
    }
  }
}
```

## DateTime Format Standardization

### Input Formats (from EXIF)
- `"2025:01:12 17:11:26"` (Standard EXIF format)
- `"2025-01-12T17:11:26"` (ISO format)
- `"2025-01-12 17:11:26"` (Alternative format)

### Required Output Format
**Always convert to**: `"YYYY-MM-DD HH:MM:SS"`

```javascript
function standardizeDatetime(exifDate) {
    if (!exifDate) return null;
    
    // Convert EXIF format "2025:01:12 17:11:26" to "2025-01-12 17:11:26"
    return exifDate.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3');
}
```

## Error Handling Best Practices

### 1. Graceful Degradation
```javascript
function extractExifSafely(image) {
    const exifDict = {};
    
    try {
        // Extract date - multiple fallbacks
        const dateOriginal = EXIF.getTag(image, "DateTimeOriginal");
        const dateTime = EXIF.getTag(image, "DateTime");
        
        if (dateOriginal) {
            exifDict.date_taken = standardizeDatetime(dateOriginal);
        } else if (dateTime) {
            exifDict.date_taken = standardizeDatetime(dateTime);
        }
    } catch (error) {
        // Silent failure - date_taken will be undefined
        console.warn('Failed to extract date:', error);
    }
    
    try {
        // Extract GPS with validation
        const gpsData = extractGPS(image);
        if (gpsData && gpsData.latitude && gpsData.longitude) {
            exifDict.gps = gpsData;
        }
    } catch (error) {
        console.warn('Failed to extract GPS:', error);
    }
    
    return exifDict;
}
```

### 2. Validation Functions
```javascript
function isValidLatitude(lat) {
    return typeof lat === 'number' && lat >= -90 && lat <= 90;
}

function isValidLongitude(lon) {
    return typeof lon === 'number' && lon >= -180 && lon <= 180;
}

function validateGPS(gpsData) {
    if (!gpsData) return null;
    
    const { latitude, longitude } = gpsData;
    
    if (isValidLatitude(latitude) && isValidLongitude(longitude)) {
        return { latitude, longitude };
    }
    
    return null;
}
```

## Platform-Specific Libraries

### JavaScript/Web
- **exif-js**: Lightweight, easy to use
- **piexifjs**: Full-featured, supports modification
- **exif-reader**: Node.js focused

```bash
npm install exif-js
# or
npm install piexifjs
```

### Python
- **Pillow (PIL)**: Built-in EXIF support
- **exifread**: Detailed EXIF extraction

```bash
pip install Pillow
# or  
pip install exifread
```

### Swift/iOS
- **ImageIO**: Native iOS framework
- **Photos Framework**: For photos from library

### Android/Java
- **ExifInterface**: Android support library
- **metadata-extractor**: Java library

## Testing Your Implementation

### Test Cases
1. **JPEG with full EXIF** - Extract all available fields
2. **JPEG without EXIF** - Handle gracefully (empty object)
3. **RAW files** - Test format support
4. **GPS coordinates** - Verify DMS → decimal conversion
5. **Different orientations** - Portrait/landscape handling
6. **Various camera brands** - Canon, Nikon, Sony, etc.

### Validation Script Example
```javascript
function validateExifExtraction(testImage) {
    const exif = extractExifSafely(testImage);
    
    // Log results for manual verification
    console.log('Extracted EXIF:', JSON.stringify(exif, null, 2));
    
    // Automated checks
    if (exif.date_taken) {
        console.assert(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(exif.date_taken), 
                     'Date format should be YYYY-MM-DD HH:MM:SS');
    }
    
    if (exif.gps) {
        console.assert(isValidLatitude(exif.gps.latitude), 'Invalid latitude');
        console.assert(isValidLongitude(exif.gps.longitude), 'Invalid longitude');
    }
    
    return exif;
}
```

## Integration with ImaLink API

Send the extracted EXIF data with your ImageFile creation request:

```javascript
const imageFileData = {
    filename: file.name,
    file_size: file.size,
    hotpreview: hotpreviewBase64,
    exif_dict: extractExifSafely(file)
};

fetch('/api/v1/image-files', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(imageFileData)
});
```

The ImaLink backend will automatically:
- Extract `taken_at` from `exif_dict.date_taken`
- Extract `gps_latitude` from `exif_dict.gps.latitude`  
- Extract `gps_longitude` from `exif_dict.gps.longitude`
- Extract `width` from `exif_dict.image_info.width`
- Extract `height` from `exif_dict.image_info.height`
- Store the complete `exif_dict` for future use

## Summary

**Essential Implementation Steps:**

1. ✅ **GPS Conversion**: Always convert DMS → decimal degrees
2. ✅ **DateTime Standardization**: Use "YYYY-MM-DD HH:MM:SS" format
3. ✅ **Priority Fields**: Focus on date_taken, GPS, and dimensions first
4. ✅ **Error Handling**: Silent failures, graceful degradation
5. ✅ **Validation**: Verify coordinate ranges and date formats
6. ✅ **Testing**: Test with various image types and EXIF scenarios

The original image files remain unchanged, allowing future extraction of additional metadata as needed.