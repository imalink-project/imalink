// ImaLink API integration
const API_BASE = 'http://localhost:8000/api/v1';

/**
 * Wrapper for fetch requests with error handling
 */
async function apiRequest(endpoint, options = {}) {
    try {
        // Set default headers, but allow override (needed for FormData)
        const defaultHeaders = options.body instanceof FormData ? {} : {
            'Content-Type': 'application/json'
        };
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                ...defaultHeaders,
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API request failed for ${endpoint}:`, error);
        throw error;
    }
}

/**
 * Health check for backend
 */
export async function healthCheck() {
    // Health endpoint is not under /api/v1, so use full path
    const response = await fetch('http://localhost:8000/health');
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Get all images
 */
export async function getImages() {
    const response = await apiRequest('/images/');
    return response.data || response; // Handle both {data: []} and [] formats
}

/**
 * Get image by ID
 */
export async function getImage(imageId) {
    return apiRequest(`/images/${imageId}`);
}

/**
 * Get all authors
 */
export async function getAuthors() {
    const response = await apiRequest('/authors/');
    return response.data || response; // Handle both {data: []} and [] formats
}

/**
 * Get author by ID with their images
 */
export async function getAuthor(authorId) {
    return apiRequest(`/authors/${authorId}`);
}

/**
 * Get all import sessions
 */
export async function getImportSessions() {
    const response = await apiRequest('/import_sessions/');
    return response.imports || response.data || response; // Handle different response formats
}

/**
 * Get import session by ID
 */
export async function getImportSession(sessionId) {
    return apiRequest(`/import_sessions/${sessionId}`);
}

/**
 * Create new import session
 */
export async function createImportSession(sourcePath) {
    return apiRequest('/import_sessions/', {
        method: 'POST',
        body: JSON.stringify({ source_path: sourcePath })
    });
}

/**
 * Get thumbnail URL for an image
 */
export function getThumbnailUrl(imageId) {
    return `http://localhost:8000/api/v1/images/${imageId}/hotpreview`;
}

/**
 * Get full image URL
 */
export function getImageUrl(imageId) {
    return `http://localhost:8000/api/v1/images/${imageId}/pool/large`;
}

/**
 * Search images
 */
export async function searchImages(query, offset = 0, limit = 100) {
    return apiRequest(`/images/search?query=${encodeURIComponent(query)}&offset=${offset}&limit=${limit}`);
}

/**
 * Get image statistics overview
 */
export async function getImageStatistics() {
    return apiRequest('/images/statistics/overview');
}

/**
 * Get recent images
 */
export async function getRecentImages(limit = 10) {
    return apiRequest(`/images/recent?limit=${limit}`);
}

/**
 * Rotate image
 */
export async function rotateImage(imageId, degrees) {
    return apiRequest(`/images/${imageId}/rotate`, {
        method: 'POST',
        body: JSON.stringify({ degrees })
    });
}

/**
 * Update image metadata
 */
export async function updateImage(imageId, updateData) {
    return apiRequest(`/images/${imageId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData)
    });
}

/**
 * Delete image
 */
export async function deleteImage(imageId) {
    return apiRequest(`/images/${imageId}`, {
        method: 'DELETE'
    });
}

/**
 * Get author by ID with their images
 */
export async function getAuthor(authorId) {
    return apiRequest(`/authors/${authorId}`);
}

/**
 * Update author
 */
export async function updateAuthor(authorId, updateData) {
    return apiRequest(`/authors/${authorId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData)
    });
}

/**
 * Delete author
 */
export async function deleteAuthor(authorId) {
    return apiRequest(`/authors/${authorId}`, {
        method: 'DELETE'
    });
}

/**
 * Search authors
 */
export async function searchAuthors(query) {
    return apiRequest(`/authors/search/?query=${encodeURIComponent(query)}`);
}

/**
 * Get import session status by ID
 */
export async function getImportSessionStatus(sessionId) {
    return apiRequest(`/import_sessions/status/${sessionId}`);
}

/**
 * Get images by author ID
 */
export async function getImagesByAuthor(authorId) {
    return apiRequest(`/images/author/${authorId}`);
}

/**
 * Create new author
 */
export async function createAuthor(authorData) {
    return apiRequest('/authors/', {
        method: 'POST',
        body: JSON.stringify(authorData)
    });
}

/**
 * Get author statistics
 */
export async function getAuthorStatistics() {
    return apiRequest('/authors/statistics/');
}

/**
 * Get authors with their images
 */
export async function getAuthorsWithImages() {
    return apiRequest('/authors/with-images/');
}

/**
 * Start import session (alternative endpoint)
 */
export async function startImportSession(sourcePath) {
    return apiRequest('/import_sessions/start', {
        method: 'POST',
        body: JSON.stringify({ source_path: sourcePath })
    });
}

/**
 * Test single image import
 */
export async function testSingleImage(imagePath) {
    return apiRequest('/import_sessions/test-single', {
        method: 'POST',
        body: JSON.stringify({ image_path: imagePath })
    });
}

/**
 * Get storage information
 */
export async function getStorageInfo() {
    return apiRequest('/import_sessions/storage-info');
}

/**
 * Test import endpoint
 */
export async function testImportEndpoint() {
    return apiRequest('/import_sessions/test');
}

/**
 * Create new image (file upload)
 * Note: This will require FormData for file uploads
 */
export async function createImage(imageFile, metadata = {}) {
    const formData = new FormData();
    formData.append('file', imageFile);
    
    // Add metadata fields
    Object.keys(metadata).forEach(key => {
        formData.append(key, metadata[key]);
    });
    
    return apiRequest('/images/', {
        method: 'POST',
        headers: {}, // Remove Content-Type to let browser set it for FormData
        body: formData
    });
}