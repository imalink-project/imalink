<!-- Reusable Card component using existing design tokens -->
<script lang="ts">
	interface Props {
		variant?: 'default' | 'compact' | 'elevated';
		padding?: 'sm' | 'md' | 'lg';
		shadow?: boolean;
	}
	
	let { 
		variant = 'default',
		padding = 'lg',
		shadow = true,
		children 
	}: Props & { children: any } = $props();
	
	const classes = $derived([
		'card',
		variant === 'compact' ? 'card-compact' : null,
		!shadow ? 'card-no-shadow' : null,
		padding !== 'lg' ? `card-padding-${padding}` : null
	].filter(Boolean).join(' '));
</script>

<div class={classes}>
	{@render children()}
</div>

<style>
	.card-no-shadow {
		box-shadow: none;
		border: 1px solid var(--border-light);
	}
	
	.card-padding-sm {
		padding: var(--spacing-sm);
	}
	
	.card-padding-md {
		padding: var(--spacing-md);
	}
	
	.card-elevated {
		box-shadow: var(--shadow-lg);
		border: none;
	}
</style>