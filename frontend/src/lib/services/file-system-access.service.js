/**
 * File System Access API Service
 * 
 * Moderne implementasjon for client-side filbehandling som erstatter upload-baserte import.
 * Bruker File System Access API for å lese filer direkte fra brukerens filsystem
 * uten opplasting til server.
 * 
 * Kompatibilitet: Chrome 86+, Edge 86+ (krever HTTPS i produksjon)
 */

/**
 * Sjekk om File System Access API er tilgjengelig
 */
export function isFileSystemAccessSupported() {
    return 'showDirectoryPicker' in window;
}

/**
 * Velg katalog ved hjelp av File System Access API
 * @returns {Promise<FileSystemDirectoryHandle>} Katalog handle
 */
export async function selectDirectory() {
    if (!isFileSystemAccessSupported()) {
        throw new Error('File System Access API is not supported in this browser');
    }
    
    try {
        const directoryHandle = await window.showDirectoryPicker({
            mode: 'read'
        });
        
        return directoryHandle;
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Directory selection was cancelled');
        }
        throw new Error(`Failed to select directory: ${error.message}`);
    }
}

/**
 * Skann katalog for bildefiler
 * @param {FileSystemDirectoryHandle} directoryHandle - Katalog handle
 * @param {Object} options - Scanneinnstillinger
 * @param {string[]} options.supportedFormats - Støttede filformater
 * @param {boolean} options.recursive - Skann underkataloger
 * @param {Function} options.progressCallback - Progress callback
 * @returns {Promise<Object[]>} Array av fileinformasjon
 */
export async function scanDirectoryForImages(directoryHandle, options = {}) {
    const {
        supportedFormats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.dng', '.arw', '.cr2', '.nef', '.orf', '.rw2'],
        recursive = true,
        progressCallback = null
    } = options;
    
    const imageFiles = [];
    let scannedCount = 0;
    
    /**
     * Rekursiv scanning av katalog
     */
    async function scanDirectory(dirHandle, currentPath = '') {
        try {
            for await (const [name, handle] of dirHandle.entries()) {
                const fullPath = currentPath ? `${currentPath}/${name}` : name;
                
                if (handle.kind === 'file') {
                    // Sjekk om filen er et støttet bildeformat
                    const extension = name.toLowerCase().slice(name.lastIndexOf('.'));
                    if (supportedFormats.includes(extension)) {
                        const file = await handle.getFile();
                        
                        imageFiles.push({
                            name: name,
                            path: fullPath,
                            size: file.size,
                            type: file.type,
                            lastModified: file.lastModified,
                            handle: handle,
                            file: file
                        });
                    }
                    
                    scannedCount++;
                    if (progressCallback) {
                        progressCallback({
                            type: 'scan',
                            scanned: scannedCount,
                            found: imageFiles.length,
                            currentFile: fullPath
                        });
                    }
                    
                } else if (handle.kind === 'directory' && recursive) {
                    // Skann underkatalog
                    await scanDirectory(handle, fullPath);
                }
            }
        } catch (error) {
            console.warn(`Failed to scan directory ${currentPath}:`, error);
        }
    }
    
    await scanDirectory(directoryHandle);
    
    return imageFiles;
}

/**
 * Les filinnhold som ArrayBuffer
 * @param {FileSystemFileHandle} fileHandle - Fil handle
 * @returns {Promise<ArrayBuffer>} Filinnhold
 */
export async function readFileAsArrayBuffer(fileHandle) {
    try {
        const file = await fileHandle.getFile();
        return await file.arrayBuffer();
    } catch (error) {
        throw new Error(`Failed to read file: ${error.message}`);
    }
}

/**
 * Les filinnhold som tekst
 * @param {FileSystemFileHandle} fileHandle - Fil handle
 * @returns {Promise<string>} Filinnhold som tekst
 */
export async function readFileAsText(fileHandle) {
    try {
        const file = await fileHandle.getFile();
        return await file.text();
    } catch (error) {
        throw new Error(`Failed to read file as text: ${error.message}`);
    }
}

/**
 * Fallback for browsere som ikke støtter File System Access API
 * Bruker tradisjonell input[type="file"] metode
 * @param {Object} options - Valg
 * @param {boolean} options.multiple - Tillat flere filer
 * @param {boolean} options.directory - Tillat katalogvalg (webkitdirectory)
 * @returns {Promise<File[]>} Valgte filer
 */
export async function selectFilesLegacy(options = {}) {
    const {
        multiple = true,
        directory = true
    } = options;
    
    return new Promise((resolve, reject) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = multiple;
        input.accept = 'image/*';
        
        if (directory) {
            input.webkitdirectory = true;
        }
        
        input.onchange = (event) => {
            const files = Array.from(event.target.files || []);
            resolve(files);
        };
        
        input.oncancel = () => {
            reject(new Error('File selection was cancelled'));
        };
        
        // Trigger file picker
        input.click();
    });
}

/**
 * Smart filvelger som bruker File System Access API hvis tilgjengelig,
 * ellers fallback til tradisjonell metode
 * @param {Object} options - Innstillinger
 * @returns {Promise<Object>} Resultat med filinfo og scanning method
 */
export async function selectImagesSmart(options = {}) {
    if (isFileSystemAccessSupported()) {
        console.log('Using File System Access API');
        
        const directoryHandle = await selectDirectory();
        const imageFiles = await scanDirectoryForImages(directoryHandle, options);
        
        return {
            method: 'filesystem-access',
            directoryHandle,
            files: imageFiles,
            totalFiles: imageFiles.length
        };
        
    } else {
        console.log('Using legacy file input method');
        
        const files = await selectFilesLegacy(options);
        const imageFiles = files.map(file => ({
            name: file.name,
            path: file.webkitRelativePath || file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified,
            file: file
        }));
        
        return {
            method: 'legacy',
            files: imageFiles,
            totalFiles: imageFiles.length
        };
    }
}