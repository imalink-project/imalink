<script lang="ts">
	export let importSessionId: number;
	export let storageRoot: string = '';

	let storageStatus = {
		accessible: false,
		total_files: 0,
		found_files: 0,
		missing_files: 0,
		directory_name: null as string | null,
		error_message: null as string | null
	};
	let isLoading = false;
	let newStorageRoot = storageRoot;

	// Load storage status on mount
	$: if (importSessionId) {
		loadStorageStatus();
	}

	async function loadStorageStatus() {
		isLoading = true;
		try {
			const params = new URLSearchParams();
			if (storageRoot) {
				params.append('storage_root', storageRoot);
			}
			
			const response = await fetch(
				`/api/v1/file-location/import-session/${importSessionId}/storage-status?${params}`
			);
			
			if (response.ok) {
				storageStatus = await response.json();
			} else {
				storageStatus.error_message = `Failed to load storage status: ${response.status}`;
			}
		} catch (error) {
			storageStatus.error_message = `Error loading storage status: ${error.message}`;
		} finally {
			isLoading = false;
		}
	}

	async function configureStorageRoot() {
		if (!newStorageRoot.trim()) return;
		
		isLoading = true;
		try {
			const response = await fetch('/api/v1/file-location/configure-storage-root', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					storage_root: newStorageRoot
				})
			});

			if (response.ok) {
				const result = await response.json();
				if (result.success) {
					storageRoot = result.storage_root;
					await loadStorageStatus();
				} else {
					storageStatus.error_message = result.message;
				}
			} else {
				storageStatus.error_message = `Failed to configure storage root: ${response.status}`;
			}
		} catch (error) {
			storageStatus.error_message = `Error configuring storage root: ${error.message}`;
		} finally {
			isLoading = false;
		}
	}

	function getStatusColor(accessible: boolean): string {
		return accessible ? '#059669' : '#dc2626';
	}

	function getStatusText(accessible: boolean, foundFiles: number, totalFiles: number): string {
		if (accessible) {
			if (foundFiles === totalFiles) {
				return 'All files accessible';
			} else {
				return `${foundFiles}/${totalFiles} files found`;
			}
		} else {
			return 'Files not accessible';
		}
	}
</script>

<div class="file-status-panel">
	<h3>File Access Status</h3>
	
	<!-- Storage Root Configuration -->
	<div class="config-section">
		<h4>Storage Root Configuration</h4>
		<div class="config-row">
			<input
				type="text"
				bind:value={newStorageRoot}
				placeholder="Enter storage root path (e.g., X:, X:\my photo storage)"
				class="storage-input"
			/>
			<button 
				class="btn btn-primary" 
				on:click={configureStorageRoot}
				disabled={isLoading || !newStorageRoot.trim()}
			>
				{isLoading ? 'Configuring...' : 'Set Root'}
			</button>
		</div>
		{#if storageRoot}
			<div class="current-root">
				Current storage root: <code>{storageRoot}</code>
			</div>
		{/if}
	</div>

	<!-- Status Display -->
	{#if isLoading}
		<div class="loading">
			Loading storage status...
		</div>
	{:else}
		<div class="status-section">
			<div class="status-row">
				<span class="label">Status:</span>
				<span 
					class="status-text"
					style="color: {getStatusColor(storageStatus.accessible)}"
				>
					{getStatusText(storageStatus.accessible, storageStatus.found_files, storageStatus.total_files)}
				</span>
			</div>

			{#if storageStatus.directory_name}
				<div class="status-row">
					<span class="label">Storage Directory:</span>
					<span class="value monospace">{storageStatus.directory_name}</span>
				</div>
			{/if}

			{#if storageStatus.total_files > 0}
				<div class="status-row">
					<span class="label">Files Found:</span>
					<span class="value">{storageStatus.found_files}</span>
				</div>
				
				{#if storageStatus.missing_files > 0}
					<div class="status-row">
						<span class="label">Files Missing:</span>
						<span class="value warning">{storageStatus.missing_files}</span>
					</div>
				{/if}
			{/if}

			{#if storageStatus.error_message}
				<div class="error-section">
					<h4>Issues:</h4>
					<div class="error-text">{storageStatus.error_message}</div>
				</div>
			{/if}
		</div>

		<div class="action-buttons">
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
	.file-status-panel {
		background: var(--color-gray-50);
		border: 1px solid var(--border-light);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
		margin: var(--spacing-md) 0;
	}

	.file-status-panel h3 {
		margin: 0 0 var(--spacing-md) 0;
		color: var(--color-gray-800);
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
	}

	.config-section {
		margin-bottom: var(--spacing-lg);
		padding-bottom: var(--spacing-md);
		border-bottom: 1px solid var(--border-light);
	}

	.config-section h4 {
		margin: 0 0 var(--spacing-sm) 0;
		color: var(--color-gray-700);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
	}

	.config-row {
		display: flex;
		gap: var(--spacing-sm);
		align-items: center;
	}

	.storage-input {
		flex: 1;
		padding: var(--spacing-sm);
		border: 1px solid var(--border-medium);
		border-radius: var(--radius-md);
		font-size: var(--font-size-sm);
		font-family: monospace;
		transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
	}

	.storage-input:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 1px var(--color-primary);
	}

	.current-root {
		margin-top: var(--spacing-sm);
		font-size: var(--font-size-xs);
		color: var(--color-gray-500);
	}

	.current-root code {
		background: var(--color-gray-100);
		padding: var(--spacing-xs) var(--spacing-xs);
		border-radius: var(--radius-sm);
		font-family: monospace;
	}

	.loading {
		color: var(--color-gray-500);
		font-style: italic;
		text-align: center;
		padding: var(--spacing-xl);
	}

	.status-section {
		margin-bottom: var(--spacing-lg);
	}

	.status-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-sm);
	}

	.label {
		font-weight: var(--font-weight-medium);
		color: var(--color-gray-700);
	}

	.value {
		color: var(--color-gray-500);
	}

	.monospace {
		font-family: monospace;
		font-size: var(--font-size-sm);
	}

	.status-text {
		font-weight: var(--font-weight-medium);
	}

	.warning {
		color: var(--color-warning-hover);
		font-weight: var(--font-weight-medium);
	}

	.error-section {
		background: var(--bg-error);
		border: 1px solid var(--border-error);
		border-radius: var(--radius-md);
		padding: var(--spacing-md);
		margin: var(--spacing-md) 0;
	}

	.error-section h4 {
		margin: 0 0 var(--spacing-sm) 0;
		color: var(--color-error);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
	}

	.error-text {
		color: var(--color-error);
		font-size: var(--font-size-sm);
		line-height: var(--line-height-normal);
	}

	.action-buttons {
		display: flex;
		gap: var(--spacing-sm);
	}

	.btn {
		padding: var(--spacing-sm) var(--spacing-md);
		border-radius: var(--radius-md);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: all var(--transition-normal);
		border: 1px solid transparent;
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-primary {
		background: var(--color-primary);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	.btn-outline {
		background: white;
		color: var(--color-gray-700);
		border-color: var(--border-medium);
	}

	.btn-outline:hover:not(:disabled) {
		background: var(--color-gray-50);
		border-color: var(--border-dark);
	}
</style>