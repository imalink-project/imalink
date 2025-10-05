<script>
    import { onMount } from 'svelte';
    import { getImages, getThumbnailUrl, getImageUrl } from '$lib/api.js';

    let images = [];
    let loading = true;
    let error = null;
    let selectedImage = null;

    onMount(async () => {
        try {
            images = await getImages();
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    });

    function openImage(image) {
        selectedImage = image;
    }

    function closeImage() {
        selectedImage = null;
    }

    function formatDate(dateString) {
        if (!dateString) return 'Ukjent dato';
        return new Date(dateString).toLocaleDateString('no-NO');
    }
</script>

<svelte:head>
    <title>Galleri - ImaLink</title>
</svelte:head>

<div class="gallery-page">
    <div class="page-header">
        <h1>Bildegalleri</h1>
        <p>Bla gjennom din bildekolleksjon</p>
    </div>

    {#if loading}
        <div class="loading">
            <p>Laster bilder...</p>
        </div>
    {:else if error}
        <div class="error">
            <h3>Feil ved lasting av bilder</h3>
            <p>{error}</p>
        </div>
    {:else if images.length === 0}
        <div class="empty">
            <h3>Ingen bilder funnet</h3>
            <p>Importer bilder for å se dem her.</p>
            <a href="/import" class="import-link">Gå til import</a>
        </div>
    {:else}
        <div class="gallery-stats">
            <p>{images.length} bilder funnet</p>
        </div>

        <div class="gallery-grid">
            {#each images as image (image.id)}
                <div class="image-card" 
                     role="button" 
                     tabindex="0" 
                     on:click={() => openImage(image)}
                     on:keydown={(e) => e.key === 'Enter' && openImage(image)}>
                    <div class="image-container">
                        <img 
                            src={getThumbnailUrl(image.id)} 
                            alt={image.filename}
                            loading="lazy"
                        />
                    </div>
                    <div class="image-info">
                        <h3>{image.filename}</h3>
                        <p class="image-meta">
                            {formatDate(image.date_taken)} • 
                            {image.file_size ? Math.round(image.file_size / 1024) + ' KB' : ''}
                        </p>
                        {#if image.author_name}
                            <p class="image-author">📷 {image.author_name}</p>
                        {/if}
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<!-- Image Modal -->
{#if selectedImage}
    <div class="modal" 
         role="dialog" 
         on:click={closeImage}
         on:keydown={(e) => e.key === 'Escape' && closeImage()}>
        <div class="modal-content" on:click|stopPropagation>
            <button class="close-btn" on:click={closeImage}>&times;</button>
            <img 
                src={getImageUrl(selectedImage.id)} 
                alt={selectedImage.filename}
                class="modal-image"
            />
            <div class="modal-info">
                <h2>{selectedImage.filename}</h2>
                <div class="image-details">
                    <p><strong>Dato:</strong> {formatDate(selectedImage.date_taken)}</p>
                    {#if selectedImage.author_name}
                        <p><strong>Fotograf:</strong> {selectedImage.author_name}</p>
                    {/if}
                    {#if selectedImage.camera_make}
                        <p><strong>Kamera:</strong> {selectedImage.camera_make} {selectedImage.camera_model || ''}</p>
                    {/if}
                    {#if selectedImage.file_size}
                        <p><strong>Størrelse:</strong> {Math.round(selectedImage.file_size / 1024)} KB</p>
                    {/if}
                    {#if selectedImage.image_width && selectedImage.image_height}
                        <p><strong>Oppløsning:</strong> {selectedImage.image_width} × {selectedImage.image_height}</p>
                    {/if}
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .gallery-page {
        max-width: 1200px;
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

    .loading, .error, .empty {
        text-align: center;
        padding: 3rem 1rem;
    }

    .error {
        background: #ffe6e6;
        border-radius: 8px;
        color: #d32f2f;
    }

    .empty {
        background: #f8f9fa;
        border-radius: 8px;
        color: #666;
    }

    .import-link {
        display: inline-block;
        margin-top: 1rem;
        padding: 0.75rem 1.5rem;
        background: #3498db;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        transition: background-color 0.2s;
    }

    .import-link:hover {
        background: #2980b9;
    }

    .gallery-stats {
        margin-bottom: 1rem;
        text-align: right;
        color: #666;
        font-size: 0.9rem;
    }

    .gallery-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
    }

    .image-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        overflow: hidden;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .image-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }

    .image-container {
        aspect-ratio: 4/3;
        overflow: hidden;
        background: #f5f5f5;
    }

    .image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .image-info {
        padding: 1rem;
    }

    .image-info h3 {
        margin: 0 0 0.5rem 0;
        font-size: 0.9rem;
        color: #2c3e50;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .image-meta {
        margin: 0 0 0.5rem 0;
        font-size: 0.8rem;
        color: #666;
    }

    .image-author {
        margin: 0;
        font-size: 0.8rem;
        color: #3498db;
    }

    /* Modal styles */
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .modal-content {
        position: relative;
        max-width: 90vw;
        max-height: 90vh;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .close-btn {
        position: absolute;
        top: 10px;
        right: 15px;
        background: rgba(0,0,0,0.5);
        color: white;
        border: none;
        font-size: 2rem;
        cursor: pointer;
        z-index: 1001;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .modal-image {
        max-width: 100%;
        max-height: 70vh;
        object-fit: contain;
    }

    .modal-info {
        padding: 1rem;
        background: white;
    }

    .modal-info h2 {
        margin: 0 0 1rem 0;
        color: #2c3e50;
    }

    .image-details p {
        margin: 0.25rem 0;
        color: #666;
    }

    @media (max-width: 768px) {
        .gallery-grid {
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .modal-content {
            max-width: 95vw;
            max-height: 95vh;
        }
        
        .modal-info {
            padding: 0.75rem;
        }
    }
</style>