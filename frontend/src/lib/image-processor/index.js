/**
 * ImaLink Image Processor
 * 
 * Standalone Node.js module for processing images:
 * - EXIF data extraction
 * - Thumbnail generation  
 * - File copying operations
 * - Progress tracking
 */

import { readExifData } from './exif-reader.js';
import { generateThumbnail } from './thumbnail.js';
import { copyFileWithStructure, ensureDirectoryExists } from './file-ops.js';
import fs from 'fs/promises';
import path from 'path';

/**
 * Supported image file extensions
 */
const SUPPORTED_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.tiff', '.tif', 
    '.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2'
];

/**
 * Check if file is a supported image format
 */
export function isSupportedImageFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return SUPPORTED_EXTENSIONS.includes(ext);
}

/**
 * Scan directory recursively for image files
 */
export async function scanForImages(sourcePath, progressCallback = null) {
    const imageFiles = [];
    
    async function scanRecursive(currentPath, relativePath = '') {
        try {
            const entries = await fs.readdir(currentPath, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(currentPath, entry.name);
                const relativeFilePath = path.join(relativePath, entry.name);
                
                if (entry.isDirectory()) {
                    // Recurse into subdirectories
                    await scanRecursive(fullPath, relativeFilePath);
                } else if (entry.isFile() && isSupportedImageFile(fullPath)) {
                    imageFiles.push({
                        fullPath,
                        relativePath: relativeFilePath,
                        filename: entry.name,
                        directory: relativePath
                    });
                    
                    if (progressCallback) {
                        progressCallback({
                            type: 'scan',
                            found: imageFiles.length,
                            current: relativeFilePath
                        });
                    }
                }
            }
        } catch (error) {
            console.warn(`Warning: Could not scan directory ${currentPath}:`, error.message);
        }
    }
    
    await scanRecursive(sourcePath);
    return imageFiles;
}

/**
 * Process a single image file
 */
export async function processImage(imageFile, options = {}) {
    const {
        generateThumbnails = true,
        thumbnailSize = 200,
        extractExif = true
    } = options;
    
    try {
        const result = {
            file: imageFile,
            success: false,
            error: null,
            exifData: null,
            thumbnail: null,
            fileInfo: null
        };
        
        // Get file stats
        const stats = await fs.stat(imageFile.fullPath);
        result.fileInfo = {
            size: stats.size,
            modified: stats.mtime,
            created: stats.birthtime
        };
        
        // Extract EXIF data
        if (extractExif) {
            try {
                result.exifData = await readExifData(imageFile.fullPath);
            } catch (error) {
                console.warn(`Warning: Could not extract EXIF from ${imageFile.filename}:`, error.message);
            }
        }
        
        // Generate thumbnail
        if (generateThumbnails) {
            try {
                result.thumbnail = await generateThumbnail(imageFile.fullPath, thumbnailSize);
            } catch (error) {
                console.warn(`Warning: Could not generate thumbnail for ${imageFile.filename}:`, error.message);
            }
        }
        
        result.success = true;
        return result;
        
    } catch (error) {
        return {
            file: imageFile,
            success: false,
            error: error.message,
            exifData: null,
            thumbnail: null,
            fileInfo: null
        };
    }
}

/**
 * Process multiple images with progress tracking
 */
export async function processImages(imageFiles, options = {}, progressCallback = null) {
    const {
        concurrency = 4  // Process 4 images in parallel
    } = options;
    
    const results = [];
    const total = imageFiles.length;
    let completed = 0;
    
    // Process images in batches for controlled concurrency
    for (let i = 0; i < imageFiles.length; i += concurrency) {
        const batch = imageFiles.slice(i, i + concurrency);
        
        const batchPromises = batch.map(async (imageFile) => {
            const result = await processImage(imageFile, options);
            completed++;
            
            if (progressCallback) {
                progressCallback({
                    type: 'process',
                    completed,
                    total,
                    current: imageFile.filename,
                    percentage: Math.round((completed / total) * 100)
                });
            }
            
            return result;
        });
        
        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);
    }
    
    return results;
}

/**
 * Copy processed images to storage location
 */
export async function copyImagesToStorage(processedImages, sourcePath, storagePath, progressCallback = null) {
    await ensureDirectoryExists(storagePath);
    
    const copyResults = [];
    let completed = 0;
    const total = processedImages.length;
    
    for (const processed of processedImages) {
        if (!processed.success) {
            copyResults.push({
                ...processed,
                copied: false,
                copyError: 'Processing failed'
            });
            continue;
        }
        
        try {
            const sourceFile = processed.file.fullPath;
            const relativePath = processed.file.relativePath;
            const targetPath = path.join(storagePath, relativePath);
            
            await copyFileWithStructure(sourceFile, targetPath);
            
            copyResults.push({
                ...processed,
                copied: true,
                copyPath: targetPath
            });
            
        } catch (error) {
            copyResults.push({
                ...processed,
                copied: false,
                copyError: error.message
            });
        }
        
        completed++;
        if (progressCallback) {
            progressCallback({
                type: 'copy',
                completed,
                total,
                current: processed.file.filename,
                percentage: Math.round((completed / total) * 100)
            });
        }
    }
    
    return copyResults;
}

/**
 * Main import function - complete workflow
 */
export async function importImages(sourcePath, storagePath, options = {}, progressCallback = null) {
    const startTime = Date.now();
    
    try {
        // Phase 1: Scan for images
        if (progressCallback) progressCallback({ type: 'phase', phase: 'scan', message: 'Scanning for images...' });
        const imageFiles = await scanForImages(sourcePath, progressCallback);
        
        if (imageFiles.length === 0) {
            throw new Error('No supported image files found in source directory');
        }
        
        // Phase 2: Process images
        if (progressCallback) progressCallback({ type: 'phase', phase: 'process', message: `Processing ${imageFiles.length} images...` });
        const processedImages = await processImages(imageFiles, options, progressCallback);
        
        // Phase 3: Copy to storage
        if (progressCallback) progressCallback({ type: 'phase', phase: 'copy', message: 'Copying images to storage...' });
        const copyResults = await copyImagesToStorage(processedImages, sourcePath, storagePath, progressCallback);
        
        // Generate summary
        const successful = copyResults.filter(r => r.success && r.copied);
        const failed = copyResults.filter(r => !r.success || !r.copied);
        
        const duration = Date.now() - startTime;
        
        return {
            success: true,
            summary: {
                totalFound: imageFiles.length,
                successful: successful.length,
                failed: failed.length,
                duration: duration
            },
            results: copyResults,
            sourcePath,
            storagePath
        };
        
    } catch (error) {
        return {
            success: false,
            error: error.message,
            summary: {
                totalFound: 0,
                successful: 0,
                failed: 0,
                duration: Date.now() - startTime
            }
        };
    }
}