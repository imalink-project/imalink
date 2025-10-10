<script lang="ts">
import { currentView } from '$lib/stores/app';
import { onMount } from 'svelte';
import { Button, Card, PageHeader } from '$lib/components/ui';	currentView.set('database-status');

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
	<PageHeader 
		title="Database Status" 
		icon="📊"
		description="Development database information and table statistics"
	>
		<Button variant="primary" onclick={loadDatabaseInfo} disabled={loading}>
			{#if loading}
				<div class="spinner-small"></div> Loading...
			{:else}
				🔄 Refresh
			{/if}
		</Button>
	</PageHeader>

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
			<Card>
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
			</Card>
		</div>

		<div class="tables-section">
			<h2>📋 Table Details</h2>
			
			{#each Object.entries(databaseInfo.tables) as [tableName, tableInfo]}
				<Card>
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
				</Card>
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
		padding: var(--spacing-xl);
	}

	/* Page header styling now handled by PageHeader component */

	/* Refresh button now uses global .btn .btn-primary utility classes */

	.loading {
		text-align: center;
		padding: var(--spacing-2xl);
		color: var(--color-gray-500);
	}

	.spinner, .spinner-small {
		border: 2px solid var(--color-gray-100);
		border-top: 2px solid var(--color-primary);
		border-radius: var(--radius-full);
		animation: spin 1s linear infinite;
		margin: 0 auto var(--spacing-md);
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
		margin-bottom: var(--spacing-xl);
	}

	/* Overview card styling now handled by Card component */

	.overview-stats {
		display: grid;
		gap: var(--spacing-md);
	}

	.stat {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-sm) 0;
		border-bottom: 1px solid var(--color-gray-100);
	}

	.stat:last-child {
		border-bottom: none;
	}

	.stat-label {
		font-weight: var(--font-weight-medium);
		color: var(--color-gray-700);
	}

	.stat-value {
		font-family: monospace;
		color: var(--color-gray-500);
	}

	.database-url {
		font-size: var(--font-size-sm);
		max-width: 400px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.dev-mode {
		color: var(--color-success-hover) !important;
		font-weight: var(--font-weight-semibold);
	}

	.tables-section {
		margin-bottom: var(--spacing-xl);
	}

	.tables-section h2 {
		color: var(--color-gray-800);
		margin-bottom: var(--spacing-md);
		font-weight: var(--font-weight-bold);
	}

	/* Table card styling now handled by Card component */

	.table-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
		flex-wrap: wrap;
		gap: var(--spacing-md);
	}

	.table-header h3 {
		margin: 0;
		color: var(--color-gray-800);
		font-weight: var(--font-weight-semibold);
	}

	.table-stats {
		display: flex;
		gap: var(--spacing-md);
		font-size: var(--font-size-sm);
	}

	.row-count {
		background-color: var(--bg-info);
		color: var(--color-primary-hover);
		padding: var(--spacing-xs) var(--spacing-sm);
		border-radius: var(--radius-sm);
		font-weight: var(--font-weight-medium);
	}

	.column-count {
		background-color: var(--bg-success);
		color: var(--color-success-hover);
		padding: var(--spacing-xs) var(--spacing-sm);
		border-radius: var(--radius-sm);
		font-weight: var(--font-weight-medium);
	}

	.columns-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--spacing-md);
	}

	.column-card {
		background: var(--color-gray-50);
		border: 1px solid var(--border-light);
		border-radius: var(--radius-md);
		padding: var(--spacing-md);
	}

	.column-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-sm);
	}

	.column-name {
		font-weight: var(--font-weight-semibold);
		color: var(--color-gray-800);
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.pk-badge {
		background-color: var(--color-warning);
		color: var(--color-warning-hover);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		border-radius: var(--radius-sm);
		font-weight: var(--font-weight-semibold);
	}

	.column-type {
		font-family: monospace;
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
	}

	.column-details {
		display: flex;
		gap: var(--spacing-sm);
		flex-wrap: wrap;
	}

	.constraint, .default {
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		border-radius: var(--radius-sm);
		font-weight: var(--font-weight-medium);
	}

	.constraint {
		background-color: var(--bg-warning);
		color: var(--color-warning-hover);
	}

	.default {
		background-color: var(--bg-info);
		color: var(--color-primary-hover);
	}

	.quick-stats h2 {
		color: var(--color-gray-800);
		margin-bottom: var(--spacing-md);
		font-weight: var(--font-weight-bold);
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: var(--spacing-md);
		margin-bottom: var(--spacing-xl);
	}

	.stat-card {
		background: var(--bg-card);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
		box-shadow: var(--shadow-md);
		border: 1px solid var(--border-light);
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.stat-icon {
		font-size: var(--font-size-3xl);
	}

	.stat-info {
		flex: 1;
	}

	.stat-title {
		font-weight: var(--font-weight-medium);
		color: var(--color-gray-500);
		font-size: var(--font-size-sm);
		text-transform: capitalize;
	}

	.stat-number {
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-gray-800);
	}

	.error {
		background-color: var(--bg-error);
		border: 1px solid var(--border-error);
		border-radius: var(--radius-md);
		padding: var(--spacing-md);
		margin: var(--spacing-md) 0;
		color: var(--color-error);
	}

	.navigation {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: var(--spacing-xl);
		padding-top: var(--spacing-xl);
		border-top: 1px solid var(--border-light);
	}

	.back-link, .danger-link {
		text-decoration: none;
		font-weight: var(--font-weight-medium);
		padding: var(--spacing-sm) var(--spacing-md);
		border-radius: var(--radius-sm);
		transition: background-color var(--transition-normal);
	}

	.back-link {
		color: var(--color-primary);
	}

	.back-link:hover {
		background-color: var(--bg-info);
	}

	.danger-link {
		color: var(--color-error);
		border: 1px solid var(--border-error);
	}

	.danger-link:hover {
		background-color: var(--bg-error);
	}
</style>