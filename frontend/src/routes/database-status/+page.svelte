<script lang="ts">
	import { currentView } from '$lib/stores/app';
	import { onMount } from 'svelte';

	currentView.set('database-status');

	let loading = false;
	let error = '';
	let databaseInfo = null;

	onMount(async () => {
		await loadDatabaseInfo();
	});

	async function loadDatabaseInfo() {
		loading = true;
		error = '';

		try {
			const response = await fetch('http://localhost:8000/api/v1/debug/database-schema');
			
			if (!response.ok) {
				const errorData = await response.text();
				throw new Error(`HTTP ${response.status}: ${errorData}`);
			}

			databaseInfo = await response.json();
			
		} catch (err) {
			console.error('Failed to load database info:', err);
			error = err.message || 'Failed to load database information';
		} finally {
			loading = false;
		}
	}

	function formatBytes(bytes) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	function getColumnTypeColor(type) {
		const typeColors = {
			'INTEGER': '#3b82f6',
			'TEXT': '#10b981', 
			'VARCHAR': '#10b981',
			'DATETIME': '#f59e0b',
			'FLOAT': '#ef4444',
			'BOOLEAN': '#8b5cf6',
			'JSON': '#f97316',
			'BLOB': '#6b7280',
			'LARGEBINARY': '#6b7280'
		};
		return typeColors[type.toUpperCase()] || '#6b7280';
	}
</script>

<div class="status-page">
	<div class="page-header">
		<h1>📊 Database Status</h1>
		<p>Development database information and table statistics</p>
		<button onclick={loadDatabaseInfo} disabled={loading} class="refresh-btn">
			{#if loading}
				<div class="spinner-small"></div> Loading...
			{:else}
				🔄 Refresh
			{/if}
		</button>
	</div>

	{#if error}
		<div class="error">
			<p>❌ {error}</p>
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading database information...</p>
		</div>
	{:else if databaseInfo}
		<div class="database-overview">
			<div class="overview-card">
				<h3>📂 Database Overview</h3>
				<div class="overview-stats">
					<div class="stat">
						<span class="stat-label">Database URL:</span>
						<span class="stat-value database-url">{databaseInfo.database_url}</span>
					</div>
					<div class="stat">
						<span class="stat-label">Total Tables:</span>
						<span class="stat-value">{databaseInfo.total_tables}</span>
					</div>
					<div class="stat">
						<span class="stat-label">Development Mode:</span>
						<span class="stat-value" class:dev-mode={databaseInfo.development_mode}>
							{databaseInfo.development_mode ? '✅ Yes' : '❌ No'}
						</span>
					</div>
				</div>
			</div>
		</div>

		<div class="tables-section">
			<h2>📋 Table Details</h2>
			
			{#each Object.entries(databaseInfo.tables) as [tableName, tableInfo]}
				<div class="table-card">
					<div class="table-header">
						<h3>🗂️ {tableName}</h3>
						<div class="table-stats">
							<span class="row-count">{tableInfo.row_count} rows</span>
							<span class="column-count">{tableInfo.columns.length} columns</span>
						</div>
					</div>

					<div class="columns-grid">
						{#each tableInfo.columns as column}
							<div class="column-card">
								<div class="column-header">
									<span class="column-name">
										{column.name}
										{#if column.primary_key}
											<span class="pk-badge">PK</span>
										{/if}
									</span>
									<span 
										class="column-type" 
										style="color: {getColumnTypeColor(column.type)}"
									>
										{column.type}
									</span>
								</div>
								<div class="column-details">
									{#if column.not_null}
										<span class="constraint">NOT NULL</span>
									{/if}
									{#if column.default_value !== null}
										<span class="default">DEFAULT: {column.default_value}</span>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>

		<div class="quick-stats">
			<h2>📈 Quick Statistics</h2>
			<div class="stats-grid">
				{#each Object.entries(databaseInfo.tables) as [tableName, tableInfo]}
					<div class="stat-card">
						<div class="stat-icon">
							{#if tableName === 'photos'}🖼️
							{:else if tableName === 'images'}📸
							{:else if tableName === 'authors'}👤
							{:else if tableName === 'import_sessions'}📥
							{:else}📄{/if}
						</div>
						<div class="stat-info">
							<div class="stat-title">{tableName}</div>
							<div class="stat-number">{tableInfo.row_count}</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="navigation">
		<a href="/" class="back-link">← Back to Photos</a>
		{#if import.meta.env.DEV}
			<a href="/clear-database" class="danger-link">🗑️ Clear Database</a>
		{/if}
	</div>
</div>

<style>
	.status-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.page-header h1 {
		color: #1f2937;
		margin: 0;
	}

	.page-header p {
		color: #6b7280;
		margin: 0;
		flex: 1;
	}

	.refresh-btn {
		background-color: #3b82f6;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
	}

	.refresh-btn:hover:not(:disabled) {
		background-color: #2563eb;
	}

	.refresh-btn:disabled {
		background-color: #9ca3af;
		cursor: not-allowed;
	}

	.loading {
		text-align: center;
		padding: 3rem;
		color: #6b7280;
	}

	.spinner, .spinner-small {
		border: 2px solid #f3f4f6;
		border-top: 2px solid #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	.spinner {
		width: 40px;
		height: 40px;
	}

	.spinner-small {
		width: 16px;
		height: 16px;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.database-overview {
		margin-bottom: 2rem;
	}

	.overview-card {
		background: white;
		border-radius: 8px;
		padding: 1.5rem;
		box-shadow: 0 1px 3px rgba(0,0,0,0.1);
		border: 1px solid #e5e7eb;
	}

	.overview-card h3 {
		margin-top: 0;
		color: #1f2937;
	}

	.overview-stats {
		display: grid;
		gap: 1rem;
	}

	.stat {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
		border-bottom: 1px solid #f3f4f6;
	}

	.stat:last-child {
		border-bottom: none;
	}

	.stat-label {
		font-weight: 500;
		color: #374151;
	}

	.stat-value {
		font-family: monospace;
		color: #6b7280;
	}

	.database-url {
		font-size: 0.875rem;
		max-width: 400px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.dev-mode {
		color: #059669 !important;
		font-weight: 600;
	}

	.tables-section {
		margin-bottom: 2rem;
	}

	.tables-section h2 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.table-card {
		background: white;
		border-radius: 8px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
		box-shadow: 0 1px 3px rgba(0,0,0,0.1);
		border: 1px solid #e5e7eb;
	}

	.table-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.table-header h3 {
		margin: 0;
		color: #1f2937;
	}

	.table-stats {
		display: flex;
		gap: 1rem;
		font-size: 0.875rem;
	}

	.row-count {
		background-color: #dbeafe;
		color: #1e40af;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-weight: 500;
	}

	.column-count {
		background-color: #ecfdf5;
		color: #047857;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-weight: 500;
	}

	.columns-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1rem;
	}

	.column-card {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		padding: 1rem;
	}

	.column-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.column-name {
		font-weight: 600;
		color: #1f2937;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.pk-badge {
		background-color: #fbbf24;
		color: #92400e;
		font-size: 0.75rem;
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		font-weight: 600;
	}

	.column-type {
		font-family: monospace;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.column-details {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.constraint, .default {
		font-size: 0.75rem;
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		font-weight: 500;
	}

	.constraint {
		background-color: #fef3c7;
		color: #92400e;
	}

	.default {
		background-color: #e0e7ff;
		color: #3730a3;
	}

	.quick-stats h2 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.stat-card {
		background: white;
		border-radius: 8px;
		padding: 1.5rem;
		box-shadow: 0 1px 3px rgba(0,0,0,0.1);
		border: 1px solid #e5e7eb;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.stat-icon {
		font-size: 2rem;
	}

	.stat-info {
		flex: 1;
	}

	.stat-title {
		font-weight: 500;
		color: #6b7280;
		font-size: 0.875rem;
		text-transform: capitalize;
	}

	.stat-number {
		font-size: 1.875rem;
		font-weight: 700;
		color: #1f2937;
	}

	.error {
		background-color: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 6px;
		padding: 1rem;
		margin: 1rem 0;
		color: #991b1b;
	}

	.navigation {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 2rem;
		padding-top: 2rem;
		border-top: 1px solid #e5e7eb;
	}

	.back-link, .danger-link {
		text-decoration: none;
		font-weight: 500;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		transition: background-color 0.2s;
	}

	.back-link {
		color: #3b82f6;
	}

	.back-link:hover {
		background-color: #eff6ff;
	}

	.danger-link {
		color: #dc2626;
		border: 1px solid #fecaca;
	}

	.danger-link:hover {
		background-color: #fef2f2;
	}
</style>