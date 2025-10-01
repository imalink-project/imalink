// ImaLink Gallery JavaScript

// API base URL
const API_BASE = '/api';

// Current images array
let currentImages = [];

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadAllImages();
});

// Test function to verify modal functionality (temporary)
function testModal() {
    console.log('Testing modal...');
    const modal = document.getElementById('imageModal');
    if (modal) {
        console.log('Modal found, showing...');
        modal.classList.remove('hidden');
        
        // Add some test content
        document.getElementById('viewerTitle').textContent = 'Test Modal';
        document.getElementById('viewerImageContainer').innerHTML = '<div style="padding: 2rem; text-align: center;">Modal fungerer! 🎉</div>';
    } else {
        console.error('Modal element not found!');
        alert('Modal element not found in HTML!');
    }
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
    
    gallery.innerHTML = currentImages.map(image => {
        const rotationDegrees = (image.user_rotation || 0) * 90;
        return `
        <div class="gallery-item">
            <div class="thumbnail-container">
                <img src="${API_BASE}/images/${image.id}/thumbnail" 
                     alt="${image.filename}"
                     title="Klikk for å åpne bildeviewer - ${image.filename}"
                     onclick="console.log('Image clicked:', ${image.id}); showImageModal(${image.id});"
                     style="transform: rotate(${rotationDegrees}deg); cursor: pointer;"
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

// Enhanced modal functions

// Load image with specific pool size
async function loadImageWithPoolSize(poolSize, imageData) {
    currentImageData = imageData;
    const container = document.getElementById('viewerImageContainer');
    const sizeSelector = document.getElementById('poolSizeSelector');
    
    // Update size selector
    sizeSelector.value = poolSize;
    
    try {
        // Try pool image URL directly - backend will create if needed
        let imageUrl = `${API_BASE}/images/${imageData.id}/pool/${poolSize}`;
        
        console.log(`Loading pool image for size '${poolSize}': ${imageUrl}`);
        
        // Create and load image
        const img = document.createElement('img');
        img.className = 'viewer-image';
        img.alt = imageData.filename;
        
        // Apply user rotation if any
        if (imageData.user_rotation) {
            const rotation = imageData.user_rotation * 90;
            img.style.transform = `rotate(${rotation}deg)`;
        }
        
        img.onload = () => {
            console.log(`Successfully loaded ${poolSize} image for ${imageData.filename}`);
            console.log(`Image dimensions: ${img.naturalWidth} x ${img.naturalHeight}`);
            container.innerHTML = '';
            container.appendChild(img);
            
            // Add debugging info overlay (remove in production)
            const debugInfo = document.createElement('div');
            debugInfo.style.cssText = `
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10;
                pointer-events: none;
            `;
            debugInfo.textContent = `${poolSize.toUpperCase()}: ${img.naturalWidth}×${img.naturalHeight}`;
            container.appendChild(debugInfo);
            
            // Add usage hint for large images
            if (img.naturalWidth > 800 || img.naturalHeight > 600) {
                const hintInfo = document.createElement('div');
                hintInfo.style.cssText = `
                    position: absolute;
                    bottom: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 11px;
                    z-index: 10;
                    pointer-events: none;
                    opacity: 0.8;
                `;
                hintInfo.textContent = '💡 Dra bildet for å navigere • Scroll for å zoome';
                container.appendChild(hintInfo);
                
                // Fade out hint after 3 seconds
                setTimeout(() => {
                    if (hintInfo.parentNode) {
                        hintInfo.style.transition = 'opacity 1s ease';
                        hintInfo.style.opacity = '0';
                        setTimeout(() => {
                            if (hintInfo.parentNode) hintInfo.remove();
                        }, 1000);
                    }
                }, 3000);
            }
            
            // Add drag scrolling functionality for large images
            setupImageDragging(img, container);
            
            // Show image dimensions in console for debugging
            img.onload = null; // Remove handler to avoid recursive calls
        };
        
        img.onerror = (error) => {
            console.error(`Failed to load ${poolSize} image:`, error);
            console.log(`Falling back to thumbnail for ${imageData.filename}`);
            
            // Fallback to thumbnail
            const fallbackImg = document.createElement('img');
            fallbackImg.className = 'viewer-image';
            fallbackImg.alt = imageData.filename;
            fallbackImg.src = `${API_BASE}/images/${imageData.id}/thumbnail`;
            
            fallbackImg.onload = () => {
                container.innerHTML = '';
                container.appendChild(fallbackImg);
            };
            
            fallbackImg.onerror = () => {
                container.innerHTML = `
                    <div class="error-message">
                        <strong>Kunne ikke laste bilde</strong><br>
                        Pool størrelse: ${poolSize}<br>
                        Thumbnail fallback feilet også
                    </div>
                `;
            };
        };
        
        img.src = imageUrl;
        
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                <strong>Feil ved lasting av pool-bilde</strong><br>
                ${error.message}
            </div>
        `;
    }
}

// Populate image information panels
function populateImageInfo(imageData) {
    // File Info panel
    const fileInfo = document.getElementById('imageFileInfo');
    fileInfo.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Filnavn</span>
            <span class="detail-value highlight">${imageData.filename || 'Ukjent'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Filsti</span>
            <span class="detail-value">${imageData.file_path || 'Ukjent'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Filstørrelse</span>
            <span class="detail-value">${formatFileSize(imageData.file_size)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Hash</span>
            <span class="detail-value muted">${imageData.hash || 'Ukjent'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Importert</span>
            <span class="detail-value">${formatDate(imageData.created_at)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Kilde</span>
            <span class="detail-value">${imageData.import_source || 'Ukjent'}</span>
        </div>
    `;
    
    // Technical Details panel with pool size explanation
    const technicalInfo = document.getElementById('imageTechnicalInfo');
    const originalWidth = imageData.width || 0;
    const originalHeight = imageData.height || 0;
    
    // Calculate effective pool sizes
    const getEffectiveSize = (maxW, maxH) => {
        if (originalWidth <= maxW && originalHeight <= maxH) {
            return `${originalWidth}×${originalHeight} (original)`;
        }
        const aspect = originalWidth / originalHeight;
        let newW, newH;
        if (aspect > 1) {
            newW = Math.min(maxW, originalWidth);
            newH = Math.round(newW / aspect);
        } else {
            newH = Math.min(maxH, originalHeight);
            newW = Math.round(newH * aspect);
        }
        return `${newW}×${newH}`;
    };
    
    technicalInfo.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Format</span>
            <span class="detail-value highlight">${(imageData.format || 'Ukjent').toUpperCase()}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Original størrelse</span>
            <span class="detail-value">${originalWidth} × ${originalHeight}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Pool: Small</span>
            <span class="detail-value muted">${getEffectiveSize(400, 400)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Pool: Medium</span>
            <span class="detail-value muted">${getEffectiveSize(800, 800)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Pool: Large</span>
            <span class="detail-value muted">${getEffectiveSize(1200, 1200)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Rotasjon (bruker)</span>
            <span class="detail-value">${imageData.user_rotation ? imageData.user_rotation * 90 + '°' : '0°'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">EXIF rotasjon</span>
            <span class="detail-value">${imageData.exif_rotation || 'Ingen'}</span>
        </div>
    `;
    
    // Metadata panel
    const metadataInfo = document.getElementById('imageMetadataInfo');
    metadataInfo.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Tatt dato</span>
            <span class="detail-value">${formatDate(imageData.taken_at)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Kamera</span>
            <span class="detail-value">${imageData.camera_make ? `${imageData.camera_make} ${imageData.camera_model || ''}`.trim() : 'Ukjent'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">GPS posisjon</span>
            <span class="detail-value">${imageData.gps_latitude && imageData.gps_longitude ? 
                `${imageData.gps_latitude.toFixed(6)}, ${imageData.gps_longitude.toFixed(6)}` : 'Ikke tilgjengelig'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Fotograf</span>
            <span class="detail-value">${imageData.photographer || 'Ukjent'}</span>
        </div>
    `;
}

function closeModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.classList.add('hidden');
    }
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

// Setup drag scrolling for large images
function setupImageDragging(img, container) {
    let isMouseDown = false;
    let startX, startY, scrollLeft, scrollTop;
    
    // Mouse events for desktop
    img.addEventListener('mousedown', (e) => {
        isMouseDown = true;
        img.style.cursor = 'grabbing';
        startX = e.pageX - container.offsetLeft;
        startY = e.pageY - container.offsetTop;
        scrollLeft = container.scrollLeft;
        scrollTop = container.scrollTop;
        e.preventDefault(); // Prevent image drag default behavior
    });
    
    container.addEventListener('mouseleave', () => {
        isMouseDown = false;
        img.style.cursor = 'grab';
    });
    
    container.addEventListener('mouseup', () => {
        isMouseDown = false;
        img.style.cursor = 'grab';
    });
    
    container.addEventListener('mousemove', (e) => {
        if (!isMouseDown) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const y = e.pageY - container.offsetTop;
        const walkX = (x - startX) * 1; // Scroll speed multiplier
        const walkY = (y - startY) * 1;
        container.scrollLeft = scrollLeft - walkX;
        container.scrollTop = scrollTop - walkY;
    });
    
    // Touch events for mobile
    img.addEventListener('touchstart', (e) => {
        isMouseDown = true;
        const touch = e.touches[0];
        startX = touch.pageX - container.offsetLeft;
        startY = touch.pageY - container.offsetTop;
        scrollLeft = container.scrollLeft;
        scrollTop = container.scrollTop;
    }, { passive: false });
    
    container.addEventListener('touchend', () => {
        isMouseDown = false;
    });
    
    container.addEventListener('touchmove', (e) => {
        if (!isMouseDown) return;
        e.preventDefault();
        const touch = e.touches[0];
        const x = touch.pageX - container.offsetLeft;
        const y = touch.pageY - container.offsetTop;
        const walkX = (x - startX) * 1;
        const walkY = (y - startY) * 1;
        container.scrollLeft = scrollLeft - walkX;
        container.scrollTop = scrollTop - walkY;
    }, { passive: false });
}

// Enhanced modal event handlers
function onPoolSizeChange() {
    const sizeSelector = document.getElementById('poolSizeSelector');
    const selectedSize = sizeSelector.value;
    
    if (currentImageData) {
        loadImageWithPoolSize(selectedSize, currentImageData);
        
        // Update dropdown options with actual sizes if available
        updateDropdownLabels();
    }
}

function updateDropdownLabels() {
    if (!currentImageData) return;
    
    const sizeSelector = document.getElementById('poolSizeSelector');
    const originalWidth = currentImageData.width || 0;
    const originalHeight = currentImageData.height || 0;
    
    // Calculate effective sizes
    const getEffectiveSize = (maxW, maxH) => {
        if (originalWidth <= maxW && originalHeight <= maxH) {
            return { width: originalWidth, height: originalHeight, isOriginal: true };
        }
        const aspect = originalWidth / originalHeight;
        let newW, newH;
        if (aspect > 1) {
            newW = Math.min(maxW, originalWidth);
            newH = Math.round(newW / aspect);
        } else {
            newH = Math.min(maxH, originalHeight);
            newW = Math.round(newH * aspect);
        }
        return { width: newW, height: newH, isOriginal: false };
    };
    
    const small = getEffectiveSize(400, 400);
    const medium = getEffectiveSize(800, 800);
    const large = getEffectiveSize(1200, 1200);
    
    // Update option texts
    const options = sizeSelector.querySelectorAll('option');
    if (options[0]) options[0].textContent = `Liten (${small.width}×${small.height})`;
    if (options[1]) options[1].textContent = `Medium (${medium.width}×${medium.height})`;
    if (options[2]) {
        const largeText = `Stor (${large.width}×${large.height})`;
        const sameAsMedium = large.width === medium.width && large.height === medium.height;
        options[2].textContent = sameAsMedium ? `${largeText} - samme som medium` : largeText;
    }
}

// Enhanced rotate function for modal
async function rotateViewerImage() {
    if (!currentImageId) return;
    
    const rotateBtn = document.getElementById('viewerRotateBtn');
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
        
        // Update current image data with new rotation
        if (currentImageData) {
            currentImageData.user_rotation = result.user_rotation;
        }
        
        // Reload the modal image with current pool size
        const currentPoolSize = document.getElementById('poolSizeSelector').value;
        await loadImageWithPoolSize(currentPoolSize, currentImageData);
        
        // Update technical info panel
        populateImageInfo(currentImageData);
        
        // Reload gallery to update thumbnail
        await loadAllImages();
        
    } catch (error) {
        alert(`Feil ved rotasjon: ${error.message}`);
    } finally {
        rotateBtn.textContent = originalText;
        rotateBtn.disabled = false;
    }
}

// Download current pool image
async function downloadViewerImage() {
    if (!currentImageId) return;
    
    const downloadBtn = document.getElementById('viewerDownloadBtn');
    const poolSize = document.getElementById('poolSizeSelector').value;
    const originalText = downloadBtn.textContent;
    
    try {
        downloadBtn.textContent = '📥 Laster ned...';
        downloadBtn.disabled = true;
        
        // Try pool image first, fallback to thumbnail
        let downloadUrl = `${API_BASE}/images/${currentImageId}/pool/${poolSize}`;
        
        // Check if pool image exists
        const checkResponse = await fetch(downloadUrl, { method: 'HEAD' });
        if (!checkResponse.ok) {
            downloadUrl = `${API_BASE}/images/${currentImageId}/thumbnail`;
        }
        
        // Create download link
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = currentImageData ? `${currentImageData.filename}_${poolSize}` : `image_${currentImageId}_${poolSize}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (error) {
        alert(`Feil ved nedlasting: ${error.message}`);
    } finally {
        downloadBtn.textContent = originalText;
        downloadBtn.disabled = false;
    }
}

// Close modal when clicking outside
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

// Current image ID and data for modal operations
let currentImageId = null;
let currentImageData = null;

// Show enhanced image modal with pool support
async function showImageModal(imageId) {
    console.log('Opening image modal for image ID:', imageId);
    
    currentImageId = imageId;  // Store for rotation and operations
    const modal = document.getElementById('imageModal');
    const imageContainer = document.getElementById('viewerImageContainer');
    const spinner = document.getElementById('imageLoadingSpinner');
    const errorDiv = document.getElementById('imageError');
    
    // Check if elements exist
    if (!modal) {
        console.error('Modal element not found!');
        alert('Feil: Modal-element ikke funnet. Sjekk HTML-strukturen.');
        return;
    }
    
    if (!imageContainer) {
        console.error('Image container element not found!');
        alert('Feil: Bildebeholder ikke funnet. Sjekk HTML-strukturen.');
        return;
    }
    
    // Reset states
    imageContainer.innerHTML = '';
    if (spinner) spinner.classList.remove('hidden');
    if (errorDiv) errorDiv.classList.add('hidden');
    modal.classList.remove('hidden');
    
    try {
        // Load image metadata
        const response = await fetch(`${API_BASE}/images/${imageId}`);
        if (!response.ok) throw new Error('Kunne ikke laste bildedata');
        
        const imageData = await response.json();
        
        // Update modal title
        document.getElementById('viewerTitle').textContent = imageData.filename || 'Ukjent fil';
        
        // Load image with default pool size
        await loadImageWithPoolSize('medium', imageData);
        
        // Populate file information
        populateImageInfo(imageData);
        
        // Update dropdown labels with actual sizes
        updateDropdownLabels();
        
        if (spinner) spinner.classList.add('hidden');
        
    } catch (error) {
        console.error('Error loading image:', error);
        if (spinner) spinner.classList.add('hidden');
        if (errorDiv) {
            errorDiv.classList.remove('hidden');
            errorDiv.innerHTML = `
                <div class="error-message">
                    <strong>Feil ved lasting av bilde</strong><br>
                    ${error.message}
                </div>
            `;
        }
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