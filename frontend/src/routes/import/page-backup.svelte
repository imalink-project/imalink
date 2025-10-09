<script lang="ts">
	import { onMount } from 'svelte';
	import { currentView } from '$lib/stores/app';
	import FileStatusPanel from '$lib/components/FileStatusPanel.svelte';

	currentView.set('import');

	let importing = false;
	let scanning = false;
	let importResults = null;
	let scanResults = null;
	let processResults = null;
	let error = '';
	let authors = [];
	let selectedAuthorId = '';
	let progressInfo = '';
	let importDirectory = '';
	let storageRoot = '';
	let currentImportSession = null;

	onMount(async () => {
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
		}
	}

	async function scanDirectory() {
		scanning = true;
		error = '';
		scanResults = null;
		processResults = null;
		importResults = null;
		progressInfo = '';

		try {
			progressInfo = 'Opening directory picker...';
			
			// Check if File System Access API is supported
			if (!window.showDirectoryPicker) {
				throw new Error('File System Access API not supported. Please use a modern browser like Chrome 86+');
			}
			
			// Show directory picker
			const dirHandle = await window.showDirectoryPicker();
			
			progressInfo = 'Scanning directory...';
			
			const imageFiles = [];
			const supportedExtensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2'];
			
			// Scan directory recursively
			await scanDirectoryRecursive(dirHandle, '', imageFiles, supportedExtensions);
			
			// Detect JPEG/RAW pairs
			const photoPairs = detectPhotoPairs(imageFiles);
			
			scanResults = {
				directory: dirHandle.name,
				total_files: imageFiles.length,
				image_files: imageFiles,
				photo_pairs: photoPairs
			};
			
			progressInfo = `Found ${imageFiles.length} image files, detected ${photoPairs.length} photo groups`;
			
		} catch (err) {
			console.error('Scan failed:', err);
			if (err.name === 'AbortError') {
				error = 'Directory selection was cancelled';
			} else {
				error = err.message || 'Directory scan failed';
			}
		} finally {
			scanning = false;
		}
	}

	async function scanDirectoryRecursive(dirHandle, path, imageFiles, supportedExtensions) {
		for await (const [name, handle] of dirHandle.entries()) {
			const fullPath = path ? `${path}/${name}` : name;
			
			if (handle.kind === 'file') {
				const ext = name.substring(name.lastIndexOf('.')).toLowerCase();
				if (supportedExtensions.includes(ext)) {
					const file = await handle.getFile();
					
					imageFiles.push({
						path: fullPath,
						filename: name,
						size: file.size,
						category: getFileCategory(name),
						extension: ext,
						base_name: getBaseName(name),
						fileHandle: handle,
						file: file
					});
				}
			} else if (handle.kind === 'directory') {
				// Recursive scan
				await scanDirectoryRecursive(handle, fullPath, imageFiles, supportedExtensions);
			}
		}
	}

	function getFileCategory(filename) {
		const ext = filename.substring(filename.lastIndexOf('.')).toLowerCase();
		const categories = {
			jpeg: ['.jpg', '.jpeg'],
			raw: ['.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2'],
			other: ['.png', '.tiff', '.tif']
		};
		
		for (const [category, extensions] of Object.entries(categories)) {
			if (extensions.includes(ext)) return category;
		}
		return 'unknown';
	}

	function getBaseName(filename) {
		return filename.substring(0, filename.lastIndexOf('.'));
	}

	function detectPhotoPairs(imageFiles) {
		const filesByBase = {};
		
		// Group by base name
		for (const file of imageFiles) {
			const baseName = file.base_name;
			if (!filesByBase[baseName]) {
				filesByBase[baseName] = { jpeg: null, raw: null, other: [] };
			}
			
			if (file.category === 'jpeg') {
				filesByBase[baseName].jpeg = file;
			} else if (file.category === 'raw') {
				filesByBase[baseName].raw = file;
			} else {
				filesByBase[baseName].other.push(file);
			}
		}
		
		// Create pairs
		const pairs = [];
		for (const [baseName, files] of Object.entries(filesByBase)) {
			const { jpeg, raw, other } = files;
			
			let type;
			if (jpeg && raw) type = 'jpeg_raw_pair';
			else if (jpeg) type = 'single_jpeg';
			else if (raw) type = 'single_raw';
			else type = 'other';
			
			pairs.push({
				base_name: baseName,
				jpeg_file: jpeg,
				raw_file: raw,
				type: type
			});
			
			// Handle other files as separate singles
			for (const otherFile of other) {
				pairs.push({
					base_name: otherFile.base_name,
					jpeg_file: otherFile.category === 'jpeg' ? otherFile : null,
					raw_file: otherFile.category === 'raw' ? otherFile : null,
					type: 'single_other'
				});
			}
		}
		
		return pairs;
	}

	async function processImages() {
		if (!scanResults || scanResults.photo_pairs.length === 0) {
			alert('No photos to process. Please scan a directory first.');
			return;
		}

		processing = true;
		error = '';
		processResults = null;
		importResults = null;
		progressInfo = '';

		try {
			progressInfo = 'Processing images...';
			
			const processedPhotos = [];
			const total = scanResults.photo_pairs.length;
			
			for (let i = 0; i < scanResults.photo_pairs.length; i++) {
				const pair = scanResults.photo_pairs[i];
				progressInfo = `Processing ${i + 1}/${total}: ${pair.base_name}`;
				
				const processedPair = {
					base_name: pair.base_name,
					type: pair.type,
					jpeg_file: null,
					raw_file: null,
					exif_data: null,
					thumbnail: null,
					error: null
				};
				
				try {
					// Process JPEG file if exists
					if (pair.jpeg_file) {
						const jpegData = await processImageFile(pair.jpeg_file);
						processedPair.jpeg_file = jpegData;
						processedPair.exif_data = jpegData.exif;
						processedPair.thumbnail = jpegData.thumbnail;
					}
					
					// Process RAW file if exists
					if (pair.raw_file) {
						const rawData = await processImageFile(pair.raw_file);
						processedPair.raw_file = rawData;
						
						// Use RAW EXIF if no JPEG EXIF
						if (!processedPair.exif_data) {
							processedPair.exif_data = rawData.exif;
						}
					}
					
				} catch (err) {
					console.error(`Error processing ${pair.base_name}:`, err);
					processedPair.error = err.message;
				}
				
				processedPhotos.push(processedPair);
			}
			
			processResults = {
				processed_count: processedPhotos.length,
				processed_photos: processedPhotos,
				success_count: processedPhotos.filter(p => !p.error).length,
				error_count: processedPhotos.filter(p => p.error).length
			};
			
			progressInfo = `Processed ${processResults.processed_count} photos (${processResults.success_count} successful, ${processResults.error_count} errors)`;
			
		} catch (err) {
			console.error('Processing failed:', err);
			error = err.message || 'Image processing failed';
		} finally {
			processing = false;
		}
	}

	async function processImageFile(imageFile) {
		const file = imageFile.file;
		
		// Extract EXIF data
		let exifData = null;
		try {
			exifData = await extractExif(file);
		} catch (err) {
			console.warn(`Failed to extract EXIF from ${imageFile.filename}:`, err);
		}
		
		// Generate thumbnail for JPEG files
		let thumbnail = null;
		if (imageFile.category === 'jpeg') {
			try {
				thumbnail = await generateThumbnail(file);
			} catch (err) {
				console.warn(`Failed to generate thumbnail for ${imageFile.filename}:`, err);
			}
		}
		
		return {
			path: imageFile.path,
			filename: imageFile.filename,
			size: imageFile.size,
			category: imageFile.category,
			exif: exifData,
			thumbnail: thumbnail
		};
	}

	async function extractExif(file) {
		// Basic EXIF extraction - you might want to use a library like exif-js or piexifjs
		return new Promise((resolve) => {
			const reader = new FileReader();
			reader.onload = function(e) {
				const arrayBuffer = e.target.result;
				const dataView = new DataView(arrayBuffer);
				
				// Simple EXIF extraction (basic implementation)
				// This is a simplified version - for production use a proper EXIF library
				const exif = {
					fileSize: file.size,
					lastModified: new Date(file.lastModified),
					type: file.type
				};
				
				resolve(exif);
			};
			reader.readAsArrayBuffer(file.slice(0, 65536)); // Read first 64KB for EXIF
		});
	}

	async function generateThumbnail(file) {
		return new Promise((resolve, reject) => {
			const img = new Image();
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');
			
			img.onload = function() {
				// Calculate thumbnail size (max 200px)
				const maxSize = 200;
				let { width, height } = img;
				
				if (width > height) {
					if (width > maxSize) {
						height *= maxSize / width;
						width = maxSize;
					}
				} else {
					if (height > maxSize) {
						width *= maxSize / height;
						height = maxSize;
					}
				}
				
				canvas.width = width;
				canvas.height = height;
				
				ctx.drawImage(img, 0, 0, width, height);
				
				// Convert to base64
				const thumbnailData = canvas.toDataURL('image/jpeg', 0.8);
				resolve(thumbnailData);
			};
			
			img.onerror = reject;
			img.src = URL.createObjectURL(file);
		});
	}	async function generateThumbnailFromBlob(blob) {
		return new Promise((resolve, reject) => {
			const img = new Image();
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');
			
			img.onload = function() {
				// Calculate thumbnail size
				const maxSize = 300;
				let { width, height } = img;
				
				if (width > height) {
					if (width > maxSize) {
						height = height * (maxSize / width);
						width = maxSize;
					}
				} else {
					if (height > maxSize) {
						width = width * (maxSize / height);
						height = maxSize;
					}
				}
				
				canvas.width = width;
				canvas.height = height;
				ctx.drawImage(img, 0, 0, width, height);
				
				// Convert to base64
				const base64 = canvas.toDataURL('image/jpeg', 0.8);
				const base64Data = base64.split(',')[1];
				
				resolve(base64Data);
			};
			
			img.onerror = () => reject(new Error('Failed to load image'));
			img.src = URL.createObjectURL(blob);
		});
	}

	// DEPRECATED: This function uses old individual Photo/Image creation
	// TODO: Replace with batch import using File System Access API and POST /photos/batch
	async function importToDatabase() {
		if (!processResults || processResults.processed_count === 0) {
			alert('No processed photos to import. Please process images first.');
			return;
		}

		importing = true;
		error = '';
		importResults = null;
		progressInfo = '';

		try {
			progressInfo = 'Importing to database...';
			
			const importedPhotos = [];
			const failedImports = [];
			const total = processResults.processed_photos.length;
			
			for (let i = 0; i < processResults.processed_photos.length; i++) {
				const photo = processResults.processed_photos[i];
				progressInfo = `Importing ${i + 1}/${total}: ${photo.base_name}`;
				
				try {
					// Skip photos with errors
					if (photo.error) {
						failedImports.push({
							base_name: photo.base_name,
							error: photo.error
						});
						continue;
					}
					
					// Determine primary file for database record
					const primaryFile = photo.jpeg_file || photo.raw_file;
					if (!primaryFile) {
						failedImports.push({
							base_name: photo.base_name,
							error: 'No valid image file found'
						});
						continue;
					}
					
					// Extract dimensions and date from EXIF if available
					const exif = photo.exif_data || {};
					
					// Generate consistent hothash using backend authority
					const hothash = await generateConsistentHash(
						primaryFile.filename,
						primaryFile.size,
						exif.width,
						exif.height
					);
					
					// Build all image files for this photo
					const images = [];
					if (photo.jpeg_file) {
						images.push({
							filename: photo.jpeg_file.filename,
							hothash: hothash,
							file_size: photo.jpeg_file.size,
							exif_data: JSON.stringify(exif),
							import_session_id: null
						});
					}
					if (photo.raw_file) {
						images.push({
							filename: photo.raw_file.filename,
							hothash: hothash,
							file_size: photo.raw_file.size,
							exif_data: JSON.stringify(exif),
							import_session_id: null
						});
					}
					
					// Use new Photos batch API for single photo
					const photoGroup = {
						hothash: hothash,
						hotpreview: photo.thumbnail || null,
						width: exif.width || null,
						height: exif.height || null,
						taken_at: exif.dateTime || null,
						gps_latitude: exif.gpsLatitude || null,
						gps_longitude: exif.gpsLongitude || null,
						title: null,
						description: null,
						tags: null,
						rating: 0,
						user_rotation: 0,
						import_session_id: null,
						images: images
					};
					
					const batchRequest = {
						photo_groups: [photoGroup],
						author_id: selectedAuthorId || null
					};
					
					const response = await fetch('http://localhost:8000/api/v1/photos/batch', {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json'
						},
						body: JSON.stringify(batchRequest)
					});
					
					if (response.ok) {
						const batchResult = await response.json();
						if (batchResult.success && batchResult.results.length > 0 && batchResult.results[0].success) {
							importedPhotos.push({
								base_name: photo.base_name,
								type: photo.type,
								photo_id: batchResult.results[0].photo.hothash,
								filename: primaryFile.filename
							});
						} else {
							throw new Error(batchResult.results[0]?.error || 'Batch import failed');
						}
					} else {
						const errorText = await response.text();
						throw new Error(`HTTP ${response.status}: ${errorText}`);
					}
					
				} catch (err) {
					console.error(`Failed to import ${photo.base_name}:`, err);
					failedImports.push({
						base_name: photo.base_name,
						error: err.message
					});
				}
			}
			
			importResults = {
				imported_count: importedPhotos.length,
				failed_count: failedImports.length,
				imported_photos: importedPhotos,
				failed_imports: failedImports
			};
			
			progressInfo = `Import completed: ${importResults.imported_count} successful, ${importResults.failed_count} failed`;
			
		} catch (err) {
			console.error('Import failed:', err);
			error = err.message || 'Database import failed';
		} finally {
			importing = false;
		}
	}

	function reset() {
		scanResults = null;
		processResults = null;
		importResults = null;
		error = '';
		selectedAuthorId = '';
		progressInfo = '';
	}
</script>

<div class="import-page">
	<div class="page-header">
		<h1>📥 Import</h1>
		<p>Import images directly from your computer using browser JavaScript</p>
		<button onclick={reset} class="reset-btn">🔄 Reset</button>
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

	<!-- Step 1: Directory Scanning -->
	<div class="step-card">
		<h3>📁 Step 1: Scan Directory</h3>
		<p>Select a directory using your browser's directory picker (Chrome 86+)</p>
		<div class="input-group">
			<button 
				onclick={scanDirectory} 
				disabled={scanning}
				class="scan-btn"
			>
				{#if scanning}
					<div class="spinner-small"></div> Scanning...
				{:else}
					� Pick Directory
				{/if}
			</button>
		</div>
		
		{#if scanResults}
			<div class="results">
				<p class="success">✅ Found {scanResults.total_files} image files</p>
				<p class="info">📸 Detected {scanResults.photo_pairs.length} photo groups (singles and JPEG/RAW pairs)</p>
				{#if scanResults.image_files.length > 0}
					<div class="file-list">
						{#each scanResults.image_files.slice(0, 5) as file}
							<p class="file-item">📸 {file.filename} ({Math.round(file.size / 1024)} KB, {file.category})</p>
						{/each}
						{#if scanResults.image_files.length > 5}
							<p class="more-files">... and {scanResults.image_files.length - 5} more files</p>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Step 2: Image Processing -->
	<div class="step-card" class:disabled={!scanResults?.photo_pairs?.length}>
		<h3>⚙️ Step 2: Process Images</h3>
		<p>Extract EXIF metadata and create thumbnails</p>
		<button 
			onclick={processImages}
			disabled={processing || !scanResults?.photo_pairs?.length}
			class="process-btn"
		>
			{#if processing}
				<div class="spinner-small"></div> Processing...
			{:else}
				⚙️ Process Images
			{/if}
		</button>
		
		{#if processResults}
			<div class="results">
				<p class="success">✅ Processed {processResults.processed_count} photos</p>
				<p class="info">✅ Successful: {processResults.success_count}</p>
				{#if processResults.error_count > 0}
					<p class="warning">⚠️ Errors: {processResults.error_count}</p>
					<div class="failed-list">
						{#each processResults.processed_photos.filter(p => p.error) as failed}
							<p class="failed-item">❌ {failed.base_name}: {failed.error}</p>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Step 3: Database Import -->
	<div class="step-card" class:disabled={!processResults?.processed_count}>
		<h3>💾 Step 3: Import to Database</h3>
		<div class="author-selection">
			<label for="author-select">Assign to Author (optional):</label>
			<select id="author-select" bind:value={selectedAuthorId}>
				<option value="">No author</option>
				{#each authors as author}
					<option value={author.id}>{author.name}</option>
				{/each}
			</select>
		</div>
		<button 
			onclick={importToDatabase}
			disabled={importing || !processResults?.processed_count}
			class="import-btn"
		>
			{#if importing}
				<div class="spinner-small"></div> Importing...
			{:else}
				💾 Import to Database
			{/if}
		</button>
		
		{#if importResults}
			<div class="results">
				{#if importResults.imported_count > 0}
					<p class="success">✅ Successfully imported {importResults.imported_count} photos</p>
				{/if}
				{#if importResults.failed_count > 0}
					<p class="warning">⚠️ Failed to import {importResults.failed_count} photos</p>
					<div class="failed-list">
						{#each importResults.failed_imports as failed}
							<p class="failed-item">❌ {failed.base_name}: {failed.error}</p>
						{/each}
					</div>
				{/if}
				<p class="completion">🎉 Import finished! <a href="/">View Photos</a></p>
			</div>
		{/if}
	</div>
</div>

<style>
	.import-page {
		max-width: 800px;
		margin: 0 auto;
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
		transition: opacity 0.2s ease;
	}

	.step-card.disabled {
		opacity: 0.5;
	}

	.step-card h3 {
		margin: 0 0 1rem 0;
		color: #1f2937;
		font-size: 1.25rem;
	}

	.input-group {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.path-input {
		flex: 1;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 1rem;
	}

	.path-input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 1px #3b82f6;
	}

	.scan-btn, .process-btn, .import-btn {
		background: #3b82f6;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		cursor: pointer;
		font-weight: 500;
		transition: background-color 0.2s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		white-space: nowrap;
	}

	.scan-btn:hover, .process-btn:hover, .import-btn:hover {
		background: #2563eb;
	}

	.scan-btn:disabled, .process-btn:disabled, .import-btn:disabled {
		background: #9ca3af;
		cursor: not-allowed;
	}

	.author-selection {
		margin-bottom: 1rem;
	}

	.author-selection label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #374151;
	}

	.author-selection select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 1rem;
		background: white;
	}

	.author-selection select:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 1px #3b82f6;
	}

	.input-group {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.path-input {
		flex: 1;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 1rem;
	}

	.path-input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 1px #3b82f6;
	}

	.spinner-small {
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

	.results {
		margin-top: 1rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 0.375rem;
		border-left: 4px solid #3b82f6;
	}

	.success {
		color: #059669;
		font-weight: 500;
		margin: 0 0 0.5rem 0;
	}

	.info {
		color: #0369a1;
		margin: 0 0 0.5rem 0;
	}

	.warning {
		color: #d97706;
		margin: 0 0 0.5rem 0;
	}

	.completion {
		color: #059669;
		font-weight: 500;
		margin: 0.5rem 0 0 0;
	}

	.completion a {
		color: #3b82f6;
		text-decoration: none;
	}

	.completion a:hover {
		text-decoration: underline;
	}

	.file-list {
		margin-top: 0.5rem;
	}

	.file-item {
		margin: 0.25rem 0;
		font-size: 0.875rem;
		color: #6b7280;
		font-family: monospace;
	}

	.more-files {
		margin: 0.25rem 0;
		font-size: 0.875rem;
		color: #9ca3af;
		font-style: italic;
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

	.failed-list {
		margin-top: 0.5rem;
	}

	.failed-item {
		margin: 0.25rem 0;
		font-size: 0.875rem;
		color: #dc2626;
		font-family: monospace;
	}
</style>