<script>
    import { onMount } from 'svelte';
    import { getImportSessions, createImportSession } from '$lib/api.js';

    let importSessions = [];
    let loading = true;
    let error = null;
    let sourcePath = '';
    let creating = false;
    let createError = null;

    onMount(async () => {
        await loadImportSessions();
    });

    async function loadImportSessions() {
        try {
            loading = true;
            importSessions = await getImportSessions();
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    async function startImport() {
        if (!sourcePath.trim()) {
            createError = 'Vennligst angi en kildemappe';
            return;
        }

        try {
            creating = true;
            createError = null;
            
            const session = await createImportSession(sourcePath.trim());
            
            // Refresh the list
            await loadImportSessions();
            
            // Clear form
            sourcePath = '';
            
        } catch (err) {
            createError = err.message;
        } finally {
            creating = false;
        }
    }

    function formatDate(dateString) {
        if (!dateString) return 'Ukjent';
        return new Date(dateString).toLocaleString('no-NO');
    }

    function getStatusText(status) {
        switch (status) {
            case 'pending': return 'Venter';
            case 'running': return 'Kjører';
            case 'completed': return 'Fullført';
            case 'failed': return 'Feilet';
            default: return status;
        }
    }

    function getStatusClass(status) {
        switch (status) {
            case 'pending': return 'status-pending';
            case 'running': return 'status-running';
            case 'completed': return 'status-completed';
            case 'failed': return 'status-failed';
            default: return 'status-unknown';
        }
    }
</script>

<svelte:head>
    <title>Import - ImaLink</title>
</svelte:head>

<div class="import-page">
    <div class="page-header">
        <h1>Importer Bilder</h1>
        <p>Legg til nye bilder fra en mappe til din samling</p>
    </div>

    <!-- New Import Form -->
    <div class="import-form-section">
        <div class="form-card">
            <h2>Start Ny Import</h2>
            <form on:submit|preventDefault={startImport}>
                <div class="form-group">
                    <label for="sourcePath">Kildemappe:</label>
                    <input 
                        type="text" 
                        id="sourcePath"
                        bind:value={sourcePath}
                        placeholder="F.eks. C:\Bilder\Feriebilder"
                        disabled={creating}
                        required
                    />
                </div>

                {#if createError}
                    <div class="error-message">
                        {createError}
                    </div>
                {/if}

                <button type="submit" disabled={creating || !sourcePath.trim()}>
                    {creating ? 'Starter import...' : 'Start Import'}
                </button>
            </form>
        </div>
    </div>

    <!-- Import Sessions List -->
    <div class="sessions-section">
        <div class="section-header">
            <h2>Import Historikk</h2>
            <button on:click={loadImportSessions} disabled={loading}>
                {loading ? 'Oppdaterer...' : 'Oppdater'}
            </button>
        </div>

        {#if loading && importSessions.length === 0}
            <div class="loading">
                <p>Laster import historikk...</p>
            </div>
        {:else if error}
            <div class="error">
                <h3>Feil ved lasting</h3>
                <p>{error}</p>
                <button on:click={loadImportSessions}>Prøv igjen</button>
            </div>
        {:else if importSessions.length === 0}
            <div class="empty">
                <p>Ingen import-sesjoner funnet.</p>
                <p>Start din første import ovenfor.</p>
            </div>
        {:else}
            <div class="sessions-grid">
                {#each importSessions as session (session.id)}
                    <div class="session-card">
                        <div class="session-header">
                            <h3>{session.source_path}</h3>
                            <span class="status {getStatusClass(session.status)}">
                                {getStatusText(session.status)}
                            </span>
                        </div>
                        
                        <div class="session-details">
                            <p><strong>Startet:</strong> {formatDate(session.created_at)}</p>
                            
                            {#if session.completed_at}
                                <p><strong>Fullført:</strong> {formatDate(session.completed_at)}</p>
                            {/if}

                            {#if session.total_images !== null}
                                <p><strong>Bilder funnet:</strong> {session.total_images}</p>
                            {/if}

                            {#if session.processed_images !== null}
                                <p><strong>Behandlet:</strong> {session.processed_images}</p>
                            {/if}

                            {#if session.error_message}
                                <p class="error-text"><strong>Feil:</strong> {session.error_message}</p>
                            {/if}
                        </div>

                        {#if session.status === 'running'}
                            <div class="progress-section">
                                <div class="progress-bar">
                                    <div 
                                        class="progress-fill"
                                        style="width: {session.total_images > 0 ? (session.processed_images / session.total_images) * 100 : 0}%"
                                    ></div>
                                </div>
                                <p class="progress-text">
                                    {session.processed_images} / {session.total_images} bilder
                                </p>
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    .import-page {
        max-width: 1000px;
        margin: 0 auto;
    }

    .page-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .page-header h1 {
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }

    .page-header p {
        color: #666;
        margin: 0;
    }

    .import-form-section {
        margin-bottom: 3rem;
    }

    .form-card {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .form-card h2 {
        margin: 0 0 1.5rem 0;
        color: #2c3e50;
    }

    .form-group {
        margin-bottom: 1rem;
    }

    .form-group label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #333;
    }

    .form-group input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 1rem;
        box-sizing: border-box;
    }

    .form-group input:focus {
        outline: none;
        border-color: #3498db;
    }

    .form-group input:disabled {
        background-color: #f5f5f5;
        color: #666;
    }

    button {
        background: #3498db;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 1rem;
        transition: background-color 0.2s;
    }

    button:hover:not(:disabled) {
        background: #2980b9;
    }

    button:disabled {
        background: #bdc3c7;
        cursor: not-allowed;
    }

    .error-message {
        background: #ffe6e6;
        color: #d32f2f;
        padding: 0.75rem;
        border-radius: 4px;
        margin-bottom: 1rem;
        border: 1px solid #ffcccc;
    }

    .sessions-section {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }

    .section-header h2 {
        margin: 0;
        color: #2c3e50;
    }

    .section-header button {
        background: #95a5a6;
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
    }

    .loading, .error, .empty {
        text-align: center;
        padding: 2rem;
        color: #666;
    }

    .error {
        background: #ffe6e6;
        border-radius: 8px;
        color: #d32f2f;
    }

    .sessions-grid {
        display: grid;
        gap: 1rem;
    }

    .session-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        background: #f8f9fa;
    }

    .session-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .session-header h3 {
        margin: 0;
        color: #2c3e50;
        font-size: 1rem;
        word-break: break-all;
    }

    .status {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-pending {
        background: #fff3cd;
        color: #856404;
    }

    .status-running {
        background: #cce7ff;
        color: #004085;
        animation: pulse 2s infinite;
    }

    .status-completed {
        background: #d4edda;
        color: #155724;
    }

    .status-failed {
        background: #f8d7da;
        color: #721c24;
    }

    .status-unknown {
        background: #e2e3e5;
        color: #383d41;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    .session-details p {
        margin: 0.25rem 0;
        font-size: 0.9rem;
        color: #666;
    }

    .error-text {
        color: #d32f2f !important;
    }

    .progress-section {
        margin-top: 1rem;
    }

    .progress-bar {
        width: 100%;
        height: 8px;
        background: #e0e0e0;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #3498db, #2980b9);
        transition: width 0.3s ease;
    }

    .progress-text {
        font-size: 0.8rem;
        color: #666;
        text-align: center;
        margin: 0;
    }

    @media (max-width: 768px) {
        .form-card, .sessions-section {
            padding: 1rem;
        }
        
        .session-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }
        
        .session-header h3 {
            word-break: break-all;
        }
    }
</style>