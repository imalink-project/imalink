<script lang="ts">
	import { onMount } from 'svelte';
	import { currentView } from '$lib/stores/app';

	currentView.set('authors');

	let authors = [];
	let loading = true;
	let error = '';
	let showAddForm = false;
	let newAuthor = {
		name: '',
		email: '',
		website: ''
	};

	onMount(async () => {
		await loadAuthors();
	});

	async function loadAuthors() {
		loading = true;
		error = '';
		
		try {
			const response = await fetch('http://localhost:8000/api/v1/authors/');
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			const data = await response.json();
			authors = data.data || [];
		} catch (err) {
			console.error('Failed to load authors:', err);
			error = err.message || 'Failed to load authors';
		} finally {
			loading = false;
		}
	}

	async function addAuthor() {
		if (!newAuthor.name.trim()) {
			alert('Author name is required');
			return;
		}

		try {
			const response = await fetch('http://localhost:8000/api/v1/authors/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					name: newAuthor.name.trim(),
					email: newAuthor.email.trim() || null,
					website: newAuthor.website.trim() || null
				})
			});

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			// Reset form and reload authors
			newAuthor = { name: '', email: '', website: '' };
			showAddForm = false;
			await loadAuthors();
		} catch (err) {
			console.error('Failed to add author:', err);
			alert('Failed to add author: ' + err.message);
		}
	}

	async function deleteAuthor(id) {
		if (!confirm('Are you sure you want to delete this author?')) {
			return;
		}

		try {
			const response = await fetch(`http://localhost:8000/api/v1/authors/${id}/`, {
				method: 'DELETE'
			});

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			await loadAuthors();
		} catch (err) {
			console.error('Failed to delete author:', err);
			alert('Failed to delete author: ' + err.message);
		}
	}

	function cancelAdd() {
		showAddForm = false;
		newAuthor = { name: '', email: '', website: '' };
	}
</script>

<div class="authors-page">
	<div class="page-header">
		<h1>👤 Authors</h1>
		<p>Manage photographers and content creators</p>
		<div class="header-actions">
			<button onclick={loadAuthors} class="refresh-btn">🔄 Refresh</button>
			<button onclick={() => showAddForm = true} class="add-btn">➕ Add Author</button>
		</div>
	</div>

	{#if showAddForm}
		<div class="add-form">
			<h3>Add New Author</h3>
			<div class="form-group">
				<label for="author-name">Name *</label>
				<input 
					id="author-name"
					type="text" 
					bind:value={newAuthor.name}
					placeholder="Author name"
					required
				/>
			</div>
			<div class="form-group">
				<label for="author-email">Email</label>
				<input 
					id="author-email"
					type="email" 
					bind:value={newAuthor.email}
					placeholder="author@example.com"
				/>
			</div>
			<div class="form-group">
				<label for="author-website">Website</label>
				<input 
					id="author-website"
					type="url" 
					bind:value={newAuthor.website}
					placeholder="https://example.com"
				/>
			</div>
			<div class="form-actions">
				<button onclick={addAuthor} class="save-btn">💾 Save</button>
				<button onclick={cancelAdd} class="cancel-btn">❌ Cancel</button>
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading authors...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>❌ {error}</p>
			<button onclick={loadAuthors} class="retry-btn">Try Again</button>
		</div>
	{:else if authors.length === 0}
		<div class="empty-state">
			<h3>📋 No authors found</h3>
			<p>Add your first author to get started!</p>
			<button onclick={() => showAddForm = true} class="add-first-btn">➕ Add First Author</button>
		</div>
	{:else}
		<div class="authors-grid">
			{#each authors as author}
				<div class="author-card">
					<div class="author-info">
						<h4 class="author-name">{author.name}</h4>
						{#if author.email}
							<p class="author-email">✉️ {author.email}</p>
						{/if}
						{#if author.website}
							<p class="author-website">
								🌐 <a href={author.website} target="_blank" rel="noopener noreferrer">
									{author.website}
								</a>
							</p>
						{/if}
						<p class="author-stats">📸 {author.photo_count || 0} photos</p>
						<p class="author-created">📅 Created: {new Date(author.created_at).toLocaleDateString()}</p>
					</div>
					<div class="author-actions">
						<button onclick={() => deleteAuthor(author.id)} class="delete-btn">🗑️ Delete</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.authors-page {
		max-width: 1200px;
		margin: 0 auto;
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
		margin: 0;
		font-size: 2rem;
		color: #1f2937;
	}

	.page-header p {
		margin: 0;
		color: #6b7280;
		flex-grow: 1;
	}

	.header-actions {
		display: flex;
		gap: 0.5rem;
	}

	.refresh-btn, .add-btn, .retry-btn, .save-btn, .cancel-btn, .delete-btn, .add-first-btn {
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		cursor: pointer;
		font-weight: 500;
		transition: background-color 0.2s ease;
	}

	.refresh-btn, .retry-btn {
		background: #3b82f6;
		color: white;
	}

	.refresh-btn:hover, .retry-btn:hover {
		background: #2563eb;
	}

	.add-btn, .add-first-btn {
		background: #10b981;
		color: white;
	}

	.add-btn:hover, .add-first-btn:hover {
		background: #059669;
	}

	.save-btn {
		background: #10b981;
		color: white;
	}

	.save-btn:hover {
		background: #059669;
	}

	.cancel-btn {
		background: #6b7280;
		color: white;
	}

	.cancel-btn:hover {
		background: #4b5563;
	}

	.delete-btn {
		background: #dc2626;
		color: white;
		font-size: 0.875rem;
		padding: 0.375rem 0.75rem;
	}

	.delete-btn:hover {
		background: #b91c1c;
	}

	.add-form {
		background: white;
		padding: 1.5rem;
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		margin-bottom: 2rem;
	}

	.add-form h3 {
		margin: 0 0 1rem 0;
		color: #1f2937;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	.form-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #374151;
	}

	.form-group input {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 1rem;
	}

	.form-group input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 1px #3b82f6;
	}

	.form-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1.5rem;
	}

	.loading {
		text-align: center;
		padding: 4rem 0;
	}

	.spinner {
		border: 4px solid #f3f4f6;
		border-left-color: #3b82f6;
		border-radius: 50%;
		width: 40px;
		height: 40px;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error {
		text-align: center;
		padding: 4rem 0;
		color: #dc2626;
	}

	.empty-state {
		text-align: center;
		padding: 4rem 0;
		color: #6b7280;
	}

	.authors-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 1.5rem;
	}

	.author-card {
		background: white;
		border-radius: 0.5rem;
		overflow: hidden;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		transition: transform 0.2s ease, box-shadow 0.2s ease;
		display: flex;
		flex-direction: column;
	}

	.author-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.author-info {
		padding: 1.5rem;
		flex-grow: 1;
	}

	.author-name {
		margin: 0 0 0.75rem 0;
		font-size: 1.25rem;
		font-weight: 600;
		color: #1f2937;
	}

	.author-email, .author-website, .author-stats, .author-created {
		margin: 0.5rem 0;
		font-size: 0.875rem;
		color: #6b7280;
	}

	.author-website a {
		color: #3b82f6;
		text-decoration: none;
		word-break: break-all;
	}

	.author-website a:hover {
		text-decoration: underline;
	}

	.author-actions {
		padding: 1rem 1.5rem;
		border-top: 1px solid #f3f4f6;
		display: flex;
		justify-content: flex-end;
	}
</style>