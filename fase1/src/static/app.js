// ImaLink Fase 1 JavaScript

// API base URL
const API_BASE = '/api';

// Current images array
let currentImages = [];
let currentImportSession = null;

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadAllImages();
});

// Import functions
async function startImport() {
    const path = document.getElementById('importPath').value.trim();
    const description = document.getElementById('importDescription').value.trim() || 'Manual import';
    
    if (!path) {
        alert('Vennligst skriv inn en sti til bildekatalogen');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/import/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source_path: path,
                source_description: description
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Import failed');
        }
        
        const result = await response.json();
        currentImportSession = result.session_id;
        
        // Show import status section
        document.getElementById('importStatus').style.display = 'block';
        
        // Start polling for status
        pollImportStatus();
        
    } catch (error) {
        alert('Import feilet: ' + error.message);
    }
}

async function pollImportStatus() {
    if (!currentImportSession) return;
    
    try {
        const response = await fetch(`${API_BASE}/import/status/${currentImportSession}`);
        const status = await response.json();
        
        updateImportProgress(status);
        
        if (status.status === 'in_progress') {
            // Continue polling every 2 seconds
            setTimeout(pollImportStatus, 2000);
        } else {
            // Import finished
            currentImportSession = null;
            if (status.status === 'completed') {
                setTimeout(() => {
                    loadAllImages(); // Reload gallery
                }, 1000);
            }
        }
        
    } catch (error) {
        console.error('Error polling import status:', error);
    }
}

function updateImportProgress(status) {
    const progressContainer = document.getElementById('importProgress');
    
    const statusText = status.status === 'in_progress' ? 'Pågår...' : 
                      status.status === 'completed' ? 'Ferdig!' : 'Feilet';
    
    progressContainer.innerHTML = `
        <div><strong>Status:</strong> ${statusText}</div>
        <div><strong>Filer funnet:</strong> ${status.total_files_found}</div>
        <div><strong>Bilder importert:</strong> ${status.images_imported}</div>
        <div><strong>Duplikater hoppet over:</strong> ${status.duplicates_skipped}</div>
        <div><strong>Feil:</strong> ${status.errors_count}</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${status.progress_percentage}%"></div>
        </div>
        <div>Fremdrift: ${status.progress_percentage.toFixed(1)}%</div>
    `;
}

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
    
    gallery.innerHTML = currentImages.map(image => `
        <div class="gallery-item" onclick="showImageModal(${image.id})">
            <img src="${API_BASE}/images/${image.id}/thumbnail" 
                 alt="${image.filename}"
                 onerror="this.style.display='none'">
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
    `).join('');
}

// Modal functions
async function showImageModal(imageId) {
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