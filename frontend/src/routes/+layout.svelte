<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { currentView } from '$lib/stores/app';

	let { children } = $props();
</script>

<svelte:head>
	<title>ImaLink - Photo Management</title>
	<link rel="icon" href={favicon} />
	<meta name="description" content="Modern photo management and gallery system" />
</svelte:head>

<div class="app">
	<!-- Navigation -->
	<nav class="navbar">
		<div class="nav-brand">
			<h1>📸 ImaLink</h1>
		</div>
		<div class="nav-links">
			<a href="/" class="nav-link" class:active={$currentView === 'photos'}>Photos</a>
			<a href="/import" class="nav-link" class:active={$currentView === 'imports'}>Import</a>
			<a href="/authors" class="nav-link" class:active={$currentView === 'authors'}>Authors</a>
			{#if import.meta.env.DEV}
				<a href="/database-status" class="nav-link dev-link" class:active={$currentView === 'database-status'}>📊 Status</a>
				<a href="/clear-database" class="nav-link dev-link danger" class:active={$currentView === 'clear-database'}>🗑️ Clear</a>
			{/if}
		</div>
	</nav>

	<!-- Main content -->
	<main class="main-content">
		{@render children?.()}
	</main>
</div>

<style>
	.app {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	.navbar {
		background: #2563eb;
		color: white;
		padding: 1rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	}

	.nav-brand h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
	}

	.nav-links {
		display: flex;
		gap: 2rem;
	}

	.nav-link {
		color: rgba(255,255,255,0.8);
		text-decoration: none;
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		transition: all 0.2s;
	}

	.nav-link:hover {
		color: white;
		background: rgba(255,255,255,0.1);
	}

	.nav-link.active {
		color: white;
		background: rgba(255,255,255,0.2);
		font-weight: 500;
	}

	.dev-link {
		color: #fbbf24 !important;
		border: 1px solid rgba(251, 191, 36, 0.3);
		font-size: 0.875rem;
	}

	.dev-link:hover {
		background: rgba(251, 191, 36, 0.1) !important;
		border-color: rgba(251, 191, 36, 0.5);
	}

	.dev-link.danger {
		color: #ef4444 !important;
		border: 1px solid rgba(239, 68, 68, 0.3);
	}

	.dev-link.danger:hover {
		background: rgba(239, 68, 68, 0.1) !important;
		border-color: rgba(239, 68, 68, 0.5);
	}

	.main-content {
		flex: 1;
		padding: 2rem;
		max-width: 1200px;
		margin: 0 auto;
		width: 100%;
	}

	/* Global styles */
	:global(body) {
		margin: 0;
		padding: 0;
		background: #f8fafc;
	}

	:global(*, *::before, *::after) {
		box-sizing: border-box;
	}
</style>
