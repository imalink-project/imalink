<script lang="ts">
	import { onMount } from 'svelte';
	import { currentView } from '$lib/stores/app';
	import { selectDirectory, isFileSystemAccessSupported, scanDirectoryForImages } from '$lib/services/file-system-access.service.js';

	currentView.set('imports');

	let error = '';
	let authors: any[] = [];
	let selectedAuthorId = '';
	let importDirectoryHandle: FileSystemDirectoryHandle | null = null;
	let storageRootHandle: FileSystemDirectoryHandle | null = null;
	let importDirectoryPath = 'Ikke valgt';
	let storageRootPath = 'Ikke valgt';
	let importing = false;
	let importResults: any = null;
	let progressInfo = '';
	let isApiSupported = false;

	onMount(async () => {
		isApiSupported = isFileSystemAccessSupported();
		await loadAuthors();
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
			error = 'Failed to load authors';
		}
	}

	async function selectImportDirectory() {
		if (!isApiSupported) {
			error = 'File System Access API ikke støttet i denne nettleseren. Bruk Chrome 86+ eller Edge 86+.';
			return;
		}

		try {
			importDirectoryHandle = await selectDirectory();
			importDirectoryPath = `Valgt: ${importDirectoryHandle.name}`;
			error = '';
		} catch (err: any) {
			if (err.message.includes('cancelled')) {
				// User cancelled, not an error
				return;
			}
			error = `Feil ved valg av import-katalog: ${err.message}`;
		}
	}

	async function selectStorageRoot() {
		if (!isApiSupported) {
			error = 'File System Access API ikke støttet i denne nettleseren. Bruk Chrome 86+ eller Edge 86+.';
			return;
		}

		try {
			// Velg storage directory med skrivetilgang
			storageRootHandle = await (window as any).showDirectoryPicker({
				mode: 'readwrite'
			});
			storageRootPath = `Valgt: ${storageRootHandle!.name} (skrivetilgang)`;
			error = '';
		} catch (err: any) {
			if (err.name === 'AbortError') {
				// User cancelled, not an error
				return;
			}
			error = `Feil ved valg av storage-katalog: ${err.message}`;
		}
	}

	async function startImport() {
		if (!importDirectoryHandle || !storageRootHandle) {
			error = 'Vennligst velg både import-katalog og storage-katalog';
			return;
		}

		importing = true;
		error = '';
		importResults = null;
		progressInfo = 'Starter frontend-dreven import...';

		try {
			// Steg 1: Skann import-katalog for bildefiler
			progressInfo = 'Skanner for bildefiler...';
			const imageFiles = await scanDirectoryForImages(importDirectoryHandle!, {
				supportedFormats: ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.dng', '.arw', '.cr2', '.nef', '.orf', '.rw2'],
				recursive: true,
				progressCallback: (progress: any) => {
					progressInfo = `Skanner: ${progress.scanned} filer funnet...`;
				}
			});

			if (imageFiles.length === 0) {
				error = 'Ingen bildefiler funnet i valgt katalog';
				return;
			}

			progressInfo = `Funnet ${imageFiles.length} bildefiler. Oppretter import session...`;

			// Steg 2: Opprett import session i backend (kun metadata)
			const response = await fetch('http://localhost:8000/api/v1/import_sessions/start', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					source_path: '/tmp',  // Dummy-sti for frontend-drevet import
					source_description: `Frontend import from ${importDirectoryHandle.name}: ${imageFiles.length} files`,
					default_author_id: selectedAuthorId || null
				})
			});

			if (!response.ok) {
				const errorData = await response.text();
				error = `Backend feil: ${response.status} - ${errorData}`;
				return;
			}

			const startResult = await response.json();
			const sessionId = startResult.import_id;
			
			progressInfo = `Import session ${sessionId} opprettet. Starter filkopiering...`;

			// Steg 3: Generer storage_name via backend
			progressInfo = 'Genererer unikt storage-navn...';
			const storageNameResponse = await fetch(`http://localhost:8000/api/v1/import_sessions/${sessionId}/storage-name`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					storage_name: `imalink_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}_${Math.random().toString(36).substring(2, 8)}`
				})
			});

			if (!storageNameResponse.ok) {
				error = 'Kunne ikke generere storage-navn';
				return;
			}

			const storageData = await storageNameResponse.json();
			const storageName = storageData.storage_name;

			// Steg 4: Opprett storage-katalog
			progressInfo = `Oppretter storage-katalog: ${storageName}`;
			const storageDirectoryHandle = await storageRootHandle!.getDirectoryHandle(storageName, { create: true });

			// Steg 5: Kopier alle filer til storage-katalog  
			progressInfo = 'Kopierer filer til permanent storage...';
			let copiedCount = 0;
			let errorCount = 0;

			for (const imageFile of imageFiles as any[]) {
				try {
					// Les filen fra import-katalog
					const fileData = await imageFile.handle.getFile();
					
					// Opprett filen i storage-katalog
					const targetFileHandle = await storageDirectoryHandle.getFileHandle(imageFile.name, { create: true });
					const writable = await targetFileHandle.createWritable();
					
					// Kopier filinnhold
					await writable.write(fileData);
					await writable.close();
					
					copiedCount++;
					progressInfo = `Kopierer filer: ${copiedCount}/${imageFiles.length}`;
				} catch (copyError: any) {
					console.error(`Feil ved kopiering av ${imageFile.name}:`, copyError);
					errorCount++;
				}
			}
			
			importResults = {
				id: sessionId,
				status: 'completed',
				source_path: `Frontend: ${importDirectoryHandle.name}`,
				total_files_found: imageFiles.length,
				files_copied: copiedCount,
				copy_errors: errorCount,
				created_at: new Date().toISOString(),
				storage_name: storageName
			};
			
			// Steg 6: Send filmetadata til backend for databaselagring
			progressInfo = 'Sender metadata til backend...';
			
			// Prosesser filene for å lage metadata
			const photoGroups: any[] = [];
			for (const imageFile of imageFiles as any[]) {
				try {
					const file = await imageFile.handle.getFile();
					
					// Generer hothash basert på filnavn og størrelse  
					const hothash = btoa(`${imageFile.name}_${file.size}_${file.lastModified}`).substring(0, 32);
					
					// Opprett PhotoGroup med grunnleggende metadata
					photoGroups.push({
						hothash: hothash,
						width: null, // Kan ekstraheres fra EXIF senere
						height: null,
						taken_at: new Date(file.lastModified).toISOString(),
						title: imageFile.name,
						import_session_id: sessionId,
						images: [{
							filename: imageFile.name,
							hothash: hothash,
							file_size: file.size,
							import_session_id: sessionId
						}]
					});
				} catch (metaError: any) {
					console.error(`Feil ved metadata-generering for ${imageFile.name}:`, metaError);  
				}
			}

			// Send batch til backend
			if (photoGroups.length > 0) {
				try {
					const batchResponse = await fetch('http://localhost:8000/api/v1/photos/batch', {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json'
						},
						body: JSON.stringify({
							photo_groups: photoGroups,
							author_id: selectedAuthorId || null
						})
					});

					if (!batchResponse.ok) {
						console.error('Backend batch import feilet:', await batchResponse.text());
						error = 'Metadata-lagring feilet i backend';
						return;
					}

					const batchResult = await batchResponse.json();
					console.log('Backend batch result:', batchResult);
				} catch (batchError: any) {
					console.error('Feil ved sending av metadata:', batchError);
					error = `Metadata-sending feilet: ${batchError.message}`;
					return;
				}
			}
			
			progressInfo = `Import fullført! ${copiedCount} filer kopiert til ${storageName}, metadata lagret i database`;
			if (errorCount > 0) {
				progressInfo += ` (${errorCount} kopieringsfeil)`;
			}

		} catch (err: any) {
			error = `Import feil: ${err.message}`;
		} finally {
			importing = false;
		}
	}
</script>

<svelte:head>
	<title>Import - ImaLink</title>
</svelte:head>

<div class="import-container">
	<div class="header">
		<h1>📥 Import Photos</h1>
		<p>Import photos from your computer using the new storage system</p>
	</div>

	{#if error}
		<div class="error-message">
			❌ {error}
		</div>
	{/if}

	{#if !isApiSupported}
		<div class="warning-message">
			⚠️ File System Access API ikke støttet i denne nettleseren.
			Bruk Chrome 86+ eller Edge 86+ med HTTPS for full funksjonalitet.
		</div>
	{/if}

	<div class="import-form">
		<div class="form-section">
			<h3>📁 Import Directory</h3>
			<div class="directory-selector">
				<div class="directory-info">
					<span class="directory-path">{importDirectoryPath}</span>
				</div>
				<button 
					class="select-dir-btn"
					on:click={selectImportDirectory}
					disabled={importing || !isApiSupported}
				>
					📂 Velg katalog
				</button>
			</div>
			<p class="help-text">Katalog som inneholder bildene som skal importeres</p>
		</div>

		<div class="form-section">
			<h3>💾 Storage Root</h3>
			<div class="directory-selector">
				<div class="directory-info">
					<span class="directory-path">{storageRootPath}</span>
				</div>
				<button 
					class="select-dir-btn"
					on:click={selectStorageRoot}
					disabled={importing || !isApiSupported}
				>
					📂 Velg katalog
				</button>
			</div>
			<p class="help-text">Hvor import-katalogen vil bli opprettet med unikt navn</p>
		</div>

		<div class="form-section">
			<h3>👤 Author (Optional)</h3>
			<select bind:value={selectedAuthorId} disabled={importing} class="author-select">
				<option value="">No author</option>
				{#each authors as author}
					<option value="{author.id}">{author.name}</option>
				{/each}
			</select>
		</div>

		<div class="action-buttons">
			<button
				class="import-button"
				disabled={importing || !importDirectoryHandle || !storageRootHandle || !isApiSupported}
				on:click={startImport}
			>
				{#if importing}
					🔄 Importerer...
				{:else}
					📥 Start Frontend Import
				{/if}
			</button>
		</div>
	</div>

	{#if progressInfo}
		<div class="progress-info">
			ℹ️ {progressInfo}
		</div>
	{/if}

	{#if importResults}
		<div class="results-section">
			<h3>✅ Import Results</h3>
			<div class="results-grid">
				<div class="result-item">
					<strong>Session ID:</strong> {importResults.id}
				</div>
				<div class="result-item">
					<strong>Status:</strong> {importResults.status}
				</div>
				<div class="result-item">
					<strong>Source:</strong> {importResults.source_path}
				</div>
				<div class="result-item">
					<strong>Storage Directory:</strong> {importResults.storage_directory_name || importResults.storage_name || 'Not generated'}
				</div>
				<div class="result-item">
					<strong>Files Found:</strong> {importResults.total_files_found || 0}
				</div>
				<div class="result-item">
					<strong>Images Imported:</strong> {importResults.images_imported || 0}
				</div>
				{#if importResults.duplicates_skipped > 0}
				<div class="result-item">
					<strong>Duplicates Skipped:</strong> {importResults.duplicates_skipped}
				</div>
				{/if}
				<div class="result-item">
					<strong>Started:</strong> {importResults.started_at ? new Date(importResults.started_at).toLocaleString() : 'Unknown'}
				</div>
				<div class="result-item">
					<strong>Completed:</strong> {importResults.completed_at ? new Date(importResults.completed_at).toLocaleString() : 'In progress'}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.import-container {
		max-width: 800px;
		margin: 0 auto;
		padding: var(--spacing-xl);
	}

	.header {
		text-align: center;
		margin-bottom: var(--spacing-xl);
	}

	.header h1 {
		color: var(--color-gray-800);
		margin-bottom: var(--spacing-sm);
		font-weight: var(--font-weight-bold);
	}

	.header p {
		color: var(--color-gray-500);
		font-size: var(--font-size-lg);
	}

	.error-message {
		background: var(--bg-error);
		border: 1px solid var(--border-error);
		color: var(--color-error);
		padding: var(--spacing-md);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-lg);
	}

	.import-form {
		background: var(--color-gray-50);
		border: 1px solid var(--border-light);
		border-radius: var(--radius-xl);
		padding: var(--spacing-xl);
		margin-bottom: var(--spacing-lg);
	}

	.form-section {
		margin-bottom: var(--spacing-lg);
	}

	.form-section h3 {
		margin: 0 0 var(--spacing-sm) 0;
		color: var(--color-gray-700);
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
	}



	.author-select {
		width: 100%;
		padding: var(--spacing-sm);
		border: 1px solid var(--border-medium);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-sm);
		background: var(--bg-card);
		transition: border-color var(--transition-normal);
	}

	.author-select:disabled {
		background: var(--color-gray-100);
		cursor: not-allowed;
	}

	.help-text {
		margin-top: var(--spacing-sm);
		font-size: var(--font-size-xs);
		color: var(--color-gray-500);
		font-style: italic;
	}

	.warning-message {
		background: var(--color-yellow-50);
		border: 1px solid var(--color-yellow-300);
		color: var(--color-yellow-800);
		padding: var(--spacing-md);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-lg);
		text-align: center;
	}

	.directory-selector {
		display: flex;
		gap: var(--spacing-md);
		align-items: center;
		flex-wrap: wrap;
	}

	.directory-info {
		flex: 1;
		min-width: 200px;
	}

	.directory-path {
		display: block;
		padding: var(--spacing-md);
		background: var(--color-gray-50);
		border: 1px solid var(--border-light);
		border-radius: var(--radius-lg);
		font-family: monospace;
		font-size: var(--font-size-sm);
		color: var(--color-gray-700);
	}

	.select-dir-btn {
		background: var(--color-blue-500);
		color: white;
		border: none;
		padding: var(--spacing-md) var(--spacing-lg);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		cursor: pointer;
		transition: all var(--transition-normal);
		white-space: nowrap;
	}

	.select-dir-btn:hover:not(:disabled) {
		background: var(--color-blue-600);
		transform: translateY(-1px);
	}

	.select-dir-btn:disabled {
		background: var(--color-gray-400);
		cursor: not-allowed;
		transform: none;
	}

	.action-buttons {
		text-align: center;
		margin-top: var(--spacing-xl);
	}

	.import-button {
		background: var(--color-primary);
		color: white;
		border: none;
		padding: var(--spacing-md) var(--spacing-xl);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		cursor: pointer;
		transition: all var(--transition-normal);
	}

	.import-button:hover:not(:disabled) {
		background: var(--color-primary-hover);
		transform: translateY(-1px);
	}

	.import-button:disabled {
		background: var(--color-gray-400);
		cursor: not-allowed;
		transform: none;
	}

	.progress-info {
		background: var(--bg-info);
		border: 1px solid var(--border-info);
		color: var(--color-primary-hover);
		padding: var(--spacing-md);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-lg);
		text-align: center;
	}

	.results-section {
		background: var(--bg-success);
		border: 1px solid var(--border-success);
		border-radius: var(--radius-xl);
		padding: var(--spacing-lg);
	}

	.results-section h3 {
		margin: 0 0 var(--spacing-md) 0;
		color: var(--color-success-hover);
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
	}

	.results-grid {
		display: grid;
		gap: var(--spacing-sm);
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	}

	.result-item {
		background: var(--bg-card);
		padding: var(--spacing-sm);
		border-radius: var(--radius-lg);
		border: 1px solid var(--border-success);
		font-size: var(--font-size-sm);
	}

	.result-item strong {
		color: var(--color-success-hover);
	}
</style>