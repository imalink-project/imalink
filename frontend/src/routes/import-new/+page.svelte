<script lang="ts">
	import { onMount } from 'svelte';
	import { currentView } from '$lib/stores/app';
	import FileStatusPanel from '$lib/components/FileStatusPanel.svelte';

	currentView.set('import');

	let importing = false;
	let importResults = null;
	let error = '';
	let authors = [];
	let selectedAuthorId = '';
	let progressInfo = '';
	let importDirectory = '/mnt/c/temp/PHOTOS_SRC_TEST_MICRO'; // Default from config
	let storageRoot = '/mnt/c/temp/storage'; // Default from config
	let currentImportSession = null;
	let importDescription = '';

	onMount(async () => {
		await loadAuthors();
		await loadDefaultStorageRoot();
	});

	async function loadAuthors() {
		try {
			const response = await fetch('http://localhost:8000/api/v1/authors/');
			if (response.ok) {
				const data = await response.json();
				authors = data.data || [];
			}
		} catch (err) {
			console.error('Failed to load authors:', err);
		}
	}

	async function loadDefaultStorageRoot() {
		try {
			const response = await fetch('http://localhost:8000/api/v1/file-location/storage-root');
			if (response.ok) {
				const data = await response.json();
				storageRoot = data.storage_root || storageRoot;
			}
		} catch (err) {
			console.warn('Failed to load default storage root:', err);
		}
	}

	async function startImport() {
		if (!importDirectory.trim()) {
			error = 'Please specify an import directory';
			return;
		}

		if (!storageRoot.trim()) {
			error = 'Please configure storage root';
			return;
		}

		importing = true;
		error = '';
		importResults = null;
		progressInfo = '';
		currentImportSession = null;

		try {
			progressInfo = 'Starting import session...';

			// Start import session
			const importRequest = {
				source_path: importDirectory,
				source_description: importDescription || `Import from ${importDirectory}`,
				default_author_id: selectedAuthorId || null,
				copy_files: true, // Enable file copying to storage
				storage_root: storageRoot
			};

			const response = await fetch('http://localhost:8000/api/v1/import/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(importRequest)
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to start import: ${response.status} ${errorText}`);
			}

			const result = await response.json();
			currentImportSession = result.import_session;
			
			progressInfo = `Import session ${currentImportSession.id} started. Processing files...`;

			// Poll for progress
			await pollImportProgress(currentImportSession.id);

		} catch (err) {
			console.error('Import failed:', err);
			error = err.message || 'Import failed';
		} finally {
			importing = false;
		}
	}

	async function pollImportProgress(importSessionId) {
		const pollInterval = 1000; // 1 second
		const maxPolls = 300; // 5 minutes max
		let polls = 0;

		const poll = async () => {
			if (polls >= maxPolls) {
				throw new Error('Import timed out');
			}

			try {
				const response = await fetch(`http://localhost:8000/api/v1/import/${importSessionId}`);
				if (!response.ok) {
					throw new Error(`Failed to check import status: ${response.status}`);
				}

				const session = await response.json();
				currentImportSession = session;

				// Update progress info
				if (session.status === 'completed') {
					progressInfo = `Import completed! ${session.images_imported} images imported, ${session.duplicates_skipped} duplicates skipped`;
					importResults = {
						success: true,
						session: session,
						imported_count: session.images_imported,
						skipped_count: session.duplicates_skipped,
						error_count: session.errors_count
					};
					return;
				} else if (session.status === 'failed') {
					throw new Error(session.error_log || 'Import failed');
				} else if (session.status === 'cancelled') {
					throw new Error('Import was cancelled');
				} else {
					// Still in progress
					const total = session.total_files_found || 0;
					const processed = session.files_processed || 0;
					progressInfo = `Processing: ${processed}/${total} files. Current: ${session.current_file || 'Unknown'}`;
					
					polls++;
					setTimeout(poll, pollInterval);
				}
			} catch (err) {
				throw err;
			}
		};

		await poll();
	}

	function reset() {
		importResults = null;
		error = '';
		progressInfo = '';
		currentImportSession = null;
		importDescription = '';
	}
</script>

<div class="import-page">
	<div class="page-header">
		<h1>📥 Import Images</h1>
		<p>Import images from a directory into the storage system</p>
		<button on:click={reset} class="reset-btn">🔄 Reset</button>
	</div>

	{#if error}
		<div class="error">
			<p>❌ {error}</p>
		</div>
	{/if}

	{#if progressInfo}
		<div class="progress-info">
			<p>ℹ️ {progressInfo}</p>
		</div>
	{/if}

	<!-- Storage Configuration -->
	<div class="step-card">
		<h3>🗂️ Storage Configuration</h3>
		<p>Configure where imported files will be stored</p>
		
		{#if currentImportSession}
			<FileStatusPanel 
				importSessionId={currentImportSession.id} 
				storageRoot={storageRoot} 
			/>
		{:else}
			<div class="storage-config">
				<div class="input-group">
					<label for="storage-root">Storage Root:</label>
					<input
						id="storage-root"
						type="text"
						bind:value={storageRoot}
						placeholder="e.g., X:, X:\my photo storage"
						class="path-input"
					/>
				</div>
				<p class="help-text">Files will be copied to katalognavn directories under this root</p>
			</div>
		{/if}
	</div>

	<!-- Import Configuration -->
	<div class="step-card">
		<h3>📁 Import Configuration</h3>
		<p>Select source directory and configure import settings</p>
		
		<div class="input-group">
			<label for="import-directory">Source Directory:</label>
			<input
				id="import-directory"
				type="text"
				bind:value={importDirectory}
				placeholder="e.g., C:\temp\PHOTOS_SRC_TEST_MINI"
				class="path-input"
				disabled={importing}
			/>
		</div>

		<div class="input-group">
			<label for="import-description">Description (optional):</label>
			<input
				id="import-description"
				type="text"
				bind:value={importDescription}
				placeholder="e.g., Summer vacation photos"
				class="path-input"
				disabled={importing}
			/>
		</div>

		<div class="input-group">
			<label for="author-select">Assign to Author (optional):</label>
			<select id="author-select" bind:value={selectedAuthorId} disabled={importing}>
				<option value="">No author</option>
				{#each authors as author}
					<option value={author.id}>{author.name}</option>
				{/each}
			</select>
		</div>

		<button 
			on:click={startImport}
			disabled={importing || !importDirectory.trim() || !storageRoot.trim()}
			class="import-btn"
		>
			{#if importing}
				<div class="spinner"></div> Importing...
			{:else}
				🚀 Start Import
			{/if}
		</button>
	</div>

	<!-- Import Progress -->
	{#if currentImportSession}
		<div class="step-card">
			<h3>📊 Import Progress</h3>
			<p>Import Session ID: {currentImportSession.id}</p>
			
			<div class="progress-details">
				<div class="progress-item">
					<span class="label">Status:</span>
					<span class="value status-{currentImportSession.status}">{currentImportSession.status}</span>
				</div>
				<div class="progress-item">
					<span class="label">Files Found:</span>
					<span class="value">{currentImportSession.total_files_found || 0}</span>
				</div>
				<div class="progress-item">
					<span class="label">Files Processed:</span>
					<span class="value">{currentImportSession.files_processed || 0}</span>
				</div>
				<div class="progress-item">
					<span class="label">Images Imported:</span>
					<span class="value">{currentImportSession.images_imported || 0}</span>
				</div>
				<div class="progress-item">
					<span class="label">Duplicates Skipped:</span>
					<span class="value">{currentImportSession.duplicates_skipped || 0}</span>
				</div>
				{#if currentImportSession.errors_count > 0}
					<div class="progress-item">
						<span class="label">Errors:</span>
						<span class="value error">{currentImportSession.errors_count}</span>
					</div>
				{/if}
			</div>

			{#if currentImportSession.storage_directory_name}
				<div class="storage-info">
					<h4>📂 Storage Directory</h4>
					<p class="storage-path">{currentImportSession.storage_directory_name}</p>
					<p class="storage-location">Location: {storageRoot}/{currentImportSession.storage_directory_name}</p>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Import Results -->
	{#if importResults}
		<div class="step-card">
			<h3>✅ Import Complete</h3>
			
			<div class="results">
				{#if importResults.success}
					<p class="success">✅ Import completed successfully!</p>
					<div class="result-stats">
						<div class="stat">
							<span class="stat-number">{importResults.imported_count}</span>
							<span class="stat-label">Images Imported</span>
						</div>
						<div class="stat">
							<span class="stat-number">{importResults.skipped_count}</span>
							<span class="stat-label">Duplicates Skipped</span>
						</div>
						{#if importResults.error_count > 0}
							<div class="stat">
								<span class="stat-number error">{importResults.error_count}</span>
								<span class="stat-label">Errors</span>
							</div>
						{/if}
					</div>
					<p class="completion">🎉 Import finished! <a href="/">View Photos</a></p>
				{:else}
					<p class="error">❌ Import failed</p>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.import-page {
		max-width: 900px;
		margin: 0 auto;
		padding: 1rem;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.page-header h1 {
		margin: 0;
		font-size: 2rem;
		color: #1f2937;
	}

	.page-header p {
		margin: 0;
		color: #6b7280;
		flex-grow: 1;
	}

	.reset-btn {
		background: #6b7280;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		cursor: pointer;
		font-weight: 500;
		transition: background-color 0.2s ease;
	}

	.reset-btn:hover {
		background: #4b5563;
	}

	.step-card {
		background: white;
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		border: 1px solid #e5e7eb;
	}

	.step-card h3 {
		margin: 0 0 1rem 0;
		color: #1f2937;
		font-size: 1.25rem;
	}

	.storage-config {
		padding: 1rem;
		background: #f9fafb;
		border-radius: 0.375rem;
		border: 1px solid #e5e7eb;
	}

	.input-group {
		margin-bottom: 1rem;
	}

	.input-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #374151;
	}

	.path-input, select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 1rem;
		background: white;
	}

	.path-input:focus, select:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 1px #3b82f6;
	}

	.path-input:disabled, select:disabled {
		background: #f3f4f6;
		color: #6b7280;
		cursor: not-allowed;
	}

	.help-text {
		margin-top: 0.5rem;
		font-size: 0.875rem;
		color: #6b7280;
	}

	.import-btn {
		background: #3b82f6;
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 0.375rem;
		cursor: pointer;
		font-weight: 500;
		font-size: 1rem;
		transition: background-color 0.2s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.import-btn:hover:not(:disabled) {
		background: #2563eb;
	}

	.import-btn:disabled {
		background: #9ca3af;
		cursor: not-allowed;
	}

	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid transparent;
		border-left-color: currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.progress-details {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin: 1rem 0;
	}

	.progress-item {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem;
		background: #f9fafb;
		border-radius: 0.375rem;
	}

	.progress-item .label {
		font-weight: 500;
		color: #374151;
	}

	.progress-item .value {
		color: #6b7280;
	}

	.progress-item .value.error {
		color: #dc2626;
		font-weight: 500;
	}

	.status-completed {
		color: #059669 !important;
		font-weight: 500 !important;
	}

	.status-failed {
		color: #dc2626 !important;
		font-weight: 500 !important;
	}

	.status-in-progress {
		color: #0369a1 !important;
		font-weight: 500 !important;
	}

	.storage-info {
		margin-top: 1rem;
		padding: 1rem;
		background: #f0f9ff;
		border-radius: 0.375rem;
		border: 1px solid #bae6fd;
	}

	.storage-info h4 {
		margin: 0 0 0.5rem 0;
		color: #0c4a6e;
	}

	.storage-path {
		font-family: monospace;
		font-size: 0.875rem;
		font-weight: 500;
		color: #0369a1;
		margin: 0.25rem 0;
	}

	.storage-location {
		font-size: 0.875rem;
		color: #64748b;
		margin: 0.25rem 0;
	}

	.results {
		padding: 1rem;
		background: #f8fafc;
		border-radius: 0.375rem;
		border-left: 4px solid #3b82f6;
	}

	.result-stats {
		display: flex;
		gap: 2rem;
		margin: 1rem 0;
	}

	.stat {
		text-align: center;
	}

	.stat-number {
		display: block;
		font-size: 2rem;
		font-weight: bold;
		color: #1f2937;
	}

	.stat-number.error {
		color: #dc2626;
	}

	.stat-label {
		display: block;
		font-size: 0.875rem;
		color: #6b7280;
		margin-top: 0.25rem;
	}

	.success {
		color: #059669;
		font-weight: 500;
		margin: 0 0 0.5rem 0;
	}

	.completion {
		color: #059669;
		font-weight: 500;
		margin: 1rem 0 0 0;
	}

	.completion a {
		color: #3b82f6;
		text-decoration: none;
	}

	.completion a:hover {
		text-decoration: underline;
	}

	.error {
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.375rem;
		padding: 1rem;
		margin-bottom: 1.5rem;
		color: #dc2626;
	}

	.progress-info {
		background: #dbeafe;
		border: 1px solid #93c5fd;
		border-radius: 0.375rem;
		padding: 1rem;
		margin-bottom: 1.5rem;
		color: #1e40af;
	}
</style>