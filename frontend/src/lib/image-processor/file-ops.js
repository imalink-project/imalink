/**
 * File Operations
 * 
 * File copying and directory management utilities
 */

import fs from 'fs/promises';
import path from 'path';

/**
 * Ensure directory exists, create if needed
 */
export async function ensureDirectoryExists(dirPath) {
    try {
        await fs.access(dirPath);
    } catch (error) {
        // Directory doesn't exist, create it
        await fs.mkdir(dirPath, { recursive: true });
    }
}

/**
 * Copy file while preserving directory structure
 */
export async function copyFileWithStructure(sourcePath, targetPath) {
    try {
        // Ensure target directory exists
        const targetDir = path.dirname(targetPath);
        await ensureDirectoryExists(targetDir);
        
        // Copy file
        await fs.copyFile(sourcePath, targetPath);
        
        // Copy file stats (timestamps, permissions)
        const stats = await fs.stat(sourcePath);
        await fs.utimes(targetPath, stats.atime, stats.mtime);
        
        return targetPath;
        
    } catch (error) {
        throw new Error(`Failed to copy file ${sourcePath} to ${targetPath}: ${error.message}`);
    }
}

/**
 * Check if path exists and is accessible
 */
export async function pathExists(filePath) {
    try {
        await fs.access(filePath);
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * Get file size in bytes
 */
export async function getFileSize(filePath) {
    try {
        const stats = await fs.stat(filePath);
        return stats.size;
    } catch (error) {
        throw new Error(`Failed to get file size: ${error.message}`);
    }
}

/**
 * Get directory size recursively
 */
export async function getDirectorySize(dirPath) {
    let totalSize = 0;
    
    try {
        const entries = await fs.readdir(dirPath, { withFileTypes: true });
        
        for (const entry of entries) {
            const fullPath = path.join(dirPath, entry.name);
            
            if (entry.isFile()) {
                const stats = await fs.stat(fullPath);
                totalSize += stats.size;
            } else if (entry.isDirectory()) {
                totalSize += await getDirectorySize(fullPath);
            }
        }
        
    } catch (error) {
        // Ignore errors for inaccessible directories
        console.warn(`Warning: Could not access directory ${dirPath}:`, error.message);
    }
    
    return totalSize;
}

/**
 * Format file size in human readable format
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Create unique filename if target already exists
 */
export async function createUniqueFilename(targetPath) {
    if (!await pathExists(targetPath)) {
        return targetPath;
    }
    
    const dir = path.dirname(targetPath);
    const ext = path.extname(targetPath);
    const basename = path.basename(targetPath, ext);
    
    let counter = 1;
    let uniquePath;
    
    do {
        uniquePath = path.join(dir, `${basename}_${counter}${ext}`);
        counter++;
    } while (await pathExists(uniquePath));
    
    return uniquePath;
}

/**
 * Move file from source to target
 */
export async function moveFile(sourcePath, targetPath) {
    try {
        // Ensure target directory exists
        const targetDir = path.dirname(targetPath);
        await ensureDirectoryExists(targetDir);
        
        // Try rename first (faster if on same filesystem)
        try {
            await fs.rename(sourcePath, targetPath);
            return targetPath;
        } catch (error) {
            // Fallback to copy + delete
            await copyFileWithStructure(sourcePath, targetPath);
            await fs.unlink(sourcePath);
            return targetPath;
        }
        
    } catch (error) {
        throw new Error(`Failed to move file ${sourcePath} to ${targetPath}: ${error.message}`);
    }
}

/**
 * Clean up empty directories recursively
 */
export async function cleanupEmptyDirectories(dirPath) {
    try {
        const entries = await fs.readdir(dirPath);
        
        if (entries.length === 0) {
            // Directory is empty, remove it
            await fs.rmdir(dirPath);
            
            // Try to clean up parent directory too
            const parentDir = path.dirname(dirPath);
            if (parentDir !== dirPath) {
                await cleanupEmptyDirectories(parentDir);
            }
        }
        
    } catch (error) {
        // Ignore errors (directory might not be empty or not accessible)
    }
}