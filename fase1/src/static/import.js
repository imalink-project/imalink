// Import page JavaScript functionality

// API base URL
const API_BASE = '/api';

// Current state
let allSessions = [];
let currentImportSession = null;
let pollingInterval = null;

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadAuthors();
    loadImportSessions();
});

// Load authors for the dropdown
async function loadAuthors() {
    try {
        const response = await fetch(`${API_BASE}/authors`);
        if (response.ok) {
            const authors = await response.json();
            const select = document.getElementById('importAuthor');
            
            // Clear existing options except the first one
            select.innerHTML = '<option value="">Velg fotograf (valgfri)</option>';
            
            authors.forEach(author => {
                const option = document.createElement('option');
                option.value = author.id;
                option.textContent = author.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading authors:', error);
    }
}

// Start new import
async function startImport() {
    const path = document.getElementById('importPath').value.trim();
    const description = document.getElementById('importDescription').value.trim() || 'Manual import';
    const authorId = document.getElementById('importAuthor').value;
    
    if (!path) {
        alert('Vennligst skriv inn en sti til bildekatalogen');
        return;
    }
    
    const importButton = document.getElementById('importButton');
    importButton.disabled = true;
    importButton.textContent = 'Starter import...';
    
    try {
        const requestBody = {
            source_path: path,
            source_description: description
        };
        
        if (authorId) {
            requestBody.default_author_id = parseInt(authorId);
        }
        
        const response = await fetch(`${API_BASE}/import/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
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
        startPollingImportStatus();
        
    } catch (error) {
        alert('Import feilet: ' + error.message);
        importButton.disabled = false;
        importButton.textContent = 'Start Import';
    }
}

// Start polling for import status
function startPollingImportStatus() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    pollingInterval = setInterval(async () => {
        if (!currentImportSession) {
            clearInterval(pollingInterval);
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/import/status/${currentImportSession}`);
            const status = await response.json();
            
            updateImportProgress(status);
            
            if (status.status !== 'in_progress') {
                // Import finished
                clearInterval(pollingInterval);
                currentImportSession = null;
                
                const importButton = document.getElementById('importButton');
                importButton.disabled = false;
                importButton.textContent = 'Start Import';
                
                if (status.status === 'completed') {
                    setTimeout(() => {
                        loadImportSessions(); // Reload sessions list
                    }, 1000);
                }
            }
            
        } catch (error) {
            console.error('Error polling import status:', error);
            clearInterval(pollingInterval);
        }
    }, 2000);
}

// Update import progress display
function updateImportProgress(status) {
    const progressContainer = document.getElementById('importProgress');
    
    const statusText = status.status === 'in_progress' ? 'Pågår...' : 
                      status.status === 'completed' ? 'Ferdig!' : 'Feilet';
    
    progressContainer.innerHTML = `
        <div><strong>Status:</strong> ${statusText}</div>
        <div><strong>Filer funnet:</strong> ${status.total_files_found}</div>
        <div><strong>Bilder importert:</strong> ${status.images_imported}</div>
        <div><strong>Duplikater hoppet over:</strong> ${status.duplicates_skipped}</div>
        <div><strong>RAW-filer hoppet over:</strong> ${status.raw_files_skipped || 0}</div>
        <div><strong>Single RAW-bilder hoppet over:</strong> ${status.single_raw_skipped || 0}</div>
        <div><strong>Feil:</strong> ${status.errors_count}</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${status.progress_percentage}%"></div>
        </div>
        <div>Fremdrift: ${status.progress_percentage.toFixed(1)}%</div>
    `;
}

// Load all import sessions
async function loadImportSessions() {
    try {
        const response = await fetch(`${API_BASE}/import/sessions`);
        if (response.ok) {
            allSessions = await response.json();
            displaySessions(allSessions);
        } else {
            throw new Error('Failed to load import sessions');
        }
    } catch (error) {
        console.error('Error loading import sessions:', error);
        document.getElementById('sessionsList').innerHTML = 
            '<div class="loading">Feil ved lasting av import-sesjoner</div>';
    }
}

// Display sessions in the list
function displaySessions(sessions) {
    const container = document.getElementById('sessionsList');
    const emptyState = document.getElementById('emptyState');
    
    if (sessions.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    container.style.display = 'grid';
    emptyState.style.display = 'none';
    
    container.innerHTML = sessions.map(session => createSessionCard(session)).join('');
}

// Create HTML for a session card
function createSessionCard(session) {
    const date = new Date(session.started_at).toLocaleString('no');
    const duration = session.completed_at ? 
        Math.round((new Date(session.completed_at) - new Date(session.started_at)) / 1000) + 's' : 
        'Pågående';
    
    const statusClass = `status-${session.status.replace('_', '-')}`;
    const statusText = session.status === 'completed' ? 'Fullført' :
                      session.status === 'failed' ? 'Feilet' :
                      session.status === 'in_progress' ? 'Pågående' : session.status;
    
    return `
        <div class="session-card" onclick="toggleSessionDetails(${session.id})">
            <div class="session-header">
                <div>
                    <div class="session-title">${session.source_description}</div>
                    <div class="session-date">📁 ${session.source_path}</div>
                    <div class="session-date">🕒 ${date} (${duration})</div>
                </div>
                <div class="session-date">ID: ${session.id}</div>
                <div class="session-status ${statusClass}">${statusText}</div>
            </div>
            
            <div class="session-stats">
                <div class="stat-item">
                    <div class="stat-number">${session.total_files_found}</div>
                    <div class="stat-label">Filer funnet</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${session.images_imported}</div>
                    <div class="stat-label">Importert</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${session.duplicates_skipped}</div>
                    <div class="stat-label">Duplikater</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${session.raw_files_skipped || 0}</div>
                    <div class="stat-label">RAW m/JPEG</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${session.single_raw_skipped || 0}</div>
                    <div class="stat-label">Single RAW</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${session.errors_count}</div>
                    <div class="stat-label">Feil</div>
                </div>
            </div>
            
            <div id="details-${session.id}" class="session-details">
                <h4>Detaljer</h4>
                <p><strong>Session ID:</strong> ${session.id}</p>
                <p><strong>Startet:</strong> ${new Date(session.started_at).toLocaleString('no')}</p>
                ${session.completed_at ? `<p><strong>Fullført:</strong> ${new Date(session.completed_at).toLocaleString('no')}</p>` : ''}
                <p><strong>Kildekatalog:</strong> ${session.source_path}</p>
                <p><strong>Beskrivelse:</strong> ${session.source_description}</p>
                ${session.error_log ? `<p><strong>Feilmelding:</strong> <code>${session.error_log}</code></p>` : ''}
            </div>
        </div>
    `;
}

// Toggle session details visibility
function toggleSessionDetails(sessionId) {
    const details = document.getElementById(`details-${sessionId}`);
    const card = details.parentElement;
    
    if (details.classList.contains('visible')) {
        details.classList.remove('visible');
        card.classList.remove('expanded');
    } else {
        // Close all other expanded cards
        document.querySelectorAll('.session-details.visible').forEach(el => {
            el.classList.remove('visible');
            el.parentElement.classList.remove('expanded');
        });
        
        details.classList.add('visible');
        card.classList.add('expanded');
    }
}

// Search and filter sessions
function searchSessions() {
    const pathQuery = document.getElementById('searchPath').value.toLowerCase();
    const descQuery = document.getElementById('searchDescription').value.toLowerCase();
    const statusFilter = document.getElementById('filterStatus').value;
    
    const filtered = allSessions.filter(session => {
        const pathMatch = !pathQuery || session.source_path.toLowerCase().includes(pathQuery);
        const descMatch = !descQuery || session.source_description.toLowerCase().includes(descQuery);
        const statusMatch = !statusFilter || session.status === statusFilter;
        
        return pathMatch && descMatch && statusMatch;
    });
    
    displaySessions(filtered);
}

// Add event listeners for search inputs
document.addEventListener('DOMContentLoaded', function() {
    ['searchPath', 'searchDescription', 'filterStatus'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', searchSessions);
        }
    });
});