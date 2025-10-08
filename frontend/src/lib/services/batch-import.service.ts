/**
 * Modern Batch Import Service
 * 
 * Kombinerer File System Access API med Photos batch API for effektiv import
 * av store mengder bilder (50,000+) direkte fra brukerens filsystem.
 * 
 * Arkitektur:
 * 1. Velg katalog med File System Access API
 * 2. Skann for bildefiler client-side
 * 3. Prosesser filer (EXIF, thumbnails) i batches
 * 4. Send PhotoGroups til backend via batch API
 */

import { selectImagesSmart, scanDirectoryForImages, readFileAsArrayBuffer } from './file-system-access.service.js';
import { PhotosApi } from '../api/photos.js';
import { processImage } from '../image-processor/index.js';
import type { PhotoGroupBatchRequest, PhotoGroupRequest, ImageCreateRequest, BatchPhotoResponse } from '../types/api.js';

export interface BatchImportOptions {
    authorId?: number;
    batchSize?: number;
    maxConcurrency?: number;
    generateThumbnails?: boolean;
    extractExif?: boolean;
    onProgress?: (progress: BatchImportProgress) => void;
    onBatchComplete?: (batchResult: BatchPhotoResponse) => void;
}

export interface BatchImportProgress {
    phase: 'scanning' | 'processing' | 'uploading' | 'completed' | 'error';
    totalFiles: number;
    processedFiles: number;
    currentFile?: string;
    percentage: number;
    batchesCompleted: number;
    totalBatches: number;
    errors: string[];
}

export interface BatchImportResult {
    success: boolean;
    totalFiles: number;
    photosCreated: number;
    photosFailed: number;
    imagesCreated: number;
    imagesFailed: number;
    processingTimeSeconds: number;
    errors: string[];
}

/**
 * Modern Batch Import Service Class
 */
export class BatchImportService {
    private options: BatchImportOptions;
    private progress: BatchImportProgress;
    private abortController: AbortController | null = null;

    constructor(options: BatchImportOptions = {}) {
        this.options = {
            batchSize: 50,
            maxConcurrency: 4,
            generateThumbnails: true,
            extractExif: true,
            ...options
        };

        this.progress = {
            phase: 'scanning',
            totalFiles: 0,
            processedFiles: 0,
            percentage: 0,
            batchesCompleted: 0,
            totalBatches: 0,
            errors: []
        };
    }

    /**
     * Start batch import process
     */
    async startImport(): Promise<BatchImportResult> {
        this.abortController = new AbortController();
        const startTime = Date.now();

        try {
            // Phase 1: Select and scan directory
            this.updateProgress({ phase: 'scanning' });
            const selectionResult = await selectImagesSmart({
                progressCallback: (scanProgress) => {
                    this.updateProgress({
                        currentFile: scanProgress.currentFile,
                        totalFiles: scanProgress.found
                    });
                }
            });

            const { files } = selectionResult;
            if (files.length === 0) {
                throw new Error('No image files found in selected directory');
            }

            this.updateProgress({
                totalFiles: files.length,
                totalBatches: Math.ceil(files.length / this.options.batchSize!)
            });

            // Phase 2: Process files in batches
            this.updateProgress({ phase: 'processing' });
            const photoGroups = await this.processFilesInBatches(files);

            // Phase 3: Upload to backend in batches
            this.updateProgress({ phase: 'uploading' });
            const results = await this.uploadInBatches(photoGroups);

            // Calculate final results
            const totalPhotosCreated = results.reduce((sum, r) => sum + r.photos_created, 0);
            const totalPhotosFailed = results.reduce((sum, r) => sum + r.photos_failed, 0);
            const totalImagesCreated = results.reduce((sum, r) => sum + r.images_created, 0);
            const totalImagesFailed = results.reduce((sum, r) => sum + r.images_failed, 0);

            this.updateProgress({ phase: 'completed', percentage: 100 });

            return {
                success: true,
                totalFiles: files.length,
                photosCreated: totalPhotosCreated,
                photosFailed: totalPhotosFailed,
                imagesCreated: totalImagesCreated,
                imagesFailed: totalImagesFailed,
                processingTimeSeconds: (Date.now() - startTime) / 1000,
                errors: this.progress.errors
            };

        } catch (error: any) {
            this.updateProgress({ 
                phase: 'error',
                errors: [...this.progress.errors, error.message]
            });

            return {
                success: false,
                totalFiles: this.progress.totalFiles,
                photosCreated: 0,
                photosFailed: this.progress.totalFiles,
                imagesCreated: 0,
                imagesFailed: this.progress.totalFiles,
                processingTimeSeconds: (Date.now() - startTime) / 1000,
                errors: this.progress.errors
            };
        }
    }

    /**
     * Cancel ongoing import
     */
    cancel(): void {
        if (this.abortController) {
            this.abortController.abort();
        }
    }

    /**
     * Process files in batches to create PhotoGroups
     */
    private async processFilesInBatches(files: any[]): Promise<PhotoGroupRequest[]> {
        const photoGroups: PhotoGroupRequest[] = [];
        const batches = this.createBatches(files, this.options.maxConcurrency!);

        for (const batch of batches) {
            if (this.abortController?.signal.aborted) {
                throw new Error('Import cancelled by user');
            }

            const batchPromises = batch.map(file => this.processFile(file));
            const batchResults = await Promise.allSettled(batchPromises);

            for (const result of batchResults) {
                if (result.status === 'fulfilled' && result.value) {
                    photoGroups.push(result.value);
                } else if (result.status === 'rejected') {
                    this.progress.errors.push(`Failed to process file: ${result.reason}`);
                }

                this.progress.processedFiles++;
                this.updateProgress({
                    percentage: Math.floor((this.progress.processedFiles / this.progress.totalFiles) * 50) // 50% for processing
                });
            }
        }

        return photoGroups;
    }

    /**
     * Process single file to create PhotoGroup
     */
    private async processFile(fileInfo: any): Promise<PhotoGroupRequest | null> {
        try {
            this.updateProgress({ currentFile: fileInfo.name });

            // Process image (EXIF, thumbnail, etc.)
            const processedImage = await processImage(fileInfo.file, {
                generateThumbnails: this.options.generateThumbnails,
                extractExif: this.options.extractExif,
                thumbnailSize: 300
            });

            if (!processedImage.success) {
                throw new Error(processedImage.error || 'Failed to process image');
            }

            // Create hothash (simplified - should use proper hashing)
            const hothash = this.generateHothash(fileInfo.name, fileInfo.size);

            // Create ImageCreateRequest
            const imageRequest: ImageCreateRequest = {
                filename: fileInfo.name,
                hothash: hothash,
                file_size: fileInfo.size,
                exif_data: processedImage.exif ? new TextEncoder().encode(JSON.stringify(processedImage.exif)) : undefined
            };

            // Create PhotoGroupRequest
            const photoGroup: PhotoGroupRequest = {
                hothash: hothash,
                hotpreview: processedImage.thumbnail,
                width: processedImage.width,
                height: processedImage.height,
                taken_at: processedImage.taken_date ? processedImage.taken_date.toISOString() : undefined,
                gps_latitude: processedImage.exif?.gps_latitude,
                gps_longitude: processedImage.exif?.gps_longitude,
                images: [imageRequest]
            };

            return photoGroup;

        } catch (error: any) {
            this.progress.errors.push(`Failed to process ${fileInfo.name}: ${error.message}`);
            return null;
        }
    }

    /**
     * Upload PhotoGroups to backend in batches
     */
    private async uploadInBatches(photoGroups: PhotoGroupRequest[]): Promise<BatchPhotoResponse[]> {
        const results: BatchPhotoResponse[] = [];
        const batches = this.createBatches(photoGroups, this.options.batchSize!);

        for (let i = 0; i < batches.length; i++) {
            if (this.abortController?.signal.aborted) {
                throw new Error('Import cancelled by user');
            }

            const batch = batches[i];
            const batchRequest: PhotoGroupBatchRequest = {
                photo_groups: batch,
                author_id: this.options.authorId
            };

            try {
                const result = await PhotosApi.createBatch(batchRequest);
                results.push(result);

                if (this.options.onBatchComplete) {
                    this.options.onBatchComplete(result);
                }

                this.progress.batchesCompleted++;
                this.updateProgress({
                    percentage: 50 + Math.floor((this.progress.batchesCompleted / this.progress.totalBatches) * 50) // 50% + upload progress
                });

            } catch (error: any) {
                this.progress.errors.push(`Batch ${i + 1} failed: ${error.message}`);
                
                // Create failed result for this batch
                const failedResult: BatchPhotoResponse = {
                    success: false,
                    total_requested: batch.length,
                    photos_created: 0,
                    photos_failed: batch.length,
                    images_created: 0,
                    images_failed: batch.reduce((sum, pg) => sum + pg.images.length, 0),
                    processing_time_seconds: 0,
                    results: [],
                    error: error.message
                };
                results.push(failedResult);
            }
        }

        return results;
    }

    /**
     * Update progress and notify callback
     */
    private updateProgress(update: Partial<BatchImportProgress>): void {
        this.progress = { ...this.progress, ...update };
        
        if (this.options.onProgress) {
            this.options.onProgress(this.progress);
        }
    }

    /**
     * Create batches from array
     */
    private createBatches<T>(items: T[], batchSize: number): T[][] {
        const batches: T[][] = [];
        for (let i = 0; i < items.length; i += batchSize) {
            batches.push(items.slice(i, i + batchSize));
        }
        return batches;
    }

    /**
     * Generate hothash (simplified implementation)
     */
    private generateHothash(filename: string, size: number): string {
        const data = `${filename}-${size}-${Date.now()}`;
        return btoa(data).substring(0, 32).replace(/[+/=]/g, '');
    }
}