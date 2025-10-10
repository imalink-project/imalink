<script lang="ts">
	import { onMount } from 'svelte';
	import { currentView } from '$lib/stores/app';
	import { Button, Card, PageHeader } from '$lib/components/ui';

	currentView.set('imports');

	let error = $state('');
	let importSessions = $state<any[]>([]);

	// Hent importsessjoner ved lasting
	onMount(async () => {
		await fetchImportSessions();
	});

	async function fetchImportSessions() {
		try {
			const response = await fetch('/api/import-sessions');
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			const data = await response.json();
			importSessions = data.imports || [];
		} catch (e) {
			console.error('Error fetching import sessions:', e);
			error = 'Kunne ikke hente importsessjoner';
		}
	}

	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleString('no-NO');
	}

	function getStatusText(status: string) {
		const statusMap: Record<string, string> = {
			pending: 'Venter',
			running: 'Kjører',
			completed: 'Fullført',
			failed: 'Feilet'
		};
		return statusMap[status] || status;
	}

	function getStatusClass(status: string) {
		const classMap: Record<string, string> = {
			pending: 'status-pending',
			running: 'status-running',
			completed: 'status-completed',
			failed: 'status-failed'
		};
		return classMap[status] || '';
	}
</script>

<svelte:head>
	<title>Import - ImaLink</title>
</svelte:head>

<div class="import-container">
	<PageHeader 
		title="📥 Import Oversikt" 
		description="Oversikt over alle importsessjoner"
	>
		<Button variant="primary" onclick={() => window.location.href = '/import/new'}>
			➕ Ny import
		</Button>
	</PageHeader>

	{#if error}
		<div class="error-message">
			❌ {error}
		</div>
	{/if}

	<!-- Import sessions oversikt -->
	<Card>
		<h3>� Alle importsessjoner</h3>
		{#if importSessions.length === 0}
			<div class="empty-state">
				<p>Ingen importsessjoner funnet.</p>
				<p><a href="/import/new" class="link-primary">Opprett din første import</a></p>
			</div>
		{:else}
			<div class="sessions-table">
				<div class="table-header">
					<div class="col col-id">ID</div>
					<div class="col col-author">Forfatter</div>
					<div class="col col-source">Kilde</div>
					<div class="col col-status">Status</div>
					<div class="col col-date">Dato</div>
					<div class="col col-storage">Storage</div>
				</div>
				{#each importSessions as session}
					<div class="table-row">
						<div class="col col-id">{session.id}</div>
						<div class="col col-author">{session.author?.name || 'Ikke satt'}</div>
						<div class="col col-source" title={session.source_path}>
							{session.source_path?.length > 30
								? '...' + session.source_path.slice(-30)
								: session.source_path}
						</div>
						<div class="col col-status">
							<span class="status-badge {getStatusClass(session.status)}">
								{getStatusText(session.status)}
							</span>
						</div>
						<div class="col col-date">{formatDate(session.started_at)}</div>
						<div class="col col-storage">
							{session.storage_name || 'Ikke satt'}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</Card>
</div>

<style>
	.import-container {
		max-width: 800px;
		margin: 0 auto;
		padding: var(--spacing-xl);
	}



	.error-message {
		background: var(--bg-error);
		border: 1px solid var(--border-error);
		color: var(--color-error);
		padding: var(--spacing-md);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-lg);
	}

	.import-form {
		background: var(--color-gray-50);
		border: 1px solid var(--border-light);
		border-radius: var(--radius-xl);
		padding: var(--spacing-xl);
		margin-bottom: var(--spacing-lg);
	}






	.link-primary {
		color: var(--color-primary);
		text-decoration: none;
		font-weight: var(--font-weight-semibold);
	}

	.link-primary:hover {
		color: var(--color-primary-hover);
		text-decoration: underline;
	}

	h3 {
		margin: 0 0 var(--spacing-lg) 0;
		color: var(--color-gray-700);
		font-weight: var(--font-weight-semibold);
	}

	.empty-state {
		text-align: center;
		padding: var(--spacing-xl);
		color: var(--color-gray-500);
	}

	.sessions-table {
		width: 100%;
		border-radius: var(--radius-lg);
		overflow: hidden;
		border: 1px solid var(--border-light);
	}

	.table-header {
		display: flex;
		background: var(--color-gray-100);
		font-weight: var(--font-weight-semibold);
		color: var(--color-gray-700);
		border-bottom: 1px solid var(--border-light);
	}

	.table-row {
		display: flex;
		background: white;
		border-bottom: 1px solid var(--border-light);
	}

	.table-row:hover {
		background: var(--color-gray-25);
	}

	.col {
		padding: var(--spacing-md);
		border-right: 1px solid var(--border-light);
	}

	.col:last-child {
		border-right: none;
	}

	.col-id {
		flex: 0 0 60px;
		text-align: center;
	}

	.col-author {
		flex: 0 0 120px;
	}

	.col-source {
		flex: 1;
		min-width: 150px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.col-status {
		flex: 0 0 100px;
		text-align: center;
	}

	.col-date {
		flex: 0 0 140px;
		font-size: var(--font-size-sm);
	}

	.col-storage {
		flex: 0 0 140px;
		font-size: var(--font-size-sm);
		font-family: monospace;
	}

	.status-badge {
		padding: 2px 8px;
		border-radius: var(--radius-sm);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		text-transform: uppercase;
	}

	.status-pending {
		background: var(--color-yellow-100);
		color: var(--color-yellow-800);
	}

	.status-running {
		background: var(--color-blue-100);
		color: var(--color-blue-800);
	}

	.status-completed {
		background: var(--color-green-100);
		color: var(--color-green-800);
	}

	.status-failed {
		background: var(--color-red-100);
		color: var(--color-red-800);
	}
</style>