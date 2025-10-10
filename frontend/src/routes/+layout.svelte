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
				<a href="/timeline-demo" class="nav-link dev-link" class:active={$currentView === 'timeline'}>📅 Timeline</a>
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
		background: var(--color-primary-hover);
		color: white;
		padding: var(--spacing-md) var(--spacing-xl);
		display: flex;
		justify-content: space-between;
		align-items: center;
		box-shadow: var(--shadow-md);
	}

	.nav-brand h1 {
		margin: 0;
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-semibold);
	}

	.nav-links {
		display: flex;
		gap: var(--spacing-xl);
	}

	.nav-link {
		color: rgba(255,255,255,0.8);
		text-decoration: none;
		padding: var(--spacing-sm) var(--spacing-md);
		border-radius: var(--radius-md);
		transition: all var(--transition-normal);
	}

	.nav-link:hover {
		color: white;
		background: rgba(255,255,255,0.1);
	}

	.nav-link.active {
		color: white;
		background: rgba(255,255,255,0.2);
		font-weight: var(--font-weight-medium);
	}

	.dev-link {
		color: #fbbf24 !important;
		border: 1px solid rgba(251, 191, 36, 0.3);
		font-size: var(--font-size-sm);
	}

	.dev-link:hover {
		background: rgba(251, 191, 36, 0.1) !important;
		border-color: rgba(251, 191, 36, 0.5);
	}

	.dev-link.danger {
		color: var(--color-error) !important;
		border: 1px solid rgba(239, 68, 68, 0.3);
	}

	.dev-link.danger:hover {
		background: rgba(239, 68, 68, 0.1) !important;
		border-color: rgba(239, 68, 68, 0.5);
	}

	.main-content {
		flex: 1;
		padding: var(--spacing-xl);
		max-width: 1200px;
		margin: 0 auto;
		width: 100%;
	}

	/* Design Tokens */
	:global(:root) {
		/* Colors */
		--color-primary: #3b82f6;
		--color-primary-hover: #2563eb;
		--color-success: #10b981;
		--color-success-hover: #059669;
		--color-error: #dc2626;
		--color-error-hover: #b91c1c;
		--color-warning: #f59e0b;
		--color-warning-hover: #d97706;
		--color-purple: #8b5cf6;
		--color-orange: #f97316;
		
		/* Gray scale */
		--color-gray-50: #f9fafb;
		--color-gray-100: #f3f4f6;
		--color-gray-200: #e5e7eb;
		--color-gray-300: #d1d5db;
		--color-gray-400: #9ca3af;
		--color-gray-500: #6b7280;
		--color-gray-600: #4b5563;
		--color-gray-700: #374151;
		--color-gray-800: #1f2937;
		--color-gray-900: #111827;
		
		/* Background colors */
		--bg-app: #f8fafc;
		--bg-card: white;
		--bg-error: #fef2f2;
		--bg-success: #f0fdf4;
		--bg-warning: #fffbeb;
		--bg-info: #eff6ff;
		
		/* Border colors */
		--border-light: #e5e7eb;
		--border-medium: #d1d5db;
		--border-dark: #9ca3af;
		--border-error: #fecaca;
		--border-success: #bbf7d0;
		--border-warning: #fed7aa;
		--border-info: #bfdbfe;
		
		/* Spacing */
		--spacing-xs: 0.25rem;
		--spacing-sm: 0.5rem;
		--spacing-md: 1rem;
		--spacing-lg: 1.5rem;
		--spacing-xl: 2rem;
		--spacing-2xl: 3rem;
		
		/* Typography */
		--font-size-xs: 0.75rem;
		--font-size-sm: 0.875rem;
		--font-size-base: 1rem;
		--font-size-lg: 1.125rem;
		--font-size-xl: 1.25rem;
		--font-size-2xl: 1.5rem;
		--font-size-3xl: 1.875rem;
		
		/* Font weights */
		--font-weight-normal: 400;
		--font-weight-medium: 500;
		--font-weight-semibold: 600;
		--font-weight-bold: 700;
		
		/* Line heights */
		--line-height-tight: 1.25;
		--line-height-normal: 1.5;
		--line-height-relaxed: 1.75;
		
		/* Border radius */
		--radius-sm: 0.25rem;
		--radius-md: 0.375rem;
		--radius-lg: 0.5rem;
		--radius-xl: 0.75rem;
		--radius-2xl: 1rem;
		--radius-full: 50%;
		
		/* Shadows */
		--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
		--shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1);
		--shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.1);
		--shadow-xl: 0 10px 15px rgba(0, 0, 0, 0.1);
		--shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.25);
		
		/* Transitions */
		--transition-fast: 0.15s ease;
		--transition-normal: 0.2s ease;
		--transition-slow: 0.3s ease;
		
		/* Z-index scale */
		--z-dropdown: 1000;
		--z-sticky: 1020;
		--z-fixed: 1030;
		--z-modal-backdrop: 1040;
		--z-modal: 1050;
		--z-popover: 1060;
		--z-tooltip: 1070;
	}

	/* Utility Classes */
	:global(.btn) {
		display: inline-block;
		padding: var(--spacing-sm) var(--spacing-md);
		border-radius: var(--radius-md);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: all var(--transition-normal);
		border: 1px solid transparent;
		text-decoration: none;
		text-align: center;
	}

	:global(.btn:disabled) {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Global button styles removed - using Button component instead */

	:global(.btn-lg) {
		padding: var(--spacing-md) var(--spacing-xl);
		font-size: var(--font-size-base);
	}

	:global(.card) {
		background: var(--bg-card);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md);
		padding: var(--spacing-lg);
		border: 1px solid var(--border-light);
	}

	:global(.card-compact) {
		padding: var(--spacing-md);
	}

	:global(.form-input) {
		width: 100%;
		padding: var(--spacing-sm);
		border: 1px solid var(--border-medium);
		border-radius: var(--radius-md);
		font-size: var(--font-size-sm);
		transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
	}

	:global(.form-input:focus) {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 1px var(--color-primary);
	}

	:global(.form-input:invalid) {
		border-color: var(--color-error);
	}

	:global(.form-label) {
		display: block;
		margin-bottom: var(--spacing-xs);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-gray-700);
	}

	:global(.alert) {
		padding: var(--spacing-md);
		border-radius: var(--radius-md);
		margin-bottom: var(--spacing-md);
		border: 1px solid;
	}

	:global(.alert-success) {
		background: var(--bg-success);
		border-color: var(--border-success);
		color: var(--color-success-hover);
	}

	:global(.alert-error) {
		background: var(--bg-error);
		border-color: var(--border-error);
		color: var(--color-error);
	}

	:global(.alert-warning) {
		background: var(--bg-warning);
		border-color: var(--border-warning);
		color: var(--color-warning-hover);
	}

	:global(.alert-info) {
		background: var(--bg-info);
		border-color: var(--border-info);
		color: var(--color-primary-hover);
	}

	:global(.text-success) {
		color: var(--color-success);
	}

	:global(.text-error) {
		color: var(--color-error);
	}

	:global(.text-warning) {
		color: var(--color-warning);
	}

	:global(.text-muted) {
		color: var(--color-gray-500);
	}

	:global(.text-xs) {
		font-size: var(--font-size-xs);
	}

	:global(.text-sm) {
		font-size: var(--font-size-sm);
	}

	:global(.text-lg) {
		font-size: var(--font-size-lg);
	}

	:global(.text-xl) {
		font-size: var(--font-size-xl);
	}

	:global(.font-medium) {
		font-weight: var(--font-weight-medium);
	}

	:global(.font-semibold) {
		font-weight: var(--font-weight-semibold);
	}

	:global(.font-bold) {
		font-weight: var(--font-weight-bold);
	}

	:global(.loading-spinner) {
		border: 2px solid var(--color-gray-200);
		border-top: 2px solid var(--color-primary);
		border-radius: var(--radius-full);
		width: 20px;
		height: 20px;
		animation: spin 1s linear infinite;
	}

	:global(.loading-spinner-lg) {
		width: 40px;
		height: 40px;
		border-width: 3px;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	:global(.grid) {
		display: grid;
	}

	:global(.grid-cols-1) {
		grid-template-columns: repeat(1, minmax(0, 1fr));
	}

	:global(.grid-cols-2) {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	:global(.grid-cols-3) {
		grid-template-columns: repeat(3, minmax(0, 1fr));
	}

	:global(.grid-auto-fit) {
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	}

	:global(.gap-sm) {
		gap: var(--spacing-sm);
	}

	:global(.gap-md) {
		gap: var(--spacing-md);
	}

	:global(.gap-lg) {
		gap: var(--spacing-lg);
	}

	:global(.flex) {
		display: flex;
	}

	:global(.flex-col) {
		flex-direction: column;
	}

	:global(.items-center) {
		align-items: center;
	}

	:global(.justify-center) {
		justify-content: center;
	}

	:global(.justify-between) {
		justify-content: space-between;
	}

	:global(.space-y-sm > * + *) {
		margin-top: var(--spacing-sm);
	}

	:global(.space-y-md > * + *) {
		margin-top: var(--spacing-md);
	}

	:global(.space-y-lg > * + *) {
		margin-top: var(--spacing-lg);
	}

	/* Global styles */
	:global(body) {
		margin: 0;
		padding: 0;
		background: var(--bg-app);
	}

	:global(*, *::before, *::after) {
		box-sizing: border-box;
	}
</style>
