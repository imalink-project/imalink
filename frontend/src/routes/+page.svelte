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
<button on:click={loadPhotos} class="refresh-btn">🔄 Refresh</button>
</div>

{#if loading}
<div class="loading">
<div class="spinner"></div>
<p>Loading photos...</p>
</div>
{:else if error}
<div class="error">
<p>❌ {error}</p>
<button on:click={loadPhotos} class="retry-btn">Try Again</button>
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
padding: 2rem;
max-width: 1200px;
margin: 0 auto;
}

.page-header {
text-align: center;
margin-bottom: 2rem;
}

.page-header h1 {
font-size: 2.5rem;
margin: 0 0 0.5rem 0;
color: #1f2937;
}

.page-header p {
font-size: 1.1rem;
color: #6b7280;
margin: 0 0 1rem 0;
}

.refresh-btn, .retry-btn {
background: #3b82f6;
color: white;
border: none;
padding: 0.75rem 1.5rem;
border-radius: 0.5rem;
cursor: pointer;
font-size: 1rem;
transition: background-color 0.2s ease;
}

.refresh-btn:hover, .retry-btn:hover {
background: #2563eb;
}

.loading {
text-align: center;
padding: 3rem;
}

.spinner {
width: 40px;
height: 40px;
border: 4px solid #e5e7eb;
border-top: 4px solid #3b82f6;
border-radius: 50%;
animation: spin 1s linear infinite;
margin: 0 auto 1rem auto;
}

@keyframes spin {
0% { transform: rotate(0deg); }
100% { transform: rotate(360deg); }
}

.error {
text-align: center;
padding: 3rem;
color: #dc2626;
}

.empty-state {
text-align: center;
padding: 3rem;
}

.empty-state h3 {
font-size: 1.5rem;
margin: 0 0 1rem 0;
color: #374151;
}

.empty-state p {
color: #6b7280;
margin: 0 0 1.5rem 0;
}

.import-link {
display: inline-block;
background: #10b981;
color: white;
text-decoration: none;
padding: 0.75rem 1.5rem;
border-radius: 0.5rem;
transition: background-color 0.2s ease;
}

.import-link:hover {
background: #059669;
}

.photos-grid {
display: grid;
grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
gap: 1.5rem;
margin-top: 2rem;
}

.photo-card {
background: white;
border-radius: 0.5rem;
overflow: hidden;
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.photo-card:hover {
transform: translateY(-2px);
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
background: #f3f4f6;
font-size: 3rem;
color: #9ca3af;
}

.photo-info {
padding: 1rem;
}

.photo-filename {
margin: 0 0 0.5rem 0;
font-size: 1rem;
font-weight: 600;
color: #1f2937;
word-break: break-word;
}

.photo-date, .photo-title, .photo-description, .photo-author, .photo-dimensions, 
.photo-rating, .photo-gps, .photo-raw, .photo-files, .photo-tags, .photo-imported {
margin: 0.25rem 0;
font-size: 0.875rem;
color: #6b7280;
line-height: 1.4;
}

.photo-rating {
color: #f59e0b;
font-weight: 500;
}

.photo-gps {
color: #059669;
font-family: monospace;
}

.photo-raw {
color: #8b5cf6;
font-weight: 500;
}

.photo-imported {
color: #9ca3af;
font-size: 0.75rem;
margin-top: 0.5rem;
padding-top: 0.5rem;
border-top: 1px solid #e5e7eb;
}
</style>
