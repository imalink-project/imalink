// ImaLink Gallery JavaScript

// API base URL
const API_BASE = '/api';

// Current images array
let currentImages = [];

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadAllImages();
});

// Search and gallery functions
async function searchImages() {
    const query = document.getElementById('searchQuery').value.trim();
    const dateFrom = document.getElementById('searchDateFrom').value;
    const dateTo = document.getElementById('searchDateTo').value;
    
    let url = `${API_BASE}/images/search?limit=100`;
    
    if (query) url += `&q=${encodeURIComponent(query)}`;
    if (dateFrom) url += `&taken_after=${dateFrom}`;
    if (dateTo) url += `&taken_before=${dateTo}`;
    
    await loadImages(url);
}

async function loadAllImages() {
    await loadImages(`${API_BASE}/images/?limit=100`);
}

async function loadImages(url) {
    const gallery = document.getElementById('gallery');
    const loading = document.getElementById('loadingIndicator');
    const imageCount = document.getElementById('imageCount');
    
    // Show loading
    loading.style.display = 'block';
    gallery.innerHTML = '';
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Failed to load images');
        }
        
        const images = await response.json();
        currentImages = Array.isArray(images) ? images : images.images || [];
        
        // Update image count
        imageCount.textContent = `Viser ${currentImages.length} bilder`;
        
        // Hide loading
        loading.style.display = 'none';
        
        if (currentImages.length === 0) {
            gallery.innerHTML = '<div class="loading">Ingen bilder funnet</div>';
            return;
        }
        
        // Render gallery
        renderGallery();
        
    } catch (error) {
        loading.style.display = 'none';
        gallery.innerHTML = '<div class="loading">Feil ved lasting av bilder: ' + error.message + '</div>';
    }
}

function renderGallery() {
    const gallery = document.getElementById('gallery');
    
    gallery.innerHTML = currentImages.map(image => {
        const rotationDegrees = (image.user_rotation || 0) * 90;
        return `
        <div class="gallery-item">
            <div class="thumbnail-container">
                <img src="${API_BASE}/images/${image.id}/thumbnail" 
                     alt="${image.filename}"
                     onclick="showImageModal(${image.id})"
                     style="transform: rotate(${rotationDegrees}deg);"
                     onerror="this.style.display='none'">
                <div class="thumbnail-controls">
                    <button class="rotate-thumbnail-btn" onclick="event.stopPropagation(); rotateThumbnail(${image.id})" title="Roter 90°">
                        🔄
                    </button>
                </div>
            </div>
            <div class="image-info">
                <div class="image-filename" title="${image.filename}">
                    ${image.filename}
                </div>
                <div class="image-meta">
                    <div class="image-date">
                        ${formatDate(image.taken_at || image.created_at)}
                    </div>
                    <div class="image-size">
                        ${image.width} × ${image.height}
                        ${image.has_gps ? '📍' : ''}
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

// Modal functions
// This function is redefined below with rotation support

function renderImageModal(imageData) {
    const container = document.getElementById('modalImageContainer');
    
    container.innerHTML = `
        <div class="modal-image-container">
            <img src="${API_BASE}/images/${imageData.id}/thumbnail" alt="${imageData.filename}">
            <h3>${imageData.filename}</h3>
            <div class="modal-metadata">
                ${Object.entries({
                    'Filsti': imageData.file_path,
                    'Størrelse': `${imageData.width} × ${imageData.height}`,
                    'Filstørrelse': formatFileSize(imageData.file_size),
                    'Format': imageData.format?.toUpperCase(),
                    'Tatt': formatDate(imageData.taken_at),
                    'Importert': formatDate(imageData.created_at),
                    'GPS': imageData.gps_latitude && imageData.gps_longitude ? 
                           `${imageData.gps_latitude.toFixed(6)}, ${imageData.gps_longitude.toFixed(6)}` : 'Nei',
                    'Kilde': imageData.import_source,
                    'Hash': imageData.hash
                }).map(([label, value]) => 
                    value ? `
                    <div class="metadata-item">
                        <span class="metadata-label">${label}:</span>
                        <span class="metadata-value">${value}</span>
                    </div>
                    ` : ''
                ).join('')}
            </div>
        </div>
    `;
}

function closeModal() {
    document.getElementById('imageModal').style.display = 'none';
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'Ukjent';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('no-NO', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return 'Ugyldig dato';
    }
}

function formatFileSize(bytes) {
    if (!bytes) return 'Ukjent';
    
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('imageModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Handle ESC key for modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Current image ID for rotation
let currentImageId = null;

// Show image modal with rotation support
async function showImageModal(imageId) {
    currentImageId = imageId;  // Store for rotation
    const modal = document.getElementById('imageModal');
    const container = document.getElementById('modalImageContainer');
    
    // Show modal with loading
    container.innerHTML = '<div class="loading">Laster bildedetaljer...</div>';
    modal.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/images/${imageId}`);
        const imageData = await response.json();
        
        renderImageModal(imageData);
        
    } catch (error) {
        container.innerHTML = `<div class="loading">Feil ved lasting: ${error.message}</div>`;
    }
}

// Rotate current image (from modal)
async function rotateImage() {
    if (!currentImageId) return;
    
    const rotateBtn = document.querySelector('.rotate-btn');
    const originalText = rotateBtn.textContent;
    
    try {
        // Show loading state
        rotateBtn.textContent = '🔄 Roterer...';
        rotateBtn.disabled = true;
        
        const response = await fetch(`${API_BASE}/images/${currentImageId}/rotate`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Rotasjon feilet');
        }
        
        const result = await response.json();
        
        // Reload the modal to show rotated thumbnail
        await showImageModal(currentImageId);
        
        // Also reload the gallery to update the thumbnail there
        await loadAllImages();
        
    } catch (error) {
        alert(`Feil ved rotasjon: ${error.message}`);
    } finally {
        rotateBtn.textContent = originalText;
        rotateBtn.disabled = false;
    }
}

// Rotate thumbnail directly in gallery
async function rotateThumbnail(imageId) {
    const rotateBtn = event.target;
    const originalText = rotateBtn.textContent;
    
    try {
        // Show loading state
        rotateBtn.textContent = '⏳';
        rotateBtn.disabled = true;
        
        const response = await fetch(`${API_BASE}/images/${imageId}/rotate`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Rotasjon feilet');
        }
        
        const result = await response.json();
        
        // Find the thumbnail image and apply CSS rotation immediately
        const thumbnailImg = rotateBtn.closest('.gallery-item').querySelector('img');
        const newRotation = (result.user_rotation || 0) * 90;
        thumbnailImg.style.transform = `rotate(${newRotation}deg)`;
        
        // Update the current images array for consistency
        const imageIndex = currentImages.findIndex(img => img.id === imageId);
        if (imageIndex !== -1) {
            currentImages[imageIndex].user_rotation = result.user_rotation;
        }
        
        // Brief success feedback
        rotateBtn.textContent = '✅';
        setTimeout(() => {
            rotateBtn.textContent = originalText;
        }, 500);
        
    } catch (error) {
        alert(`Feil ved rotasjon: ${error.message}`);
        rotateBtn.textContent = '❌';
        setTimeout(() => {
            rotateBtn.textContent = originalText;
        }, 1000);
    } finally {
        rotateBtn.disabled = false;
    }
}