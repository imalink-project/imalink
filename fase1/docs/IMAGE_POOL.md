# Image Pool Service

Optimized image caching system for ImaLink that provides fast access to multiple image sizes.

## 🎯 Overview

The Image Pool Service creates and manages optimized versions of images in predefined sizes:

- **Small (400x400)**: Gallery grid view, quick browsing
- **Medium (800x800)**: Standard web viewing 
- **Large (1200x1200)**: Detailed viewing, zoom functionality

## ⚡ Key Features

### 🏗️ Algorithmic File Structure
- No database metadata required
- Hash-based directory structure: `{hash[:2]}/{hash[2:4]}/{hash}_{size}.jpg`
- Supports millions of images with optimal filesystem performance

### 🔄 Cascading Optimization
- Loads original image once, applies EXIF rotation
- Creates large → medium → small (reuses previous size as source)
- 2-4x faster than traditional approaches for large images

### 🛡️ Anti-Upscaling Protection
- Never enlarges images beyond their original size
- Preserves aspect ratio while respecting size constraints
- Intelligently skips unnecessary sizes

### 🎨 EXIF Processing Strategy
- **Bakes in EXIF rotation** permanently into pool images
- **Strips all EXIF data** for smaller file sizes and faster loading
- **Consistent orientation** across all browsers and devices
- **Original file unchanged** - retains all metadata

## 🗂️ File Structure

```
C:/temp/imalink_data/imalink_pool/
├── ab/
│   └── cd/
│       ├── abcd1234ef567890_small.jpg    # 400x400 max
│       ├── abcd1234ef567890_medium.jpg   # 800x800 max
│       └── abcd1234ef567890_large.jpg    # 1200x1200 max
└── ef/
    └── gh/
        └── efgh5678ijkl9012_medium.jpg   # Only sizes that need scaling
```

## 🔧 Configuration

Environment variables (`.env`):
```bash
IMAGE_POOL_DIRECTORY=C:/temp/imalink_data/imalink_pool
POOL_QUALITY=85
```

Code configuration:
```python
from config import config
from services.image_pool import ImagePoolService

# Initialize service
pool_service = ImagePoolService(config.IMAGE_POOL_DIRECTORY)
```

## 📡 API Endpoints

### Get Pool Image
```http
GET /api/images/{image_id}/pool/{size}
```

Parameters:
- `image_id`: Database ID of image
- `size`: `small`, `medium`, or `large`

Response:
- Optimized JPEG with aggressive caching headers
- ETag for conditional requests
- Custom headers with metadata

Example:
```bash
curl "http://localhost:8000/api/images/123/pool/medium"
```

### Response Headers
```
Cache-Control: public, max-age=31536000  # 1 year cache
ETag: "abcd1234_medium"
X-Pool-Size: medium
X-Image-Hash: abcd1234ef567890
```

## 🔄 Usage Patterns

### Frontend Integration
```javascript
// Use different sizes based on context
function getImageUrl(imageId, context) {
    const sizeMap = {
        'gallery': 'small',      // Grid view
        'detail': 'medium',      // Modal/detail view
        'fullscreen': 'large'    // Zoom/fullscreen
    };
    
    const size = sizeMap[context] || 'medium';
    return `/api/images/${imageId}/pool/${size}`;
}

// Progressive loading
function loadProgressiveImage(imageId) {
    const img = new Image();
    
    // Load small first for quick display
    img.src = `/api/images/${imageId}/pool/small`;
    img.onload = () => {
        // Replace with medium when loaded
        img.src = `/api/images/${imageId}/pool/medium`;
    };
    
    return img;
}
```

### Import Integration
Pool images are automatically generated during import:

```python
# In import process
image_record = create_image_record(file_path, source_description, db)
if image_record:
    # Generate pool versions in background
    pool_service.create_all_sizes_optimized(
        original_path=file_path,
        image_hash=image_record.image_hash,
        quality=config.POOL_QUALITY
    )
```

## 🛠️ Service Methods

### Core Operations
```python
# Get or create single size
pool_path = pool_service.get_or_create(
    original_path=Path("image.jpg"),
    image_hash="abcd1234",
    size="medium"
)

# Create all sizes optimized
created_paths = pool_service.create_all_sizes_optimized(
    original_path=Path("image.jpg"),
    image_hash="abcd1234",
    quality=85
)

# Check if version exists
exists = pool_service.exists("abcd1234", "large")
```

### Analysis & Maintenance
```python
# Analyze requirements for an image
analysis = pool_service.analyze_original_requirements(Path("image.jpg"))
print(f"Recommended sizes: {analysis['recommended_sizes']}")
print(f"Skippable sizes: {analysis['skippable_sizes']}")

# Get pool statistics
stats = pool_service.get_pool_stats()
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")

# Cleanup orphaned files
valid_hashes = ["hash1", "hash2", "hash3"]
deleted_count = pool_service.cleanup_orphaned_files(valid_hashes)
```

## 📊 Performance Benefits

### Storage Efficiency
- **75% smaller** than originals (typical JPEG compression)
- **No redundant EXIF data** (saves 2-50KB per file)
- **Progressive JPEG** for faster perceived loading

### Speed Improvements
- **Cascading scaling**: 2-4x faster generation
- **Single I/O operation** per image during bulk processing
- **Browser caching**: 1-year cache headers for pool images
- **CDN-friendly**: Optimized for content delivery networks

### Scalability
- **Hash-based structure** supports millions of images
- **No database queries** for file location
- **Parallel processing** safe (separate hash directories)
- **Memory efficient** cascading approach

## 🧪 Testing

Run the test script:
```bash
cd scripts/testing
python test_image_pool.py
```

Test coverage:
- ✅ Path generation algorithms
- ✅ Anti-upscaling protection  
- ✅ Size calculation logic
- ✅ Pool statistics
- ✅ Analysis functions
- ✅ Error handling

## 🔧 Maintenance

### Cleanup Script
```python
# scripts/maintenance/cleanup_pool.py
from services.image_pool import ImagePoolService
from models import Image

# Get valid hashes from database
valid_hashes = [img.image_hash for img in db.query(Image.image_hash).all()]

# Remove orphaned pool files
pool_service = ImagePoolService(config.IMAGE_POOL_DIRECTORY)
deleted = pool_service.cleanup_orphaned_files(valid_hashes)
print(f"Cleaned up {deleted} orphaned files")
```

### Monitoring
```python
# Check pool health
stats = pool_service.get_pool_stats()
expected_files = db.query(Image).count() * 3  # 3 sizes per image

if stats['total_files'] < expected_files * 0.8:
    print("Warning: Pool appears incomplete")
```

## 🎯 Future Enhancements

- **WebP format** option for modern browsers
- **AVIF format** for next-gen compression
- **Background regeneration** for quality upgrades
- **Cloud storage** integration (S3, Azure)
- **CDN purging** API integration
- **Selective size generation** based on usage patterns