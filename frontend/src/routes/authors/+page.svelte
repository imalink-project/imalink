<script>
    import { onMount } from 'svelte';
    import { getAuthors, getThumbnailUrl } from '$lib/api.js';

    let authors = [];
    let loading = true;
    let error = null;

    onMount(async () => {
        try {
            authors = await getAuthors();
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    });
</script>

<svelte:head>
    <title>Forfattere - ImaLink</title>
</svelte:head>

<div class="authors-page">
    <div class="page-header">
        <h1>Fotografer</h1>
        <p>Se alle fotografer i din samling</p>
    </div>

    {#if loading}
        <div class="loading">
            <p>Laster fotografer...</p>
        </div>
    {:else if error}
        <div class="error">
            <h3>Feil ved lasting</h3>
            <p>{error}</p>
        </div>
    {:else if authors.length === 0}
        <div class="empty">
            <h3>Ingen fotografer funnet</h3>
            <p>Importer bilder med EXIF-data for å se fotografer.</p>
        </div>
    {:else}
        <div class="authors-stats">
            <p>{authors.length} fotografer funnet</p>
        </div>

        <div class="authors-grid">
            {#each authors as author (author.id)}
                <div class="author-card">
                    <div class="author-header">
                        <div class="author-avatar">
                            📷
                        </div>
                        <div class="author-info">
                            <h3>{author.name}</h3>
                            <p>{author.image_count || 0} bilder</p>
                        </div>
                    </div>

                    {#if author.recent_images && author.recent_images.length > 0}
                        <div class="author-images">
                            <h4>Siste bilder:</h4>
                            <div class="images-grid">
                                {#each author.recent_images.slice(0, 4) as image (image.id)}
                                    <div class="image-thumb">
                                        <img 
                                            src={getThumbnailUrl(image.id)} 
                                            alt={image.filename}
                                            loading="lazy"
                                        />
                                    </div>
                                {/each}
                            </div>
                            {#if author.image_count > 4}
                                <p class="more-images">
                                    +{author.image_count - 4} flere bilder
                                </p>
                            {/if}
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .authors-page {
        max-width: 1000px;
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

    .authors-stats {
        margin-bottom: 1rem;
        text-align: right;
        color: #666;
        font-size: 0.9rem;
    }

    .authors-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 1.5rem;
    }

    .author-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 1.5rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .author-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }

    .author-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
    }

    .author-avatar {
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #3498db, #2980b9);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-right: 1rem;
    }

    .author-info h3 {
        margin: 0 0 0.25rem 0;
        color: #2c3e50;
        font-size: 1.1rem;
    }

    .author-info p {
        margin: 0;
        color: #666;
        font-size: 0.9rem;
    }

    .author-images h4 {
        margin: 0 0 1rem 0;
        color: #2c3e50;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .images-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    .image-thumb {
        aspect-ratio: 1;
        overflow: hidden;
        border-radius: 4px;
        background: #f5f5f5;
    }

    .image-thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .more-images {
        margin: 0;
        text-align: center;
        color: #666;
        font-size: 0.8rem;
        font-style: italic;
    }

    @media (max-width: 768px) {
        .authors-grid {
            grid-template-columns: 1fr;
        }
        
        .author-card {
            padding: 1rem;
        }
        
        .images-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
</style>