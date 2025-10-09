<script lang="ts">
	import { onDestroy } from 'svelte';
	import { storageService, type StorageProgress, type StorageResult } from '$lib/services/storage.service';

	export let importSessionId: number;
	export let importSessionName: string = '';

	let storageStatus: StorageProgress | null = null;
	let isLoading = false;
	let error = '';
	let pollInterval: number | null = null;

	// Load initial storage status
	$: if (importSessionId) {
		loadStorageStatus();
	}

	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});

	async function loadStorageStatus() {
		try {
			error = '';
			storageStatus = await storageService.getStorageStatus(importSessionId);
		} catch (err) {
			console.error('Failed to load storage status:', err);
			error = `Failed to load storage status: ${err instanceof Error ? err.message : String(err)}`;
		}
	}

	async function prepareStorage() {
		isLoading = true;
		error = '';

		try {
			const result = await storageService.prepareStorage(importSessionId, importSessionName);
			
			if (result.success) {
				// Reload status to show prepared storage
				await loadStorageStatus();
			} else {
				error = result.message;
			}
		} catch (err) {
			error = `Failed to prepare storage: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			isLoading = false;
		}
	}

	async function startStorageCopy() {
		isLoading = true;
		error = '';

		try {
			const result = await storageService.startStorageCopy(importSessionId);
			
			if (result.success) {
				// Start polling for progress
				startPolling();
			} else {
				error = result.message;
			}
		} catch (err) {
			error = `Failed to start storage copy: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			isLoading = false;
		}
	}

	async function verifyStorage() {
		isLoading = true;
		error = '';

		try {
			const result = await storageService.verifyStorage(importSessionId);
			
			if (result.success) {
				// Reload status to show verification results
				await loadStorageStatus();
			} else {
				error = result.message;
			}
		} catch (err) {
			error = `Failed to verify storage: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			isLoading = false;
		}
	}

	function startPolling() {
		// Clear existing poll
		if (pollInterval) {
			clearInterval(pollInterval);
		}

		// Poll every 2 seconds while in progress
		pollInterval = setInterval(async () => {
			const progress = await storageService.getStorageStatus(importSessionId);
			
			if (progress) {
				storageStatus = progress;

				// Stop polling when completed or failed
				if (progress.status !== 'in_progress' && pollInterval) {
					clearInterval(pollInterval);
					pollInterval = null;
				}
			}
		}, 2000);
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'not_started': return '#6b7280';
			case 'in_progress': return '#3b82f6';
			case 'completed': return '#059669';
			case 'failed': return '#dc2626';
			default: return '#6b7280';
		}
	}


</script>

<div class="storage-panel">
	<h3>Permanent Storage</h3>
	
	{#if error}
		<div class="error">
			{error}
		</div>
	{/if}

	{#if !storageStatus}
		<div class="no-status">
			<p>Loading storage status...</p>
		</div>
	{:else}
		<div class="status-info">
			<div class="status-row">
				<span class="label">Status:</span>
				<span class="status" style="color: {getStatusColor(storageStatus.status)}">
					{storageService.getStatusDescription(storageStatus.status)}
				</span>
			</div>

			{#if storageStatus.storage_uuid}
				<div class="status-row">
					<span class="label">Storage ID:</span>
					<span class="value monospace">{storageStatus.storage_uuid.substring(0, 8)}...</span>
				</div>
			{/if}

			{#if storageStatus.storage_directory_name}
				<div class="status-row">
					<span class="label">Directory:</span>
					<span class="value monospace">{storageStatus.storage_directory_name}</span>
				</div>
			{/if}

			{#if storageStatus.total_size_mb > 0}
				<div class="status-row">
					<span class="label">Total Size:</span>
					<span class="value">{storageService.formatStorageSize(storageStatus.total_size_mb)}</span>
				</div>
			{/if}

			{#if storageStatus.status === 'in_progress'}
				<div class="progress-section">
					<div class="progress-bar">
						<div 
							class="progress-fill" 
							style="width: {storageStatus.progress_percentage}%"
						></div>
					</div>
					<div class="progress-text">
						{storageStatus.progress_percentage.toFixed(1)}% 
						({storageStatus.files_processed}/{storageStatus.total_files} files)
					</div>
					
					{#if storageStatus.current_file}
						<div class="current-file">
							Copying: {storageStatus.current_file}
						</div>
					{/if}
				</div>
			{/if}

			{#if storageStatus.status === 'completed'}
				<div class="completion-stats">
					<div class="stat-row">
						<span class="label">Files Copied:</span>
						<span class="value success">{storageStatus.files_copied}</span>
					</div>
					{#if storageStatus.files_skipped > 0}
						<div class="stat-row">
							<span class="label">Files Skipped:</span>
							<span class="value info">{storageStatus.files_skipped}</span>
						</div>
					{/if}
					{#if storageStatus.completed_at}
						<div class="stat-row">
							<span class="label">Completed:</span>
							<span class="value">{new Date(storageStatus.completed_at).toLocaleString()}</span>
						</div>
					{/if}
				</div>
			{/if}

			{#if storageStatus.errors && storageStatus.errors.length > 0}
				<div class="error-section">
					<h4>Errors:</h4>
					<ul class="error-list">
						{#each storageStatus.errors as error}
							<li>{error}</li>
						{/each}
					</ul>
				</div>
			{/if}
		</div>

		<div class="action-buttons">
			{#if !storageStatus.has_permanent_storage}
				<button 
					class="btn btn-primary" 
					on:click={prepareStorage}
					disabled={isLoading}
				>
					{isLoading ? 'Preparing...' : 'Prepare Storage'}
				</button>
			{:else if storageStatus.status === 'not_started'}
				<button 
					class="btn btn-secondary" 
					on:click={startStorageCopy}
					disabled={isLoading}
				>
					{isLoading ? 'Starting...' : 'Start Copy to Storage'}
				</button>
			{:else if storageStatus.status === 'completed'}
				<button 
					class="btn btn-outline" 
					on:click={verifyStorage}
					disabled={isLoading}
				>
					{isLoading ? 'Verifying...' : 'Verify Storage'}
				</button>
			{/if}

			<button 
				class="btn btn-outline" 
				on:click={loadStorageStatus}
				disabled={isLoading}
			>
				Refresh Status
			</button>
		</div>
	{/if}
</div>

<style>
	.storage-panel {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin: 1rem 0;
	}

	.storage-panel h3 {
		margin: 0 0 1rem 0;
		color: #1f2937;
		font-size: 1.125rem;
		font-weight: 600;
	}

	.error {
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.375rem;
		padding: 0.75rem;
		margin-bottom: 1rem;
		color: #dc2626;
		font-size: 0.875rem;
	}

	.no-status {
		color: #6b7280;
		font-style: italic;
	}

	.status-info {
		margin-bottom: 1.5rem;
	}

	.status-row, .stat-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.label {
		font-weight: 500;
		color: #374151;
	}

	.value {
		color: #6b7280;
	}

	.monospace {
		font-family: monospace;
		font-size: 0.875rem;
	}

	.status {
		font-weight: 500;
	}

	.success {
		color: #059669;
	}

	.info {
		color: #0369a1;
	}

	.progress-section {
		margin: 1rem 0;
		padding: 1rem;
		background: #f3f4f6;
		border-radius: 0.375rem;
	}

	.progress-bar {
		width: 100%;
		height: 0.5rem;
		background: #e5e7eb;
		border-radius: 0.25rem;
		margin-bottom: 0.5rem;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: #3b82f6;
		transition: width 0.3s ease;
	}

	.progress-text {
		font-size: 0.875rem;
		color: #374151;
		font-weight: 500;
	}

	.current-file {
		font-size: 0.75rem;
		color: #6b7280;
		font-family: monospace;
		margin-top: 0.5rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.completion-stats {
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 0.375rem;
		padding: 1rem;
		margin: 1rem 0;
	}

	.error-section {
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.375rem;
		padding: 1rem;
		margin: 1rem 0;
	}

	.error-section h4 {
		margin: 0 0 0.5rem 0;
		color: #dc2626;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.error-list {
		margin: 0;
		padding-left: 1rem;
		color: #dc2626;
		font-size: 0.875rem;
	}

	.action-buttons {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.btn {
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		border: 1px solid transparent;
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-primary {
		background: #3b82f6;
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: #2563eb;
	}

	.btn-secondary {
		background: #059669;
		color: white;
	}

	.btn-secondary:hover:not(:disabled) {
		background: #047857;
	}

	.btn-outline {
		background: white;
		color: #374151;
		border-color: #d1d5db;
	}

	.btn-outline:hover:not(:disabled) {
		background: #f9fafb;
		border-color: #9ca3af;
	}
</style>