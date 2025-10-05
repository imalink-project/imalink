<script>
    import { onMount } from 'svelte';
    import { healthCheck, getImages, getAuthors } from '$lib/api.js';

    let backendStatus = 'Sjekker...';
    let imageCount = 0;
    let authorCount = 0;
    let error = null;

    onMount(async () => {
        try {
            // Test backend connection
            const health = await healthCheck();
            backendStatus = health.message || 'OK';
            
            // Get basic stats
            const [images, authors] = await Promise.all([
                getImages(),
                getAuthors()
            ]);
            
            imageCount = images.length || 0;
            authorCount = authors.length || 0;
        } catch (err) {
            error = err.message;
            backendStatus = 'Feil - ikke tilkoblet';
        }
    });
</script>

<svelte:head>
    <title>ImaLink - Bildehåndtering</title>
</svelte:head>

<div class="dashboard">
    <div class="hero">
        <h1>Velkommen til ImaLink</h1>
        <p>Organisering og håndtering av bildekolleksjoner</p>
    </div>

    <div class="status-grid">
        <div class="status-card">
            <h3>Backend Status</h3>
            <p class="status-value" class:error={error}>
                {backendStatus}
            </p>
        </div>

        <div class="status-card">
            <h3>Bilder</h3>
            <p class="status-value">{imageCount}</p>
        </div>

        <div class="status-card">
            <h3>Forfattere</h3>
            <p class="status-value">{authorCount}</p>
        </div>
    </div>

    {#if error}
        <div class="error-message">
            <h3>Tilkoblingsfeil</h3>
            <p>Kan ikke koble til backend: {error}</p>
            <p>Sjekk at FastAPI server kjører på localhost:8000</p>
        </div>
    {:else}
        <div class="quick-actions">
            <h2>Hurtighandlinger</h2>
            <div class="action-buttons">
                <a href="/gallery" class="action-btn">
                    <span>📷</span>
                    <div>
                        <h3>Se Galleri</h3>
                        <p>Bla gjennom bildekolleksjonen</p>
                    </div>
                </a>

                <a href="/import" class="action-btn">
                    <span>📁</span>
                    <div>
                        <h3>Importer Bilder</h3>
                        <p>Legg til nye bilder fra mappe</p>
                    </div>
                </a>

                <a href="/authors" class="action-btn">
                    <span>👤</span>
                    <div>
                        <h3>Forfattere</h3>
                        <p>Se fotografer og deres bilder</p>
                    </div>
                </a>
            </div>
        </div>
    {/if}
</div>

<style>
    .dashboard {
        max-width: 1000px;
        margin: 0 auto;
    }

    .hero {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
    }

    .hero h1 {
        font-size: 3rem;
        margin: 0 0 1rem 0;
    }

    .hero p {
        font-size: 1.2rem;
        margin: 0;
        opacity: 0.9;
    }

    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3rem;
    }

    .status-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }

    .status-card h3 {
        margin: 0 0 1rem 0;
        color: #666;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .status-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
        color: #2c3e50;
    }

    .status-value.error {
        color: #e74c3c;
    }

    .error-message {
        background: #ffe6e6;
        border: 1px solid #ffcccc;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        color: #d32f2f;
    }

    .error-message h3 {
        margin: 0 0 1rem 0;
        color: #d32f2f;
    }

    .quick-actions h2 {
        text-align: center;
        margin-bottom: 2rem;
        color: #2c3e50;
    }

    .action-buttons {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
    }

    .action-btn {
        display: flex;
        align-items: center;
        padding: 1.5rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-decoration: none;
        color: #333;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }

    .action-btn span {
        font-size: 2.5rem;
        margin-right: 1rem;
    }

    .action-btn h3 {
        margin: 0 0 0.5rem 0;
        color: #2c3e50;
    }

    .action-btn p {
        margin: 0;
        color: #666;
        font-size: 0.9rem;
    }
</style>
