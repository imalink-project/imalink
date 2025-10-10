<!-- Gjenbrukbar PageHeader komponent for konsistente side-headers -->
<script lang="ts">
	interface Props {
		title: string;
		description?: string;
		icon?: string;
		actions?: any; // Snippet for action buttons
	}
	
	let { 
		title, 
		description, 
		icon,
		actions,
		children 
	}: Props & { children?: any } = $props();
</script>

<div class="page-header">
	<div class="page-header-content">
		<h1>
			{#if icon}
				<span class="header-icon">{icon}</span>
			{/if}
			{title}
		</h1>
		{#if description}
			<p class="header-description">{description}</p>
		{/if}
	</div>
	
	{#if actions || children}
		<div class="page-header-actions">
			{#if actions}
				{@render actions()}
			{/if}
			{#if children}
				{@render children()}
			{/if}
		</div>
	{/if}
</div>

<style>
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: var(--spacing-xl);
		flex-wrap: wrap;
		gap: var(--spacing-md);
	}

	.page-header-content {
		flex: 1;
		min-width: 0; /* Allows text to wrap */
	}

	.page-header h1 {
		color: var(--color-gray-800);
		margin: 0 0 var(--spacing-xs) 0;
		font-weight: var(--font-weight-bold);
		font-size: var(--font-size-3xl);
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.header-icon {
		font-size: 1.2em;
	}

	.header-description {
		color: var(--color-gray-500);
		margin: 0;
		font-size: var(--font-size-lg);
		line-height: var(--line-height-relaxed);
	}

	.page-header-actions {
		display: flex;
		gap: var(--spacing-sm);
		align-items: center;
		flex-wrap: wrap;
	}

	@media (max-width: 640px) {
		.page-header {
			flex-direction: column;
			align-items: stretch;
		}
		
		.page-header-actions {
			justify-content: flex-start;
		}
	}
</style>