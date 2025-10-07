<script lang="ts">
	import { currentView } from '$lib/stores/app';

	currentView.set('clear-database');

	let clearing = false;
	let result = null;
	let error = '';

	async function clearDatabase() {
		if (!confirm('⚠️ ADVARSEL: Dette vil slette ALLE data i databasen!\n\nEr du sikker på at du vil fortsette?')) {
			return;
		}

		if (!confirm('🚨 SISTE SJANSE: All data vil bli permanent slettet!\n\nDette kan ikke angres. Fortsett?')) {
			return;
		}

		clearing = true;
		error = '';
		result = null;

		try {
			const response = await fetch('http://localhost:8000/api/v1/debug/clear-database', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				}
			});

			if (!response.ok) {
				const errorData = await response.text();
				throw new Error(`HTTP ${response.status}: ${errorData}`);
			}

			result = await response.json();
			
		} catch (err) {
			console.error('Clear database failed:', err);
			error = err.message || 'Failed to clear database';
		} finally {
			clearing = false;
		}
	}
</script>

<div class="clear-database-page">
	<div class="page-header">
		<h1>🗑️ Clear Database</h1>
		<p class="warning">⚠️ Development tool - Use with extreme caution!</p>
	</div>

	{#if error}
		<div class="error">
			<p>❌ {error}</p>
		</div>
	{/if}

	{#if result}
		<div class="success">
			<p>✅ Database cleared successfully!</p>
			<div class="result-details">
				<p>• Photos deleted: {result.photos_deleted || 0}</p>
				<p>• Images deleted: {result.images_deleted || 0}</p>
				<p>• Authors deleted: {result.authors_deleted || 0}</p>
				<p>• Import sessions deleted: {result.import_sessions_deleted || 0}</p>
			</div>
		</div>
	{/if}

	<div class="action-card">
		<h3>🚨 Database Reset</h3>
		<p>This will permanently delete:</p>
		<ul>
			<li>All photos and images</li>
			<li>All authors</li>
			<li>All import sessions</li>
			<li>All metadata and relationships</li>
		</ul>
		
		<div class="warning-box">
			<p><strong>⚠️ WARNING:</strong> This action cannot be undone!</p>
			<p>Only use during development when you need a clean database state.</p>
		</div>

		<button 
			onclick={clearDatabase}
			disabled={clearing}
			class="clear-btn"
		>
			{#if clearing}
				<div class="spinner-small"></div> Clearing Database...
			{:else}
				🗑️ Clear All Database Data
			{/if}
		</button>
	</div>

	<div class="navigation">
		<a href="/" class="back-link">← Back to Photos</a>
	</div>
</div>

<style>
	.clear-database-page {
		max-width: 600px;
		margin: 0 auto;
		padding: 2rem;
	}

	.page-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.page-header h1 {
		color: #dc3545;
		margin-bottom: 0.5rem;
	}

	.warning {
		color: #856404;
		background-color: #fff3cd;
		border: 1px solid #ffeaa7;
		border-radius: 4px;
		padding: 0.5rem 1rem;
		margin: 0;
	}

	.action-card {
		background: white;
		border: 2px solid #dc3545;
		border-radius: 8px;
		padding: 2rem;
		margin-bottom: 2rem;
	}

	.action-card h3 {
		color: #dc3545;
		margin-top: 0;
	}

	.action-card ul {
		margin: 1rem 0;
		padding-left: 1.5rem;
	}

	.action-card li {
		margin: 0.5rem 0;
		color: #666;
	}

	.warning-box {
		background-color: #f8d7da;
		border: 1px solid #f5c6cb;
		border-radius: 4px;
		padding: 1rem;
		margin: 1.5rem 0;
	}

	.warning-box p {
		margin: 0.5rem 0;
		color: #721c24;
	}

	.clear-btn {
		background-color: #dc3545;
		color: white;
		border: none;
		padding: 1rem 2rem;
		border-radius: 6px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		justify-content: center;
		transition: background-color 0.2s;
	}

	.clear-btn:hover:not(:disabled) {
		background-color: #c82333;
	}

	.clear-btn:disabled {
		background-color: #6c757d;
		cursor: not-allowed;
	}

	.success {
		background-color: #d4edda;
		border: 1px solid #c3e6cb;
		border-radius: 4px;
		padding: 1rem;
		margin: 1rem 0;
		color: #155724;
	}

	.result-details {
		margin-top: 1rem;
		font-family: monospace;
	}

	.result-details p {
		margin: 0.25rem 0;
	}

	.error {
		background-color: #f8d7da;
		border: 1px solid #f5c6cb;
		border-radius: 4px;
		padding: 1rem;
		margin: 1rem 0;
		color: #721c24;
	}

	.spinner-small {
		width: 16px;
		height: 16px;
		border: 2px solid transparent;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.navigation {
		text-align: center;
		margin-top: 2rem;
	}

	.back-link {
		color: #007bff;
		text-decoration: none;
		font-weight: 500;
	}

	.back-link:hover {
		text-decoration: underline;
	}
</style>