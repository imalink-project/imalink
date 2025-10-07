#!/usr/bin/env node

/**
 * ImaLink Image Processor CLI
 * 
 * Command-line interface for testing the image processor
 */

import { Command } from 'commander';
import { importImages, scanForImages, processImages } from '../image-processor/index.js';
import { formatFileSize } from '../image-processor/file-ops.js';
import path from 'path';

const program = new Command();

program
    .name('imalink-processor')
    .description('ImaLink Image Processor - CLI for image processing and import')
    .version('1.0.0');

program
    .command('scan')
    .description('Scan directory for supported image files')
    .argument('<source>', 'Source directory to scan')
    .option('-v, --verbose', 'Show detailed output')
    .action(async (source, options) => {
        console.log(`🔍 Scanning: ${source}`);
        console.log('');
        
        try {
            const imageFiles = await scanForImages(source, (progress) => {
                if (options.verbose) {
                    console.log(`Found: ${progress.current}`);
                }
            });
            
            console.log(`✅ Found ${imageFiles.length} image files`);
            
            if (options.verbose && imageFiles.length > 0) {
                console.log('\nFiles found:');
                imageFiles.forEach((file, index) => {
                    console.log(`  ${index + 1}. ${file.relativePath}`);
                });
            }
            
        } catch (error) {
            console.error(`❌ Error scanning directory: ${error.message}`);
            process.exit(1);
        }
    });

program
    .command('process')
    .description('Process images (extract EXIF, generate thumbnails)')
    .argument('<source>', 'Source directory to process')
    .option('-t, --thumbnails', 'Generate thumbnails (default: true)')
    .option('-e, --exif', 'Extract EXIF data (default: true)')
    .option('-s, --size <size>', 'Thumbnail size in pixels', '200')
    .option('-c, --concurrency <num>', 'Number of concurrent operations', '4')
    .option('-v, --verbose', 'Show detailed output')
    .action(async (source, options) => {
        console.log(`🎯 Processing images in: ${source}`);
        console.log('');
        
        const startTime = Date.now();
        
        try {
            // First scan for images
            const imageFiles = await scanForImages(source);
            console.log(`Found ${imageFiles.length} images to process`);
            
            if (imageFiles.length === 0) {
                console.log('No images found to process');
                return;
            }
            
            // Process images
            const processOptions = {
                generateThumbnails: options.thumbnails !== false,
                extractExif: options.exif !== false,
                thumbnailSize: parseInt(options.size),
                concurrency: parseInt(options.concurrency)
            };
            
            console.log('Processing...');
            const results = await processImages(imageFiles, processOptions, (progress) => {
                const percentage = Math.round((progress.completed / progress.total) * 100);
                if (options.verbose) {
                    console.log(`[${percentage}%] Processing: ${progress.current}`);
                } else {
                    // Simple progress bar
                    process.stdout.write(`\r[${percentage.toString().padStart(3)}%] ${progress.completed}/${progress.total}`);
                }
            });
            
            if (!options.verbose) {
                console.log(''); // New line after progress bar
            }
            
            // Summary
            const successful = results.filter(r => r.success).length;
            const failed = results.filter(r => !r.success).length;
            const duration = Date.now() - startTime;
            
            console.log(`\n✅ Processing complete!`);
            console.log(`   Successful: ${successful}`);
            console.log(`   Failed: ${failed}`);
            console.log(`   Duration: ${(duration / 1000).toFixed(1)}s`);
            
            if (failed > 0 && options.verbose) {
                console.log('\nFailed files:');
                results.filter(r => !r.success).forEach(result => {
                    console.log(`  ❌ ${result.file.filename}: ${result.error}`);
                });
            }
            
        } catch (error) {
            console.error(`❌ Error processing images: ${error.message}`);
            process.exit(1);
        }
    });

program
    .command('import')
    .description('Complete import workflow: scan, process, and copy to storage')
    .argument('<source>', 'Source directory')
    .argument('<storage>', 'Storage destination directory')
    .option('-t, --thumbnails', 'Generate thumbnails (default: true)')
    .option('-e, --exif', 'Extract EXIF data (default: true)')
    .option('-s, --size <size>', 'Thumbnail size in pixels', '200')
    .option('-c, --concurrency <num>', 'Number of concurrent operations', '4')
    .option('-v, --verbose', 'Show detailed output')
    .action(async (source, storage, options) => {
        console.log(`📦 Importing from: ${source}`);
        console.log(`📁 Storage location: ${storage}`);
        console.log('');
        
        try {
            const importOptions = {
                generateThumbnails: options.thumbnails !== false,
                extractExif: options.exif !== false,
                thumbnailSize: parseInt(options.size),
                concurrency: parseInt(options.concurrency)
            };
            
            const result = await importImages(source, storage, importOptions, (progress) => {
                switch (progress.type) {
                    case 'phase':
                        console.log(`🔄 ${progress.message}`);
                        break;
                    case 'scan':
                        if (options.verbose) {
                            console.log(`   Found: ${progress.current}`);
                        }
                        break;
                    case 'process':
                        const percentage = Math.round((progress.completed / progress.total) * 100);
                        if (options.verbose) {
                            console.log(`   [${percentage}%] Processing: ${progress.current}`);
                        } else {
                            process.stdout.write(`\r   [${percentage.toString().padStart(3)}%] ${progress.completed}/${progress.total}`);
                        }
                        break;
                    case 'copy':
                        const copyPercentage = Math.round((progress.completed / progress.total) * 100);
                        if (options.verbose) {
                            console.log(`   [${copyPercentage}%] Copying: ${progress.current}`);
                        } else {
                            process.stdout.write(`\r   [${copyPercentage.toString().padStart(3)}%] ${progress.completed}/${progress.total}`);
                        }
                        break;
                }
            });
            
            if (!options.verbose) {
                console.log(''); // New line after progress bars
            }
            
            console.log('\n🎉 Import completed!');
            console.log(`   Total found: ${result.summary.totalFound}`);
            console.log(`   Successful: ${result.summary.successful}`);
            console.log(`   Failed: ${result.summary.failed}`);
            console.log(`   Duration: ${(result.summary.duration / 1000).toFixed(1)}s`);
            
        } catch (error) {
            console.error(`❌ Import failed: ${error.message}`);
            process.exit(1);
        }
    });

program
    .command('info')
    .description('Show information about a directory')
    .argument('<path>', 'Directory path')
    .action(async (dirPath) => {
        console.log(`📊 Directory Info: ${dirPath}`);
        console.log('');
        
        try {
            const imageFiles = await scanForImages(dirPath);
            console.log(`Images found: ${imageFiles.length}`);
            
            if (imageFiles.length > 0) {
                // Group by extension
                const extensions = {};
                imageFiles.forEach(file => {
                    const ext = path.extname(file.filename).toLowerCase();
                    extensions[ext] = (extensions[ext] || 0) + 1;
                });
                
                console.log('\nFile types:');
                Object.entries(extensions).forEach(([ext, count]) => {
                    console.log(`  ${ext}: ${count} files`);
                });
            }
            
        } catch (error) {
            console.error(`❌ Error getting directory info: ${error.message}`);
            process.exit(1);
        }
    });

// Parse command line arguments
program.parse();