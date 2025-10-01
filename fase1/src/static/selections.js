// ImaLink Selections JavaScript

// API base URL
const API_BASE = '/api';

// Current selections array
let currentSelections = [];
let algorithmicPreviews = [];

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSelections();
});

// Initialize selections page
async function initializeSelections() {
    await loadSelections();
    await loadAuthors();
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    // Algorithm radio buttons
    document.querySelectorAll('input[name="algorithmType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            updateAlgorithmParams(this.value);
        });
    });

    // Parent selection change
    document.getElementById('parentSelection').addEventListener('change', function() {
        updateCascadePreview(this.value);
    });

    // Form submission
    document.getElementById('selectionForm').addEventListener('submit', handleSelectionSubmit);
}

// Load all selections
async function loadSelections() {
    try {
        const showFavorites = document.getElementById('showFavorites')?.checked || false;
        const showAlgorithmic = document.getElementById('showAlgorithmic')?.checked || true;
        
        let url = `${API_BASE}/selections/?include_algorithmic=${showAlgorithmic}`;
        if (showFavorites) {
            url += '&favorites_only=true';
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load selections');
        
        currentSelections = await response.json();
        displaySelections(currentSelections);
    } catch (error) {
        console.error('Error loading selections:', error);
        showError('Kunne ikke laste selections. Prøv igjen.');
    }
}

// Display selections in grid
function displaySelections(selections) {
    const grid = document.getElementById('selectionsGrid');
    
    if (!selections || selections.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📁</div>
                <h3>Ingen selections funnet</h3>
                <p>Opprett din første selection for å organisere bildene dine.</p>
                <button class="btn btn-primary" onclick="showCreateSelectionModal()">
                    ➕ Opprett Selection
                </button>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = selections.map(selection => `
        <div class="selection-card ${selection.parent_selection_id ? 'cascaded' : ''}" data-id="${selection.id}">
            <div class="selection-header">
                <div class="selection-icon" style="color: ${selection.color || '#3498db'}">
                    ${selection.icon || '📁'}
                </div>
                <div class="selection-info">
                    <h3 class="selection-name">${escapeHtml(selection.name)}</h3>
                    <p class="selection-type">${getSelectionTypeLabel(selection.is_algorithmic)}</p>
                </div>
                <div class="selection-actions">
                    ${selection.is_favorite ? '<span class="favorite-star">⭐</span>' : ''}
                    <button class="btn-icon" onclick="showSelectionMenu(${selection.id})" title="Mer">⋮</button>
                </div>
            </div>
            
            ${selection.description ? `<p class="selection-description">${escapeHtml(selection.description)}</p>` : ''}
            
            ${selection.parent_selection_id ? `
                <div class="cascade-indicator">
                    <span class="chain-icon">⛓️</span>
                    <span>Baserer seg på selection #${selection.parent_selection_id}</span>
                </div>
            ` : ''}
            
            <div class="selection-stats">
                <div class="stat">
                    <span class="stat-icon">📊</span>
                    <span class="stat-value" id="count-${selection.id}">-</span>
                    <span class="stat-label">bilder</span>
                </div>
                <div class="stat">
                    <span class="stat-icon">👁️</span>
                    <span class="stat-value">${selection.access_count || 0}</span>
                    <span class="stat-label">visninger</span>
                </div>
                <div class="stat">
                    <span class="stat-icon">🕒</span>
                    <span class="stat-value">${formatDate(selection.updated_at)}</span>
                    <span class="stat-label">oppdatert</span>
                </div>
            </div>
            
            <div class="selection-footer">
                <button class="btn btn-primary" onclick="executeSelection(${selection.id})">
                    🚀 Vis bilder
                </button>
                <button class="btn btn-secondary" onclick="editSelection(${selection.id})">
                    ✏️ Rediger
                </button>
            </div>
        </div>
    `).join('');
    
    // Load image counts for each selection
    selections.forEach(selection => {
        loadSelectionCount(selection.id);
    });
}

// Load image count for a selection
async function loadSelectionCount(selectionId) {
    try {
        const response = await fetch(`${API_BASE}/selections/${selectionId}/execute?page=1&page_size=1`, {
            method: 'POST'
        });
        if (response.ok) {
            const result = await response.json();
            const countElement = document.getElementById(`count-${selectionId}`);
            if (countElement) {
                countElement.textContent = result.total_count.toLocaleString();
            }
        }
    } catch (error) {
        console.error('Error loading selection count:', error);
    }
}

// Execute a selection and show results
async function executeSelection(selectionId) {
    try {
        showLoading('Utfører selection...');
        
        const response = await fetch(`${API_BASE}/selections/${selectionId}/execute?page=1&page_size=50`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to execute selection');
        
        const result = await response.json();
        displaySelectionResults(result);
        hideLoading();
    } catch (error) {
        console.error('Error executing selection:', error);
        showError('Kunne ikke utføre selection. Prøv igjen.');
        hideLoading();
    }
}

// Display selection results
function displaySelectionResults(result) {
    const resultsContainer = document.getElementById('selectionResults');
    const titleElement = document.getElementById('resultsTitle');
    const countElement = document.getElementById('resultsCount');
    const timeElement = document.getElementById('executionTime');
    const gridElement = document.getElementById('resultsGrid');
    
    titleElement.textContent = `${result.selection_name} - Resultater`;
    countElement.textContent = `${result.total_count.toLocaleString()} bilder`;
    timeElement.textContent = `${Math.round(result.execution_time_ms)}ms`;
    
    // Display images
    if (result.images && result.images.length > 0) {
        gridElement.innerHTML = result.images.map(image => `
            <div class="image-card" onclick="showImageModal('${image.image_hash}', '${escapeHtml(image.original_filename)}')">
                <div class="image-thumbnail">
                    <img src="/api/images/${image.image_hash}/thumbnail?size=medium" 
                         alt="${escapeHtml(image.original_filename)}"
                         loading="lazy"
                         onerror="this.src='/static/placeholder.jpg'">
                    ${image.rating ? `<div class="image-rating">${'⭐'.repeat(image.rating)}</div>` : ''}
                </div>
                <div class="image-info">
                    <div class="image-filename">${escapeHtml(image.original_filename)}</div>
                    <div class="image-meta">
                        ${image.taken_at ? formatDate(image.taken_at) : 'Ukjent dato'}
                        ${image.width && image.height ? ` • ${image.width}×${image.height}` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        gridElement.innerHTML = `
            <div class="empty-results">
                <p>Ingen bilder funnet for denne selectionen.</p>
            </div>
        `;
    }
    
    // Setup pagination if needed
    setupPagination(result);
    
    // Show results
    resultsContainer.style.display = 'block';
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

// Setup pagination controls
function setupPagination(result) {
    const paginationContainer = document.getElementById('paginationControls');
    
    if (result.total_count <= result.page_size) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    const totalPages = Math.ceil(result.total_count / result.page_size);
    const currentPage = result.page;
    
    let paginationHtml = '<div class="pagination">';
    
    // Previous button
    if (currentPage > 1) {
        paginationHtml += `<button class="btn btn-secondary" onclick="loadSelectionPage(${result.selection_id}, ${currentPage - 1})">« Forrige</button>`;
    }
    
    // Page numbers
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        if (i === currentPage) {
            paginationHtml += `<button class="btn btn-primary current">${i}</button>`;
        } else {
            paginationHtml += `<button class="btn btn-secondary" onclick="loadSelectionPage(${result.selection_id}, ${i})">${i}</button>`;
        }
    }
    
    // Next button
    if (currentPage < totalPages) {
        paginationHtml += `<button class="btn btn-secondary" onclick="loadSelectionPage(${result.selection_id}, ${currentPage + 1})">Neste »</button>`;
    }
    
    paginationHtml += '</div>';
    paginationContainer.innerHTML = paginationHtml;
}

// Load a specific page of selection results
async function loadSelectionPage(selectionId, page) {
    try {
        showLoading('Laster side...');
        
        const response = await fetch(`${API_BASE}/selections/${selectionId}/execute?page=${page}&page_size=50`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to load page');
        
        const result = await response.json();
        displaySelectionResults(result);
        hideLoading();
    } catch (error) {
        console.error('Error loading page:', error);
        showError('Kunne ikke laste siden. Prøv igjen.');
        hideLoading();
    }
}

// Close selection results
function closeSelectionResults() {
    document.getElementById('selectionResults').style.display = 'none';
}

// === CASCADING FUNCTIONS ===

// Load available parent selections
async function loadParentSelections(excludeId = null) {
    try {
        let url = `${API_BASE}/selections/available-parents`;
        if (excludeId) {
            url += `?exclude_id=${excludeId}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load parent selections');
        
        const parents = await response.json();
        const select = document.getElementById('parentSelection');
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">Ingen - start fra alle bilder</option>';
        
        parents.forEach(parent => {
            const option = document.createElement('option');
            option.value = parent.id;
            option.textContent = `${parent.name} (${getSelectionTypeLabel(parent.is_algorithmic)})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading parent selections:', error);
        showError('Kunne ikke laste parent selections.');
    }
}

// Update cascade preview when parent selection changes
async function updateCascadePreview(parentId) {
    const previewContainer = document.getElementById('cascadePreview');
    const chainElement = document.getElementById('cascadeChain');
    
    if (!parentId) {
        previewContainer.style.display = 'none';
        return;
    }
    
    try {
        // Get hierarchy information for the parent
        const response = await fetch(`${API_BASE}/selections/${parentId}/hierarchy`);
        if (!response.ok) throw new Error('Failed to load hierarchy');
        
        const hierarchy = await response.json();
        
        // Build chain display
        const chainNames = hierarchy.hierarchy_chain.map(item => 
            `${item.name} (${getSelectionTypeLabel(item.selection_type)})`
        );
        chainNames.push('→ Din nye selection');
        
        chainElement.textContent = chainNames.join(' → ');
        previewContainer.style.display = 'block';
    } catch (error) {
        console.error('Error updating cascade preview:', error);
        chainElement.textContent = 'Kunne ikke laste forhåndsvisning';
        previewContainer.style.display = 'block';
    }
}

// Show create selection modal
async function showCreateSelectionModal() {
    resetSelectionForm();
    document.getElementById('modalTitle').textContent = 'Ny Selection';
    await loadParentSelections();
    document.getElementById('selectionModal').style.display = 'flex';
}

// Show edit selection modal
async function editSelection(selectionId) {
    try {
        const response = await fetch(`${API_BASE}/selections/${selectionId}`);
        if (!response.ok) throw new Error('Failed to load selection');
        
        const selection = await response.json();
        
        // Load parent selections, excluding current selection to prevent circular references
        await loadParentSelections(selectionId);
        
        populateSelectionForm(selection);
        document.getElementById('modalTitle').textContent = 'Rediger Selection';
        document.getElementById('selectionModal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading selection for editing:', error);
        showError('Kunne ikke laste selection for redigering.');
    }
}

// Close selection modal
function closeSelectionModal() {
    document.getElementById('selectionModal').style.display = 'none';
    resetSelectionForm();
}

// Toggle algorithmic mode
function toggleAlgorithmicMode() {
    const isAlgorithmic = document.getElementById('isAlgorithmic').checked;
    const searchCriteriaSection = document.getElementById('searchCriteriaSection');
    const algorithmicSection = document.getElementById('algorithmicSection');
    
    if (isAlgorithmic) {
        searchCriteriaSection.style.display = 'none';
        algorithmicSection.style.display = 'block';
    } else {
        searchCriteriaSection.style.display = 'block';
        algorithmicSection.style.display = 'none';
    }
}

// Update algorithm parameters based on selected type
function updateAlgorithmParams(algorithmType) {
    const paramsContainer = document.getElementById('algorithmParams');
    
    let paramsHtml = '';
    
    switch (algorithmType) {
        case 'recent':
            paramsHtml = `
                <div class="form-group">
                    <label for="recentDays">Antall dager tilbake</label>
                    <input type="number" id="recentDays" value="30" min="1" max="365">
                </div>
            `;
            break;
        case 'memories':
            paramsHtml = `
                <div class="form-group">
                    <label for="memoryDate">Dato for minner</label>
                    <input type="date" id="memoryDate" value="${new Date().toISOString().split('T')[0]}">
                </div>
            `;
            break;
        case 'top_rated':
            paramsHtml = `
                <div class="form-group">
                    <label for="minRatingAlgo">Minimum rating</label>
                    <select id="minRatingAlgo">
                        <option value="4">4+ stjerner</option>
                        <option value="5">5 stjerner</option>
                        <option value="3">3+ stjerner</option>
                    </select>
                </div>
            `;
            break;
    }
    
    paramsContainer.innerHTML = paramsHtml;
}

// Handle selection form submission
async function handleSelectionSubmit(e) {
    e.preventDefault();
    
    try {
        showLoading('Lagrer selection...');
        
        const formData = collectSelectionFormData();
        
        const response = await fetch(`${API_BASE}/selections/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create selection');
        }
        
        const newSelection = await response.json();
        
        closeSelectionModal();
        await loadSelections();
        showSuccess('Selection opprettet!');
        hideLoading();
        
    } catch (error) {
        console.error('Error creating selection:', error);
        showError('Kunne ikke lagre selection: ' + error.message);
        hideLoading();
    }
}

// Collect form data
function collectSelectionFormData() {
    const name = document.getElementById('selectionName').value.trim();
    const description = document.getElementById('selectionDescription').value.trim();
    const color = document.getElementById('selectionColor').value;
    const icon = document.getElementById('selectionIcon').value;
    const isFavorite = document.getElementById('isFavorite').checked;
    const isPublic = document.getElementById('isPublic').checked;
    const parentSelectionId = document.getElementById('parentSelection').value;
    const isAlgorithmic = document.getElementById('isAlgorithmic').checked;
    
    const formData = {
        name,
        description: description || null,
        color: color || null,
        icon: icon || null,
        is_algorithmic: isAlgorithmic,
        is_favorite: isFavorite,
        is_public: isPublic,
        sort_order: 0,
        parent_selection_id: parentSelectionId ? parseInt(parentSelectionId) : null
    };
    
    if (isAlgorithmic) {
        const algorithmType = document.querySelector('input[name="algorithmType"]:checked')?.value;
        if (algorithmType) {
            formData.algorithm_type = algorithmType;
            formData.algorithm_params = collectAlgorithmParams(algorithmType);
        }
    } else {
        // Collect search criteria and image IDs
        formData.search_criteria = collectSearchCriteria();
        
        // Handle manual image selection via image IDs
        const imageIds = document.getElementById('imageIds').value.trim();
        if (imageIds) {
            formData.search_criteria.image_ids = imageIds.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
        }
    }
    
    return formData;
}

// Collect search criteria from form
function collectSearchCriteria() {
    const criteria = {};
    
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const minRating = document.getElementById('minRating').value;
    const authorFilter = document.getElementById('authorFilter').value;
    
    if (dateFrom) criteria.date_from = dateFrom;
    if (dateTo) criteria.date_to = dateTo;
    if (minRating) criteria.min_rating = parseInt(minRating);
    if (authorFilter) criteria.author_id = parseInt(authorFilter);
    
    return criteria;
}

// Collect algorithm parameters
function collectAlgorithmParams(algorithmType) {
    const params = {};
    
    switch (algorithmType) {
        case 'recent':
            const days = document.getElementById('recentDays')?.value;
            if (days) params.days = parseInt(days);
            break;
        case 'memories':
            const date = document.getElementById('memoryDate')?.value;
            if (date) params.date = date;
            break;
        case 'top_rated':
            const minRating = document.getElementById('minRatingAlgo')?.value;
            if (minRating) params.min_rating = parseInt(minRating);
            break;
    }
    
    return params;
}

// Reset selection form
function resetSelectionForm() {
    document.getElementById('selectionForm').reset();
    document.getElementById('selectionColor').value = '#3498db';
    document.getElementById('isAlgorithmic').checked = false;
    toggleAlgorithmicMode();
    document.getElementById('algorithmParams').innerHTML = '';
    document.getElementById('cascadePreview').style.display = 'none';
}

// Populate form with existing selection data
function populateSelectionForm(selection) {
    document.getElementById('selectionName').value = selection.name || '';
    document.getElementById('selectionDescription').value = selection.description || '';
    document.getElementById('selectionColor').value = selection.color || '#3498db';
    document.getElementById('selectionIcon').value = selection.icon || '';
    document.getElementById('isFavorite').checked = selection.is_favorite || false;
    document.getElementById('isPublic').checked = selection.is_public || false;
    
    // Set parent selection if exists
    if (selection.parent_selection_id) {
        document.getElementById('parentSelection').value = selection.parent_selection_id;
        updateCascadePreview(selection.parent_selection_id);
    }
    
    // Set algorithmic mode
    document.getElementById('isAlgorithmic').checked = selection.is_algorithmic || false;
    toggleAlgorithmicMode();
    
    // Populate algorithmic fields if it's an algorithmic selection
    if (selection.is_algorithmic && selection.algorithm_type) {
        const radioButton = document.querySelector(`input[name="algorithmType"][value="${selection.algorithm_type}"]`);
        if (radioButton) {
            radioButton.checked = true;
            updateAlgorithmParams(selection.algorithm_type);
        }
    }
    
    // Populate search criteria if it's a criteria-based selection
    if (!selection.is_algorithmic && selection.search_criteria) {
        const criteria = selection.search_criteria;
        
        if (criteria.date_from) document.getElementById('dateFrom').value = criteria.date_from;
        if (criteria.date_to) document.getElementById('dateTo').value = criteria.date_to;
        if (criteria.min_rating) document.getElementById('minRating').value = criteria.min_rating;
        if (criteria.author_id) document.getElementById('authorFilter').value = criteria.author_id;
        if (criteria.image_ids) document.getElementById('imageIds').value = criteria.image_ids.join(', ');
    }
}

// Show algorithmic previews modal
async function showAlgorithmicPreviews() {
    try {
        showLoading('Laster forslag...');
        
        const response = await fetch(`${API_BASE}/selections/algorithmic/preview`);
        if (!response.ok) throw new Error('Failed to load previews');
        
        algorithmicPreviews = await response.json();
        displayAlgorithmicPreviews(algorithmicPreviews);
        
        document.getElementById('algorithmicModal').style.display = 'flex';
        hideLoading();
    } catch (error) {
        console.error('Error loading algorithmic previews:', error);
        showError('Kunne ikke laste forslag.');
        hideLoading();
    }
}

// Display algorithmic previews
function displayAlgorithmicPreviews(previews) {
    const container = document.getElementById('algorithmicPreviews');
    
    container.innerHTML = previews.map(preview => `
        <div class="algorithmic-preview">
            <div class="preview-header">
                <div class="preview-icon">${preview.icon || '🤖'}</div>
                <div class="preview-info">
                    <h4>${escapeHtml(preview.name)}</h4>
                    <p>${escapeHtml(preview.description)}</p>
                </div>
                <div class="preview-count">
                    <span class="count-number">${preview.preview_count.toLocaleString()}</span>
                    <span class="count-label">bilder</span>
                </div>
            </div>
            <div class="preview-actions">
                <button class="btn btn-secondary" onclick="executeAlgorithmicPreview('${preview.algorithm_type}', ${JSON.stringify(preview.params).replace(/"/g, '&quot;')})">
                    👁️ Forhåndsvis
                </button>
                <button class="btn btn-primary" onclick="createAlgorithmicSelection('${preview.algorithm_type}', '${escapeHtml(preview.name)}', ${JSON.stringify(preview.params).replace(/"/g, '&quot;')})">
                    💾 Lagre som Selection
                </button>
            </div>
        </div>
    `).join('');
}

// Execute algorithmic preview
async function executeAlgorithmicPreview(algorithmType, params) {
    try {
        showLoading('Utfører forhåndsvisning...');
        
        const response = await fetch(`${API_BASE}/selections/algorithmic/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                algorithm_type: algorithmType,
                params: params,
                save_to_database: false
            })
        });
        
        if (!response.ok) throw new Error('Failed to create preview');
        
        const tempSelection = await response.json();
        
        // Execute the temporary selection
        const execResponse = await fetch(`${API_BASE}/selections/algorithmic/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                algorithm_type: algorithmType,
                params: params,
                save_to_database: false
            })
        });
        
        // Close modal and show results
        closeAlgorithmicModal();
        hideLoading();
    } catch (error) {
        console.error('Error executing preview:', error);
        showError('Kunne ikke utføre forhåndsvisning.');
        hideLoading();
    }
}

// Create algorithmic selection
async function createAlgorithmicSelection(algorithmType, name, params) {
    try {
        showLoading('Oppretter selection...');
        
        const response = await fetch(`${API_BASE}/selections/algorithmic/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                algorithm_type: algorithmType,
                params: params,
                name: name,
                save_to_database: true
            })
        });
        
        if (!response.ok) throw new Error('Failed to create selection');
        
        const newSelection = await response.json();
        
        closeAlgorithmicModal();
        await loadSelections();
        showSuccess('Algoritmisk selection opprettet!');
        hideLoading();
    } catch (error) {
        console.error('Error creating algorithmic selection:', error);
        showError('Kunne ikke opprette selection.');
        hideLoading();
    }
}

// Close algorithmic modal
function closeAlgorithmicModal() {
    document.getElementById('algorithmicModal').style.display = 'none';
}

// Load authors for dropdown
async function loadAuthors() {
    try {
        const response = await fetch(`${API_BASE}/authors/`);
        if (!response.ok) return; // Fail silently
        
        const authors = await response.json();
        const select = document.getElementById('authorFilter');
        
        authors.forEach(author => {
            const option = document.createElement('option');
            option.value = author.id;
            option.textContent = author.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading authors:', error);
    }
}

// Filter and sort functions
function filterSelections() {
    loadSelections(); // Reload with new filters
}

function sortSelections() {
    const sortOrder = document.getElementById('sortOrder').value;
    
    let sortedSelections = [...currentSelections];
    
    switch (sortOrder) {
        case 'name':
            sortedSelections.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'created':
            sortedSelections.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            break;
        case 'accessed':
            sortedSelections.sort((a, b) => (b.access_count || 0) - (a.access_count || 0));
            break;
        default:
            break;
    }
    
    displaySelections(sortedSelections);
}

// Refresh selections
function refreshSelections() {
    loadSelections();
}

// Utility functions
function getSelectionTypeLabel(isAlgorithmic) {
    return isAlgorithmic ? '🤖 Algoritmisk' : '🔍 Søkebasert';
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('no-NO', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Loading and error handling
function showLoading(message = 'Laster...') {
    // Implementation depends on existing loading system
    console.log('Loading:', message);
}

function hideLoading() {
    // Implementation depends on existing loading system
    console.log('Loading complete');
}

function showError(message) {
    alert('Feil: ' + message); // Replace with better error handling
}

function showSuccess(message) {
    alert('Suksess: ' + message); // Replace with better success handling
}