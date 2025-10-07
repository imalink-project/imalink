/**
 * Frontend Image Processing Service
 * 
 * Wrapper around Node.js image processor for use in Svelte frontend
 */

import { importImages, scanForImages, processImages } from '../image-processor/index.js';

/**
 * Frontend-friendly image import service
 */
export class ImageImportService {
    constructor() {
        this.isProcessing = false;
        this.currentProgress = null;
        this.progressCallbacks = new Set();
    }

    /**
     * Add progress callback listener
     */
    onProgress(callback) {
        this.progressCallbacks.add(callback);
        return () => this.progressCallbacks.delete(callback);
    }

    /**
     * Broadcast progress to all listeners
     */
    _notifyProgress(progress) {
        this.currentProgress = progress;
        this.progressCallbacks.forEach(callback => {
            try {
                callback(progress);
            } catch (error) {
                console.error('Progress callback error:', error);
            }
        });
    }

    /**
     * Scan directory for images
     */
    async scanDirectory(sourcePath) {
        try {
            const imageFiles = await scanForImages(sourcePath, (progress) => {
                this._notifyProgress({
                    type: 'scan',
                    phase: 'scanning',
                    ...progress
                });
            });

            return {
                success: true,
                files: imageFiles,
                count: imageFiles.length
            };

        } catch (error) {
            return {
                success: false,
                error: error.message,
                files: [],
                count: 0
            };
        }
    }

    /**
     * Process images (EXIF + thumbnails)
     */
    async processImages(imageFiles, options = {}) {
        const defaultOptions = {
            generateThumbnails: true,
            extractExif: true,
            thumbnailSize: 200,
            concurrency: 4
        };

        const processOptions = { ...defaultOptions, ...options };

        try {
            this.isProcessing = true;
            
            const results = await processImages(imageFiles, processOptions, (progress) => {
                this._notifyProgress({
                    type: 'process',
                    phase: 'processing',
                    ...progress
                });
            });

            this.isProcessing = false;
            return {
                success: true,
                results,
                processed: results.filter(r => r.success).length,
                failed: results.filter(r => !r.success).length
            };

        } catch (error) {
            this.isProcessing = false;
            return {
                success: false,
                error: error.message,
                results: [],
                processed: 0,
                failed: 0
            };
        }
    }

    /**
     * Complete import workflow
     */
    async importImages(sourcePath, storagePath, options = {}) {
        try {
            this.isProcessing = true;

            const result = await importImages(sourcePath, storagePath, options, (progress) => {
                this._notifyProgress(progress);
            });

            this.isProcessing = false;
            return result;

        } catch (error) {
            this.isProcessing = false;
            return {
                success: false,
                error: error.message,
                summary: {
                    totalFound: 0,
                    successful: 0,
                    failed: 0,
                    duration: 0
                }
            };
        }
    }

    /**
     * Cancel current operation (if possible)
     */
    async cancel() {
        // For now, we don't have cancellation support in the processor
        // But we can set a flag for future enhancement
        this.isProcessing = false;
        this._notifyProgress({
            type: 'cancelled',
            message: 'Operation cancelled by user'
        });
    }

    /**
     * Get current processing status
     */
    getStatus() {
        return {
            isProcessing: this.isProcessing,
            currentProgress: this.currentProgress
        };
    }
}

/**
 * Create singleton instance
 */
export const imageImportService = new ImageImportService();