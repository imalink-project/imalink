<!-- Reusable Button component using existing design tokens -->
<script lang="ts">
	interface Props {
		variant?: 'primary' | 'success' | 'error' | 'outline';
		size?: 'sm' | 'md' | 'lg';
		disabled?: boolean;
		type?: 'button' | 'submit' | 'reset';
		loading?: boolean;
		onclick?: (event: MouseEvent) => void;
	}
	
	let { 
		variant = 'primary', 
		size = 'md', 
		disabled = false,
		type = 'button',
		loading = false,
		onclick,
		children 
	}: Props & { children: any } = $props();
	
	// Build CSS classes using existing utility classes
	const classes = $derived([
		'btn',
		`btn-${variant}`,
		size !== 'md' ? `btn-${size}` : null,
		loading ? 'btn-loading' : null
	].filter(Boolean).join(' '));
</script>

<button 
	{type} 
	{disabled}
	class={classes}
	onclick={onclick}
	aria-busy={loading}
>
	{#if loading}
		<span class="loading-spinner" aria-hidden="true"></span>
	{/if}
	{@render children()}
</button>

<style>
	.btn-loading {
		position: relative;
		pointer-events: none;
		opacity: 0.7;
	}
	
	.btn-loading .loading-spinner {
		margin-right: var(--spacing-sm);
	}
</style>