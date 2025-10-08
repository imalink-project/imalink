<!--
    Demo component for testing the new batch import system
    
    This replaces the old upload-based import with modern File System Access API
    and batch processing for handling 50,000+ images efficiently.
-->

<script>
    import { onMount } from 'svelte';
    import { BatchImportService } from '../lib/services/batch-import.service.ts';
    import { isFileSystemAccessSupported } from '../lib/services/file-system-access.service.js';
    
    let importService = null;
    let isImporting = false;
    let progress = {
        phase: 'idle',
        totalFiles: 0,
        processedFiles: 0,
        percentage: 0,
        batchesCompleted: 0,
        totalBatches: 0,
        errors: []
    };
    let result = null;
    let isApiSupported = false;
    
    onMount(() => {
        isApiSupported = isFileSystemAccessSupported();
    });
    
    async function startBatchImport() {
        if (isImporting) return;
        
        isImporting = true;
        result = null;
        progress = {
            phase: 'scanning',
            totalFiles: 0,
            processedFiles: 0,
            percentage: 0,
            batchesCompleted: 0,
            totalBatches: 0,
            errors: []
        };
        
        try {
            importService = new BatchImportService({
                batchSize: 50,
                maxConcurrency: 4,
                generateThumbnails: true,
                extractExif: true,
                onProgress: (p) => {
                    progress = { ...p };
                },
                onBatchComplete: (batchResult) => {
                    console.log('Batch completed:', batchResult);
                }
            });
            
            result = await importService.startImport();
            
        } catch (error) {
            console.error('Import failed:', error);
            progress = {
                ...progress,
                phase: 'error',
                errors: [...progress.errors, error.message]
            };
        } finally {
            isImporting = false;
            importService = null;
        }
    }
    
    function cancelImport() {
        if (importService) {
            importService.cancel();
        }
    }
    
    function getPhaseText(phase) {
        switch (phase) {
            case 'scanning': return '📂 Scanning directory...';
            case 'processing': return '⚡ Processing images...';
            case 'uploading': return '☁️ Uploading to server...';
            case 'completed': return '✅ Import completed!';
            case 'error': return '❌ Import failed';
            default: return '⏸️ Ready to import';
        }
    }
    
    function getProgressColor(phase) {
        switch (phase) {
            case 'scanning': return '#3b82f6';
            case 'processing': return '#8b5cf6';
            case 'uploading': return '#10b981';
            case 'completed': return '#059669';
            case 'error': return '#dc2626';
            default: return '#6b7280';
        }
    }
</script>

<div class="batch-import-demo">
    <div class="header">
        <h2>🚀 Batch Import Demo</h2>
        <p>Modern File System Access API + Photos Batch Processing</p>
        
        {#if !isApiSupported}
            <div class="warning">
                ⚠️ File System Access API not supported in this browser. 
                Please use Chrome 86+ or Edge 86+ with HTTPS.
            </div>
        {/if}
    </div>
    
    <div class="controls">
        <button 
            on:click={startBatchImport} 
            disabled={isImporting || !isApiSupported}
            class="primary-button"
        >
            {#if isImporting}
                🔄 Importing...
            {:else}
                📁 Select Directory & Start Import
            {/if}
        </button>
        
        {#if isImporting}
            <button on:click={cancelImport} class="cancel-button">
                ❌ Cancel Import
            </button>
        {/if}
    </div>
    
    {#if progress.phase !== 'idle'}
        <div class="progress-section">
            <div class="phase-indicator">
                <h3>{getPhaseText(progress.phase)}</h3>
                {#if progress.currentFile}
                    <p class="current-file">📄 {progress.currentFile}</p>
                {/if}
            </div>
            
            <div class="progress-bar">
                <div 
                    class="progress-fill" 
                    style="width: {progress.percentage}%; background-color: {getProgressColor(progress.phase)}"
                ></div>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <span class="label">Files:</span>
                    <span class="value">{progress.processedFiles}/{progress.totalFiles}</span>
                </div>
                <div class="stat">
                    <span class="label">Batches:</span>
                    <span class="value">{progress.batchesCompleted}/{progress.totalBatches}</span>
                </div>
                <div class="stat">
                    <span class="label">Progress:</span>
                    <span class="value">{progress.percentage}%</span>
                </div>
            </div>
        </div>
    {/if}
    
    {#if result}
        <div class="result-section">
            <h3>📊 Import Results</h3>
            <div class="result-grid">
                <div class="result-item success">
                    <span class="label">✅ Photos Created:</span>
                    <span class="value">{result.photosCreated}</span>
                </div>
                <div class="result-item success">
                    <span class="label">✅ Images Created:</span>
                    <span class="value">{result.imagesCreated}</span>
                </div>
                {#if result.photosFailed > 0}
                    <div class="result-item error">
                        <span class="label">❌ Photos Failed:</span>
                        <span class="value">{result.photosFailed}</span>
                    </div>
                {/if}
                {#if result.imagesFailed > 0}
                    <div class="result-item error">
                        <span class="label">❌ Images Failed:</span>
                        <span class="value">{result.imagesFailed}</span>
                    </div>
                {/if}
                <div class="result-item">
                    <span class="label">⏱️ Processing Time:</span>
                    <span class="value">{result.processingTimeSeconds.toFixed(2)}s</span>
                </div>
            </div>
        </div>
    {/if}
    
    {#if progress.errors.length > 0}
        <div class="errors-section">
            <h3>⚠️ Errors ({progress.errors.length})</h3>
            <div class="errors-list">
                {#each progress.errors.slice(0, 10) as error}
                    <div class="error-item">{error}</div>
                {/each}
                {#if progress.errors.length > 10}
                    <div class="error-item">... and {progress.errors.length - 10} more errors</div>
                {/if}
            </div>
        </div>
    {/if}
</div>

<style>
    .batch-import-demo {
        max-width: 800px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .header h2 {
        font-size: 1.75rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #1f2937;
    }
    
    .header p {
        color: #6b7280;
        font-size: 1rem;
    }
    
    .warning {
        margin-top: 1rem;
        padding: 1rem;
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        color: #b45309;
    }
    
    .controls {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-bottom: 2rem;
    }
    
    .primary-button {
        background: #3b82f6;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .primary-button:hover:not(:disabled) {
        background: #2563eb;
    }
    
    .primary-button:disabled {
        background: #9ca3af;
        cursor: not-allowed;
    }
    
    .cancel-button {
        background: #dc2626;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .cancel-button:hover {
        background: #b91c1c;
    }
    
    .progress-section {
        margin-bottom: 2rem;
    }
    
    .phase-indicator {
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .phase-indicator h3 {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #1f2937;
    }
    
    .current-file {
        color: #6b7280;
        font-size: 0.875rem;
        font-family: monospace;
    }
    
    .progress-bar {
        width: 100%;
        height: 12px;
        background: #e5e7eb;
        border-radius: 6px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    
    .progress-fill {
        height: 100%;
        transition: width 0.3s ease-in-out;
        border-radius: 6px;
    }
    
    .stats {
        display: flex;
        justify-content: space-around;  
        gap: 1rem;
    }
    
    .stat {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.25rem;
    }
    
    .stat .label {
        font-size: 0.875rem;
        color: #6b7280;
    }
    
    .stat .value {
        font-size: 1.125rem;
        font-weight: 600;
        color: #1f2937;
    }
    
    .result-section, .errors-section {
        margin-top: 2rem;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    
    .result-section h3, .errors-section h3 {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #1f2937;
    }
    
    .result-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }
    
    .result-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        border-radius: 6px;
        background: #f9fafb;
    }
    
    .result-item.success {
        background: #ecfdf5;
        border: 1px solid #d1fae5;
    }
    
    .result-item.error {
        background: #fef2f2;
        border: 1px solid #fecaca;
    }
    
    .result-item .label {
        font-weight: 500;
        color: #374151;
    }
    
    .result-item .value {
        font-weight: 600;
        color: #1f2937;
    }
    
    .errors-list {
        max-height: 200px;
        overflow-y: auto;
    }
    
    .error-item {
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 4px;
        font-size: 0.875rem;
        color: #b91c1c;
        font-family: monospace;
    }
</style>