/**
 * Raw EXIF Data Extractor
 * 
 * Extracts raw EXIF binary data from images to send to backend
 * Backend handles all EXIF parsing using Python libraries
 */

import fs from 'fs/promises';

/**
 * Extract raw EXIF bytes from image file (Node.js version)
 * 
 * Uses the same approach as Python PIL: read the file and extract
 * the raw EXIF binary data segment
 */
export async function extractRawExifBytes(filePath) {
    try {
        // Read the entire file as a buffer
        const fileBuffer = await fs.readFile(filePath);
        
        // For JPEG files, extract EXIF segment
        if (isJpegFile(filePath)) {
            return extractJpegExifBytes(fileBuffer);
        }
        
        // For other formats, try to use existing EXIF libraries to get raw data
        return await extractGenericExifBytes(filePath);
        
    } catch (error) {
        console.warn(`Could not extract raw EXIF from ${filePath}:`, error.message);
        return null;
    }
}

/**
 * Extract raw EXIF bytes from browser File object
 * 
 * For browser usage with File System Access API
 */
export async function extractRawExifBytesFromFile(file) {
    try {
        const arrayBuffer = await file.arrayBuffer();
        const fileBuffer = Buffer.from(arrayBuffer);
        
        // For JPEG files, extract EXIF segment
        if (isJpegFile(file.name)) {
            return extractJpegExifBytes(fileBuffer);
        }
        
        // For other formats, return null (backend will handle missing EXIF gracefully)
        console.warn(`Raw EXIF extraction not implemented for non-JPEG: ${file.name}`);
        return null;
        
    } catch (error) {
        console.warn(`Could not extract raw EXIF from ${file.name}:`, error.message);
        return null;
    }
}

/**
 * Extract EXIF segment from JPEG buffer
 * 
 * JPEG EXIF data is stored in APP1 marker (0xFFE1)
 */
function extractJpegExifBytes(buffer) {
    try {
        // Look for JPEG markers
        if (buffer[0] !== 0xFF || buffer[1] !== 0xD8) {
            throw new Error('Not a valid JPEG file');
        }
        
        let offset = 2;
        
        // Scan for APP1 marker (0xFFE1) which contains EXIF
        while (offset < buffer.length - 1) {
            if (buffer[offset] === 0xFF && buffer[offset + 1] === 0xE1) {
                // Found APP1 marker
                const segmentLength = (buffer[offset + 2] << 8) | buffer[offset + 3];
                
                // Check if this is an EXIF segment (starts with "Exif\0\0")
                if (offset + 10 < buffer.length &&
                    buffer[offset + 4] === 0x45 && // 'E'
                    buffer[offset + 5] === 0x78 && // 'x'
                    buffer[offset + 6] === 0x69 && // 'i'
                    buffer[offset + 7] === 0x66 && // 'f'
                    buffer[offset + 8] === 0x00 && // '\0'
                    buffer[offset + 9] === 0x00) {  // '\0'
                    
                    // Extract the EXIF data (including the "Exif\0\0" header to match PIL)
                    const exifStart = offset + 4; // Start from "Exif\0\0"
                    const exifLength = segmentLength - 2; // Subtract only the segment length bytes
                    
                    return buffer.slice(exifStart, exifStart + exifLength);
                }
            }
            
            // Move to next marker
            if (buffer[offset] === 0xFF) {
                if (buffer[offset + 1] === 0xD9) break; // End of image
                
                // Skip this segment
                const segmentLength = (buffer[offset + 2] << 8) | buffer[offset + 3];
                offset += segmentLength + 2;
            } else {
                offset++;
            }
        }
        
        // No EXIF data found
        return null;
        
    } catch (error) {
        throw new Error(`Failed to extract JPEG EXIF: ${error.message}`);
    }
}

/**
 * Extract raw EXIF using ExifReader for non-JPEG files
 * 
 * Fallback method that uses the existing ExifReader library
 * but attempts to get raw binary data
 */
async function extractGenericExifBytes(filePath) {
    try {
        // Import ExifReader dynamically
        const ExifReader = (await import('exifreader')).default;
        
        const buffer = await fs.readFile(filePath);
        
        // Try to load EXIF and get raw data
        // Note: This is a simplified approach - some formats may need special handling
        const tags = ExifReader.load(buffer);
        
        // ExifReader doesn't directly provide raw EXIF bytes for non-JPEG
        // For now, return null and let backend handle missing EXIF
        console.warn(`Raw EXIF extraction not fully implemented for: ${filePath}`);
        return null;
        
    } catch (error) {
        // If ExifReader fails, that's OK - just return null
        return null;
    }
}

/**
 * Check if file is a JPEG
 */
function isJpegFile(filename) {
    const ext = filename.toLowerCase();
    return ext.endsWith('.jpg') || ext.endsWith('.jpeg');
}

/**
 * Get basic image dimensions without full EXIF parsing
 * 
 * Frontend still needs to provide dimensions since backend needs them
 * for the ImageProcessor.extract_metadata_from_raw_exif() call
 */
export async function getImageDimensions(filePath) {
    try {
        // Use sharp to get dimensions quickly
        const sharp = (await import('sharp')).default;
        const metadata = await sharp(filePath).metadata();
        
        return {
            width: metadata.width,
            height: metadata.height
        };
        
    } catch (error) {
        console.warn(`Could not get dimensions for ${filePath}:`, error.message);
        return { width: null, height: null };
    }
}

/**
 * Get basic image dimensions from browser File object
 */
export async function getImageDimensionsFromFile(file) {
    return new Promise((resolve) => {
        const img = new Image();
        
        img.onload = function() {
            resolve({
                width: img.naturalWidth,
                height: img.naturalHeight
            });
        };
        
        img.onerror = function() {
            console.warn(`Could not get dimensions for ${file.name}`);
            resolve({ width: null, height: null });
        };
        
        img.src = URL.createObjectURL(file);
    });
}