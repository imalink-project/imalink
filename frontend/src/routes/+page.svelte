<script lang="ts">
import { onMount } from 'svelte';
import { currentView } from '$lib/stores/app';

currentView.set('photos');

let photos = [];
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
error = err.message || 'Failed to load photos';
} finally {
loading = false;
}
}
</script>

<div class="photos-page">
<div class="page-header">
<h1>📸 Photos</h1>
<p>Browse your photo collection</p>
<button on:click={loadPhotos} class="btn btn-primary">🔄 Refresh</button>
</div>

{#if loading}
<div class="loading">
<div class="spinner"></div>
<p>Loading photos...</p>
</div>
{:else if error}
<div class="error">
<p>❌ {error}</p>
<button on:click={loadPhotos} class="btn btn-primary">Try Again</button>
</div>
{:else if photos.length === 0}
<div class="empty-state">
<h3>📋 No photos found</h3>
<p>Import some photos to get started!</p>
<a href="/import" class="import-link">Go to Import</a>
</div>
{:else}
<div class="photos-grid">
{#each photos as photo}
<div class="photo-card">
{#if photo.hotpreview}
<img 
src="data:image/jpeg;base64,{photo.hotpreview}" 
alt={photo.primary_filename || photo.hothash}
class="photo-thumbnail"
/>
{:else}
<div class="photo-placeholder">
📸
</div>
{/if}

<div class="photo-info">
<h4 class="photo-filename">{photo.primary_filename || photo.hothash}</h4>

{#if photo.taken_at}
<p class="photo-date">📅 {new Date(photo.taken_at).toLocaleDateString()} {new Date(photo.taken_at).toLocaleTimeString()}</p>
{/if}

{#if photo.title}
<p class="photo-title">📝 {photo.title}</p>
{/if}

{#if photo.description}
<p class="photo-description">📄 {photo.description}</p>
{/if}

{#if photo.author?.name}
<p class="photo-author">👤 {photo.author.name}</p>
{/if}

{#if photo.width && photo.height}
<p class="photo-dimensions">📐 {photo.width} × {photo.height}px</p>
{/if}

{#if photo.rating > 0}
<p class="photo-rating">⭐ {'★'.repeat(photo.rating)}{'☆'.repeat(5 - photo.rating)}</p>
{/if}

{#if photo.has_gps}
<p class="photo-gps">📍 GPS: {photo.gps_latitude?.toFixed(4)}, {photo.gps_longitude?.toFixed(4)}</p>
{/if}

{#if photo.has_raw_companion}
<p class="photo-raw">📸 RAW + JPEG</p>
{/if}

{#if photo.files && photo.files.length > 0}
<p class="photo-files">📁 {photo.files.length} file{photo.files.length > 1 ? 's' : ''}</p>
{/if}

{#if photo.tags && photo.tags.length > 0}
<p class="photo-tags">🏷️ {photo.tags.join(', ')}</p>
{/if}

<p class="photo-imported">⏰ Imported {new Date(photo.created_at).toLocaleDateString()}</p>
</div>
</div>
{/each}
</div>
{/if}
</div>

<style>
.photos-page {
padding: var(--spacing-xl);
max-width: 1200px;
margin: 0 auto;
}

.page-header {
text-align: center;
margin-bottom: var(--spacing-xl);
}

.page-header h1 {
font-size: var(--font-size-3xl);
margin: 0 0 var(--spacing-sm) 0;
color: var(--color-gray-800);
font-weight: var(--font-weight-bold);
}

.page-header p {
font-size: var(--font-size-lg);
color: var(--color-gray-500);
margin: 0 0 var(--spacing-md) 0;
}

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

.photos-grid {
display: grid;
grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
gap: var(--spacing-lg);
margin-top: var(--spacing-xl);
}

.photo-card {
background: var(--bg-card);
border-radius: var(--radius-lg);
overflow: hidden;
box-shadow: var(--shadow-md);
transition: transform var(--transition-normal), box-shadow var(--transition-normal);
}

.photo-card:hover {
transform: translateY(-2px);
box-shadow: var(--shadow-xl);
}

.photo-thumbnail {
width: 100%;
height: 200px;
object-fit: cover;
}

.photo-placeholder {
width: 100%;
height: 200px;
display: flex;
align-items: center;
justify-content: center;
background: var(--color-gray-100);
font-size: var(--font-size-3xl);
color: var(--color-gray-400);
}

.photo-info {
padding: var(--spacing-md);
}

.photo-filename {
margin: 0 0 var(--spacing-sm) 0;
font-size: var(--font-size-base);
font-weight: var(--font-weight-semibold);
color: var(--color-gray-800);
word-break: break-word;
}

.photo-date, .photo-title, .photo-description, .photo-author, .photo-dimensions, 
.photo-rating, .photo-gps, .photo-raw, .photo-files, .photo-tags, .photo-imported {
margin: var(--spacing-xs) 0;
font-size: var(--font-size-sm);
color: var(--color-gray-500);
line-height: var(--line-height-normal);
}

.photo-rating {
color: var(--color-warning);
font-weight: var(--font-weight-medium);
}

.photo-gps {
color: var(--color-success-hover);
font-family: monospace;
}

.photo-raw {
color: var(--color-purple);
font-weight: var(--font-weight-medium);
}

.photo-imported {
color: var(--color-gray-400);
font-size: var(--font-size-xs);
margin-top: var(--spacing-sm);
padding-top: var(--spacing-sm);
border-top: 1px solid var(--border-light);
}
</style>
