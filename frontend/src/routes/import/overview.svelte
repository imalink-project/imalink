<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let imports = [];
	let loading = true;
	let error = '';

	onMount(async () => {
		await loadImports();
	});

	async function loadImports() {
		loading = true;
		error = '';
		
		try {
			const response = await fetch('http://localhost:8000/api/v1/import_sessions/');
			if (response.ok) {
				const data = await response.json();
				imports = data.imports || [];
			} else {
				error = `Failed to load imports: ${response.status}`;
			}
		} catch (err) {
			error = `Error loading imports: ${err.message}`;
		} finally {
			loading = false;
		}
	}

	function startNewImport() {
		goto('/import/new');
	}

	function getStatusColor(status: string) {
		switch(status) {
			case 'completed': return 'text-green-600';
			case 'processing': return 'text-blue-600';
			case 'failed': return 'text-red-600';
			default: return 'text-gray-600';
		}
	}

	function formatDate(dateString: string) {
		if (!dateString) return 'Unknown';
		return new Date(dateString).toLocaleString();
	}
</script>

<div class="container mx-auto p-6">
	<div class="mb-6 flex justify-between items-center">
		<h1 class="text-3xl font-bold text-gray-800">Import Sessions</h1>
		<button 
			on:click={startNewImport}
			class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg flex items-center gap-2"
		>
			<span class="text-xl">+</span>
			New Import
		</button>
	</div>

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<span class="ml-3 text-gray-600">Loading imports...</span>
		</div>
	{:else if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
			<p class="text-red-600">⚠️ {error}</p>
			<button 
				on:click={loadImports}
				class="mt-2 text-sm bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded"
			>
				Retry
			</button>
		</div>
	{:else if imports.length === 0}
		<div class="text-center py-12">
			<p class="text-gray-500 text-lg mb-4">No import sessions found</p>
			<button 
				on:click={startNewImport}
				class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg"
			>
				Create Your First Import
			</button>
		</div>
	{:else}
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
			{#each imports as importSession}
				<div class="bg-white rounded-lg shadow-md border border-gray-200 p-6">
					<div class="flex justify-between items-start mb-4">
						<h3 class="text-lg font-semibold text-gray-800">
							Session {importSession.id}
						</h3>
						<span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(importSession.status)} bg-gray-100">
							{importSession.status}
						</span>
					</div>

					<div class="space-y-2 text-sm text-gray-600">
						<div>
							<span class="font-medium">Source:</span>
							<div class="truncate" title={importSession.source_path}>
								{importSession.source_path}
							</div>
						</div>

						{#if importSession.storage_name}
							<div>
								<span class="font-medium">Storage:</span>
								<div class="truncate font-mono text-xs" title={importSession.storage_name}>
									{importSession.storage_name}
								</div>
							</div>
						{:else}
							<div class="text-amber-600">
								<span class="font-medium">Storage:</span> Not configured
							</div>
						{/if}

						<div class="flex justify-between">
							<span><span class="font-medium">Files:</span> {importSession.total_files_found || 0}</span>
							<span><span class="font-medium">Imported:</span> {importSession.images_imported || 0}</span>
						</div>

						{#if importSession.duplicates_skipped > 0}
							<div class="text-amber-600">
								<span class="font-medium">Duplicates:</span> {importSession.duplicates_skipped} skipped
							</div>
						{/if}

						<div class="pt-2 border-t border-gray-100">
							<div class="text-xs">
								<div><span class="font-medium">Started:</span> {formatDate(importSession.started_at)}</div>
								{#if importSession.completed_at}
									<div><span class="font-medium">Completed:</span> {formatDate(importSession.completed_at)}</div>
								{/if}
							</div>
						</div>
					</div>

					<div class="mt-4 flex gap-2">
						{#if importSession.status === 'processing'}
							<button class="flex-1 bg-blue-100 text-blue-700 py-1 px-3 rounded text-sm font-medium">
								In Progress...
							</button>
						{:else}
							<button class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-1 px-3 rounded text-sm font-medium">
								View Details
							</button>
						{/if}
					</div>
				</div>
			{/each}
		</div>

		<div class="mt-6 text-center">
			<button 
				on:click={loadImports}
				class="text-sm text-gray-500 hover:text-gray-700 underline"
			>
				Refresh List
			</button>
		</div>
	{/if}
</div>

<style>
	.container {
		max-width: 1200px;
	}
</style>