<script lang="ts">
import { onMount } from 'svelte';
import { currentView } from '$lib/stores/app';
import { Button, PageHeader } from '$lib/components/ui';
import PhotoGrid from '$lib/components/domain/PhotoGrid.svelte';

currentView.set('photos');

let photos: any[] = [];
let loading = true;
let error = '';

onMount(async () => {
await loadPhotos();
});

async function loadPhotos() {
loading = true;
error = '';

try {
const response = await fetch('http://localhost:8000/api/v1/photos/');
if (!response.ok) {
throw new Error(`HTTP ${response.status}: ${response.statusText}`);
}

const data = await response.json();
photos = data.data || [];
} catch (err) {
console.error('Failed to load photos:', err);
error = err instanceof Error ? err.message : 'Failed to load photos';
} finally {
loading = false;
}
}
</script>

<div class="photos-page">
	<PageHeader 
		title="Photos" 
		icon="📸"
		description="Browse your photo collection"
	>
		<Button variant="primary" onclick={loadPhotos}>🔄 Refresh</Button>
	</PageHeader>{#if loading}
<div class="loading">
<div class="spinner"></div>
<p>Loading photos...</p>
</div>
{:else if error}
<div class="error">
<p>❌ {error}</p>
<Button variant="primary" onclick={loadPhotos}>Try Again</Button>
</div>
{:else if photos.length === 0}
<div class="empty-state">
<h3>📋 No photos found</h3>
<p>Import some photos to get started!</p>
<a href="/import" class="import-link">Go to Import</a>
</div>
{:else}
<PhotoGrid 
	{photos}
	layout="grid"
	cardVariant="grid"
	showActions={false}
/>
{/if}
</div>

<style>
.photos-page {
padding: var(--spacing-xl);
max-width: 1200px;
margin: 0 auto;
}

/* Page header styling now handled by PageHeader component */

/* Buttons now use global utility classes */

.loading {
text-align: center;
padding: var(--spacing-2xl);
}

.spinner {
width: 40px;
height: 40px;
border: 4px solid var(--color-gray-200);
border-top: 4px solid var(--color-primary);
border-radius: var(--radius-full);
animation: spin 1s linear infinite;
margin: 0 auto var(--spacing-md) auto;
}

@keyframes spin {
0% { transform: rotate(0deg); }
100% { transform: rotate(360deg); }
}

.error {
text-align: center;
padding: var(--spacing-2xl);
color: var(--color-error);
}

.empty-state {
text-align: center;
padding: var(--spacing-2xl);
}

.empty-state h3 {
font-size: var(--font-size-2xl);
margin: 0 0 var(--spacing-md) 0;
color: var(--color-gray-700);
}

.empty-state p {
color: var(--color-gray-500);
margin: 0 0 var(--spacing-lg) 0;
}

.import-link {
display: inline-block;
background: var(--color-success);
color: white;
text-decoration: none;
padding: var(--spacing-sm) var(--spacing-lg);
border-radius: var(--radius-lg);
font-weight: var(--font-weight-medium);
transition: background-color var(--transition-normal);
}

.import-link:hover {
background: var(--color-success-hover);
}

/* Photo grid and card styling now handled by PhotoGrid and PhotoCard components */
</style>
