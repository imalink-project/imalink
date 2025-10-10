<!-- PhotoGrid komponent for forskjellige layouts -->
<script lang="ts">
	import PhotoCard from './PhotoCard.svelte';
	
	interface Props {
		photos: any[];
		layout?: 'grid' | 'list' | 'masonry';
		cardVariant?: 'compact' | 'detailed' | 'grid' | 'list';
		showActions?: boolean;
		onPhotoClick?: (photo: any) => void;
	}
	
	let { 
		photos, 
		layout = 'grid',
		cardVariant = 'grid',
		showActions = false,
		onPhotoClick
	}: Props = $props();
	
	// Override card variant basert på layout
	const effectiveCardVariant = $derived(
		layout === 'list' ? 'list' : cardVariant
	);
	
	const gridClasses = $derived([
		'photo-grid',
		`photo-grid--${layout}`
	].join(' '));
</script>

<div class={gridClasses}>
	{#each photos as photo}
		<PhotoCard 
			{photo} 
			variant={effectiveCardVariant}
			{showActions}
			clickable={!!onPhotoClick}
			onclick={() => onPhotoClick?.(photo)}
		/>
	{/each}
</div>

<style>
	.photo-grid {
		display: grid;
		gap: var(--spacing-lg);
	}
	
	/* Grid layout */
	.photo-grid--grid {
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
	}
	
	/* List layout */
	.photo-grid--list {
		grid-template-columns: 1fr;
		gap: var(--spacing-md);
	}
	
	/* Masonry layout */
	.photo-grid--masonry {
		columns: 3;
		column-gap: var(--spacing-lg);
	}
	
	.photo-grid--masonry :global(.photo-card) {
		break-inside: avoid;
		margin-bottom: var(--spacing-lg);
	}
	
	/* Responsive breakpoints */
	@media (max-width: 768px) {
		.photo-grid--grid {
			grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		}
		
		.photo-grid--masonry {
			columns: 2;
		}
	}
	
	@media (max-width: 480px) {
		.photo-grid--grid {
			grid-template-columns: 1fr;
		}
		
		.photo-grid--masonry {
			columns: 1;
		}
	}
</style>