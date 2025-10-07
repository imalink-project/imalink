/**
 * Thumbnail Generator
 * 
 * Generates thumbnails using Sharp for fast image processing
 */

import sharp from 'sharp';
import path from 'path';

/**
 * Generate thumbnail from image file
 */
export async function generateThumbnail(filePath, size = 200) {
    try {
        // Generate thumbnail buffer
        const thumbnailBuffer = await sharp(filePath)
            .resize(size, size, {
                fit: 'inside',
                withoutEnlargement: true
            })
            .jpeg({
                quality: 85,
                progressive: true
            })
            .toBuffer();
        
        // Return as base64 data URL for easy embedding
        const base64 = thumbnailBuffer.toString('base64');
        return `data:image/jpeg;base64,${base64}`;
        
    } catch (error) {
        throw new Error(`Failed to generate thumbnail: ${error.message}`);
    }
}

/**
 * Generate thumbnail and save to file
 */
export async function generateThumbnailFile(filePath, outputPath, size = 200) {
    try {
        await sharp(filePath)
            .resize(size, size, {
                fit: 'inside',
                withoutEnlargement: true
            })
            .jpeg({
                quality: 85,
                progressive: true
            })
            .toFile(outputPath);
        
        return outputPath;
        
    } catch (error) {
        throw new Error(`Failed to generate thumbnail file: ${error.message}`);
    }
}

/**
 * Get image dimensions without loading full image
 */
export async function getImageInfo(filePath) {
    try {
        const metadata = await sharp(filePath).metadata();
        
        return {
            width: metadata.width,
            height: metadata.height,
            format: metadata.format,
            channels: metadata.channels,
            hasAlpha: metadata.hasAlpha,
            orientation: metadata.orientation,
            density: metadata.density
        };
        
    } catch (error) {
        throw new Error(`Failed to get image info: ${error.message}`);
    }
}

/**
 * Apply EXIF orientation to fix rotation
 */
export async function applyOrientation(filePath) {
    try {
        const image = sharp(filePath);
        
        // Sharp automatically applies EXIF orientation when rotating
        // This returns a buffer with corrected orientation
        return await image
            .rotate() // Applies EXIF orientation
            .jpeg({ quality: 95 })
            .toBuffer();
            
    } catch (error) {
        throw new Error(`Failed to apply orientation: ${error.message}`);
    }
}

/**
 * Generate multiple thumbnail sizes
 */
export async function generateMultipleThumbnails(filePath, sizes = [200, 400, 800]) {
    const thumbnails = {};
    
    try {
        for (const size of sizes) {
            const thumbnail = await generateThumbnail(filePath, size);
            thumbnails[`thumb_${size}`] = thumbnail;
        }
        
        return thumbnails;
        
    } catch (error) {
        throw new Error(`Failed to generate multiple thumbnails: ${error.message}`);
    }
}