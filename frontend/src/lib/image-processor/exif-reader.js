/**
 * EXIF Data Reader
 * 
 * Extracts metadata from image files using exifreader
 */

import ExifReader from 'exifreader';
import fs from 'fs/promises';

/**
 * Read and parse EXIF data from image file
 */
export async function readExifData(filePath) {
    try {
        const buffer = await fs.readFile(filePath);
        const tags = ExifReader.load(buffer);
        
        // Extract commonly used EXIF fields
        const exifData = {
            // Basic image info
            width: getTagValue(tags, 'Image Width') || getTagValue(tags, 'PixelXDimension'),
            height: getTagValue(tags, 'Image Height') || getTagValue(tags, 'PixelYDimension'),
            orientation: getTagValue(tags, 'Orientation'),
            
            // Camera info
            make: getTagValue(tags, 'Make'),
            model: getTagValue(tags, 'Model'),
            lens: getTagValue(tags, 'LensModel') || getTagValue(tags, 'Lens'),
            
            // Capture settings
            iso: getTagValue(tags, 'ISOSpeedRatings') || getTagValue(tags, 'ISO'),
            aperture: getTagValue(tags, 'FNumber'),
            shutterSpeed: getTagValue(tags, 'ExposureTime'),
            focalLength: getTagValue(tags, 'FocalLength'),
            exposureProgram: getTagValue(tags, 'ExposureProgram'),
            meteringMode: getTagValue(tags, 'MeteringMode'),
            flash: getTagValue(tags, 'Flash'),
            whiteBalance: getTagValue(tags, 'WhiteBalance'),
            
            // Date/time
            dateTime: getTagValue(tags, 'DateTime'),
            dateTimeOriginal: getTagValue(tags, 'DateTimeOriginal'),
            dateTimeDigitized: getTagValue(tags, 'DateTimeDigitized'),
            
            // GPS data
            gpsLatitude: getGpsCoordinate(tags, 'GPSLatitude', 'GPSLatitudeRef'),
            gpsLongitude: getGpsCoordinate(tags, 'GPSLongitude', 'GPSLongitudeRef'),
            gpsAltitude: getTagValue(tags, 'GPSAltitude'),
            
            // Software
            software: getTagValue(tags, 'Software'),
            processingTime: getTagValue(tags, 'ProcessingTime'),
            
            // Raw EXIF for debugging/advanced use
            rawExif: extractRelevantTags(tags)
        };
        
        // Clean up undefined values
        return cleanExifData(exifData);
        
    } catch (error) {
        throw new Error(`Failed to read EXIF data: ${error.message}`);
    }
}

/**
 * Get tag value with fallback handling
 */
function getTagValue(tags, tagName) {
    const tag = tags[tagName];
    if (!tag) return null;
    
    // Handle different tag value formats
    if (typeof tag.value !== 'undefined') {
        return tag.value;
    }
    if (typeof tag.description !== 'undefined') {
        return tag.description;
    }
    return tag;
}

/**
 * Convert GPS coordinates to decimal degrees
 */
function getGpsCoordinate(tags, coordTag, refTag) {
    const coord = getTagValue(tags, coordTag);
    const ref = getTagValue(tags, refTag);
    
    if (!coord || !ref) return null;
    
    try {
        let decimal = 0;
        if (Array.isArray(coord)) {
            // Convert from degrees, minutes, seconds
            decimal = coord[0] + (coord[1] / 60) + (coord[2] / 3600);
        } else if (typeof coord === 'number') {
            decimal = coord;
        } else {
            return null;
        }
        
        // Apply hemisphere reference
        if (ref === 'S' || ref === 'W') {
            decimal = -decimal;
        }
        
        return decimal;
    } catch (error) {
        return null;
    }
}

/**
 * Extract only relevant tags for debugging
 */
function extractRelevantTags(tags) {
    const relevant = {};
    const keepTags = [
        'Make', 'Model', 'DateTime', 'DateTimeOriginal', 'Orientation', 
        'XResolution', 'YResolution', 'Software', 'ExposureTime', 'FNumber',
        'ISOSpeedRatings', 'FocalLength', 'LensModel', 'ColorSpace'
    ];
    
    for (const tagName of keepTags) {
        if (tags[tagName]) {
            relevant[tagName] = tags[tagName];
        }
    }
    
    return relevant;
}

/**
 * Remove null/undefined values from EXIF data
 */
function cleanExifData(exifData) {
    const cleaned = {};
    for (const [key, value] of Object.entries(exifData)) {
        if (value !== null && value !== undefined) {
            cleaned[key] = value;
        }
    }
    return cleaned;
}

/**
 * Extract date from EXIF data with fallbacks
 */
export function extractPhotoDate(exifData) {
    // Try different date fields in order of preference
    const dateFields = ['dateTimeOriginal', 'dateTimeDigitized', 'dateTime'];
    
    for (const field of dateFields) {
        if (exifData[field]) {
            try {
                // EXIF dates are in format "YYYY:MM:DD HH:MM:SS"
                const dateStr = exifData[field].toString().replace(/:/g, '-', 2);
                const date = new Date(dateStr);
                if (!isNaN(date.getTime())) {
                    return date;
                }
            } catch (error) {
                continue;
            }
        }
    }
    
    return null;
}

/**
 * Generate a human-readable camera description
 */
export function getCameraDescription(exifData) {
    const parts = [];
    
    if (exifData.make) parts.push(exifData.make);
    if (exifData.model) parts.push(exifData.model);
    if (exifData.lens) parts.push(`(${exifData.lens})`);
    
    return parts.join(' ') || 'Unknown Camera';
}