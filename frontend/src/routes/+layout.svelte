<script>
    import { page } from '$app/stores';
</script>

<div class="app">
    <header class="header">
        <nav class="nav">
            <div class="nav-brand">
                <h1><a href="/">ImaLink</a></h1>
            </div>
            <ul class="nav-menu">
                <li class="nav-item">
                    <a href="/" class:active={$page.url.pathname === '/'}>Hjem</a>
                </li>
                <li class="nav-item">
                    <a href="/gallery" class:active={$page.url.pathname === '/gallery'}>Galleri</a>
                </li>
                <li class="nav-item">
                    <a href="/import" class:active={$page.url.pathname === '/import'}>Import</a>
                </li>
                <li class="nav-item">
                    <a href="/authors" class:active={$page.url.pathname === '/authors'}>Forfattere</a>
                </li>
            </ul>
        </nav>
    </header>

    <main class="main">
        <slot />
    </main>

    <footer class="footer">
        <p>&copy; 2025 ImaLink - Bildehåndtering</p>
    </footer>
</div>

<style>
    :global(body) {
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: #f5f5f5;
        color: #333;
    }

    .app {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    .header {
        background-color: #2c3e50;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
        height: 60px;
    }

    .nav-brand h1 {
        margin: 0;
    }

    .nav-brand a {
        color: white;
        text-decoration: none;
        font-size: 1.5rem;
        font-weight: bold;
    }

    .nav-menu {
        display: flex;
        list-style: none;
        margin: 0;
        padding: 0;
        gap: 2rem;
    }

    .nav-item a {
        color: white;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        transition: background-color 0.2s;
    }

    .nav-item a:hover, .nav-item a.active {
        background-color: #34495e;
    }

    .main {
        flex: 1;
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
        width: 100%;
        box-sizing: border-box;
    }

    .footer {
        background-color: #34495e;
        color: white;
        text-align: center;
        padding: 1rem;
    }

    .footer p {
        margin: 0;
    }
</style>