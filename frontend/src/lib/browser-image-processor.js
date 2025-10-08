/**
 * ImaLink Complete Image Import System
 * 
 * Full-featured JavaScript library for image import:
 * - Directory scanning (using webkitdirectory)
 * - Single file and JPEG/RAW pair detection
 * - EXIF data extraction
 * - Hotpreview generation
 * - Database Image and Photo object creation
 */

/**
 * Supported image file extensions and types
 */
export const SUPPORTED_EXTENSIONS = {
    jpeg: ['.jpg', '.jpeg'],
    raw: ['.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2'],
    other: ['.png', '.tiff', '.tif']
};

export const SUPPORTED_MIME_TYPES = [
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/tiff',
    'image/tif'
];

/**
 * Check if file is a supported image type
 */
export function isSupportedImage(file) {
    const ext = getFileExtension(file.name).toLowerCase();
    return Object.values(SUPPORTED_EXTENSIONS).flat().includes(ext);
}

/**
 * Get file extension from filename
 */
export function getFileExtension(filename) {
    return filename.substring(filename.lastIndexOf('.'));
}

/**
 * Get base filename without extension
 */
export function getBaseName(filename) {
    return filename.substring(0, filename.lastIndexOf('.'));
}

/**
 * Determine file type category
 */
export function getFileCategory(filename) {
    const ext = getFileExtension(filename).toLowerCase();
    
    if (SUPPORTED_EXTENSIONS.jpeg.includes(ext)) return 'jpeg';
    if (SUPPORTED_EXTENSIONS.raw.includes(ext)) return 'raw';
    if (SUPPORTED_EXTENSIONS.other.includes(ext)) return 'other';
    
    return 'unknown';
}

/**
 * Extract basic EXIF data from image file
 * Uses browser's built-in image loading
 */
export async function extractImageMetadata(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        img.onload = function() {
            // Get basic image dimensions
            const metadata = {
                filename: file.name,
                file_size: file.size,
                width: img.naturalWidth,
                height: img.naturalHeight,
                file_format: file.type.split('/')[1] || 'unknown',
                taken_date: file.lastModified ? new Date(file.lastModified).toISOString() : null
            };
            
            resolve(metadata);
        };
        
        img.onerror = () => reject(new Error('Failed to load image'));
        img.src = URL.createObjectURL(file);
    });
}

/**
 * Generate thumbnail from image file
 * Returns base64 encoded JPEG thumbnail
 */
export async function generateThumbnail(file, maxSize = 300) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        img.onload = function() {
            // Calculate thumbnail dimensions
            let { width, height } = img;
            
            if (width > height) {
                if (width > maxSize) {
                    height = height * (maxSize / width);
                    width = maxSize;
                }
            } else {
                if (height > maxSize) {
                    width = width * (maxSize / height);
                    height = maxSize;
                }
            }
            
            // Draw resized image on canvas
            canvas.width = width;
            canvas.height = height;
            ctx.drawImage(img, 0, 0, width, height);
            
            // Convert to base64 JPEG
            const base64 = canvas.toDataURL('image/jpeg', 0.8);
            // Remove data:image/jpeg;base64, prefix
            const base64Data = base64.split(',')[1];
            
            resolve(base64Data);
        };
        
        img.onerror = () => reject(new Error('Failed to generate thumbnail'));
        img.src = URL.createObjectURL(file);
    });
}

/**
 * Process multiple image files
 * Returns array of processed image data
 */
export async function processImageFiles(files, progressCallback = null) {
    const processed = [];
    const failed = [];
    const total = files.length;
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        try {
            if (!isSupportedImage(file)) {
                throw new Error(`Unsupported file type: ${file.type}`);
            }
            
            // Extract metadata
            const metadata = await extractImageMetadata(file);
            
            // Generate thumbnail
            const thumbnail = await generateThumbnail(file);
            
            processed.push({
                ...metadata,
                hotpreview: thumbnail,
                file: file // Keep reference for potential upload
            });
            
            if (progressCallback) {
                progressCallback(i + 1, total, file.name);
            }
            
        } catch (error) {
            console.error(`Failed to process ${file.name}:`, error);
            failed.push({
                filename: file.name,
                error: error.message
            });
        }
    }
    
    return { processed, failed };
}

/**
 * Submit processed images to backend API
 * Sends only metadata as JSON, no actual file upload
 * 
 * @deprecated This function uses the old individual Image creation API
 * TODO: Replace with Photo batch API (POST /photos/batch) when implementing File System Access
 */
export async function submitImagesToAPI(processedImages, authorId = null, apiBase = 'http://localhost:8000') {
    const results = [];
    
    for (const imageData of processedImages) {
        try {
            // Create hothash from filename (simple approach)
            const hothash = btoa(imageData.filename + Date.now()).substring(0, 32);
            
            // Create JSON payload with metadata only
            const payload = {
                filename: imageData.filename,
                hothash: hothash,
                file_size: imageData.file_size,
                width: imageData.width,
                height: imageData.height,
                taken_at: imageData.taken_date,
                author_id: authorId || null
            };
            
            const response = await fetch(`${apiBase}/api/v1/images/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                const result = await response.json();
                results.push({
                    success: true,
                    filename: imageData.filename,
                    data: result
                });
            } else {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
        } catch (error) {
            results.push({
                success: false,
                filename: imageData.filename,
                error: error.message
            });
        }
    }
    
    return results;
}

/**
 * Simple file picker helper
 */
export function createFilePicker(multiple = true, accept = 'image/*') {
    return new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = multiple;
        input.accept = accept;
        
        input.onchange = (e) => {
            const files = Array.from(e.target.files || []);
            resolve(files);
        };
        
        input.click();
    });
}