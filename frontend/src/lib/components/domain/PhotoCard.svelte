<!-- PhotoCard komponent med forskjellige varianter -->
<script lang="ts">
	import { Card } from '$lib/components/ui';
	
	interface Props {
		photo: any;
		variant?: 'compact' | 'detailed' | 'grid' | 'list';
		showActions?: boolean;
		clickable?: boolean;
		onclick?: () => void;
	}
	
	let { 
		photo, 
		variant = 'grid',
		showActions = false,
		clickable = false,
		onclick
	}: Props = $props();
	
	const cardClasses = $derived([
		'photo-card',
		`photo-card--${variant}`,
		clickable ? 'photo-card--clickable' : null
	].filter(Boolean).join(' '));
</script>

<Card 
	class={cardClasses}
	onclick={clickable ? onclick : undefined}
	padding={variant === 'compact' ? 'sm' : 'md'}
>
	<!-- Thumbnail basert på variant -->
	{#if variant === 'list'}
		<div class="photo-content-horizontal">
			<div class="photo-thumbnail-small">
				{#if photo.hotpreview}
					<img 
						src="data:image/jpeg;base64,{photo.hotpreview}" 
						alt={photo.primary_filename || photo.hothash}
					/>
				{:else}
					<div class="photo-placeholder">📸</div>
				{/if}
			</div>
			<div class="photo-info">
				<h4 class="photo-filename">{photo.primary_filename || photo.hothash}</h4>
				{#if photo.taken_at}
					<p class="photo-date">📅 {new Date(photo.taken_at).toLocaleDateString()}</p>
				{/if}
				{#if photo.width && photo.height}
					<p class="photo-dimensions">📐 {photo.width} × {photo.height}px</p>
				{/if}
			</div>
		</div>
	{:else}
		<!-- Grid/Compact/Detailed variants -->
		<div class="photo-thumbnail">
			{#if photo.hotpreview}
				<img 
					src="data:image/jpeg;base64,{photo.hotpreview}" 
					alt={photo.primary_filename || photo.hothash}
				/>
			{:else}
				<div class="photo-placeholder">📸</div>
			{/if}
		</div>
		
		<div class="photo-info">
			<h4 class="photo-filename">{photo.primary_filename || photo.hothash}</h4>
			
			{#if variant === 'detailed'}
				<!-- Full info for detailed variant -->
				{#if photo.taken_at}
					<p class="photo-date">📅 {new Date(photo.taken_at).toLocaleDateString()} {new Date(photo.taken_at).toLocaleTimeString()}</p>
				{/if}
				
				{#if photo.title}
					<p class="photo-title">📝 {photo.title}</p>
				{/if}
				
				{#if photo.description}
					<p class="photo-description">📄 {photo.description}</p>
				{/if}
				
				{#if photo.author?.name}
					<p class="photo-author">👤 {photo.author.name}</p>
				{/if}
				
				{#if photo.width && photo.height}
					<p class="photo-dimensions">📐 {photo.width} × {photo.height}px</p>
				{/if}
				
				{#if photo.rating > 0}
					<p class="photo-rating">⭐ {'★'.repeat(photo.rating)}{'☆'.repeat(5 - photo.rating)}</p>
				{/if}
				
				{#if photo.has_gps}
					<p class="photo-gps">📍 GPS: {photo.gps_latitude?.toFixed(4)}, {photo.gps_longitude?.toFixed(4)}</p>
				{/if}
				
				{#if photo.has_raw_companion}
					<p class="photo-raw">📸 RAW + JPEG</p>
				{/if}
				
				{#if photo.files && photo.files.length > 0}
					<p class="photo-files">📁 {photo.files.length} file{photo.files.length > 1 ? 's' : ''}</p>
				{/if}
				
				{#if photo.tags && photo.tags.length > 0}
					<p class="photo-tags">🏷️ {photo.tags.join(', ')}</p>
				{/if}
			{:else if variant === 'grid'}
				<!-- Medium info for grid variant -->
				{#if photo.taken_at}
					<p class="photo-date">📅 {new Date(photo.taken_at).toLocaleDateString()}</p>
				{/if}
				
				{#if photo.width && photo.height}
					<p class="photo-dimensions">📐 {photo.width} × {photo.height}px</p>
				{/if}
			{:else if variant === 'compact'}
				<!-- Minimal info for compact variant -->
				{#if photo.taken_at}
					<p class="photo-date">{new Date(photo.taken_at).toLocaleDateString()}</p>
				{/if}
			{/if}
			
			<p class="photo-imported">⏰ Imported {new Date(photo.created_at).toLocaleDateString()}</p>
		</div>
	{/if}
	
	{#if showActions}
		<div class="photo-actions">
			<button class="action-btn">👁️ View</button>
			<button class="action-btn">✏️ Edit</button>
			<button class="action-btn">🗑️ Delete</button>
		</div>
	{/if}
</Card>

<style>
	:global(.photo-card--clickable) {
		cursor: pointer;
		transition: transform var(--transition-normal), box-shadow var(--transition-normal);
	}
	
	:global(.photo-card--clickable:hover) {
		transform: translateY(-2px);
		box-shadow: var(--shadow-xl);
	}
	
	/* Grid variant (default) */
	:global(.photo-card--grid) {
		/* Default card styling */
	}
	
	/* Compact variant */
	:global(.photo-card--compact) .photo-thumbnail {
		height: 120px;
	}
	
	:global(.photo-card--compact) .photo-info {
		padding-top: var(--spacing-xs);
	}
	
	:global(.photo-card--compact) .photo-filename {
		font-size: var(--font-size-sm);
	}
	
	/* Detailed variant */
	:global(.photo-card--detailed) .photo-thumbnail {
		height: 250px;
	}
	
	/* List variant */
	:global(.photo-card--list) {
		/* Override Card component padding for horizontal layout */
	}
	
	.photo-content-horizontal {
		display: flex;
		gap: var(--spacing-md);
		align-items: flex-start;
	}
	
	.photo-thumbnail-small {
		width: 80px;
		height: 80px;
		flex-shrink: 0;
		border-radius: var(--radius-md);
		overflow: hidden;
	}
	
	.photo-thumbnail-small img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	
	.photo-thumbnail {
		width: 100%;
		height: 200px;
		border-radius: var(--radius-md);
		overflow: hidden;
		margin-bottom: var(--spacing-sm);
	}
	
	.photo-thumbnail img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	
	.photo-placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-gray-100);
		color: var(--color-gray-400);
		font-size: 2rem;
	}
	
	.photo-info {
		flex: 1;
	}
	
	.photo-filename {
		margin: 0 0 var(--spacing-xs) 0;
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-gray-800);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	
	.photo-info p {
		margin: var(--spacing-xs) 0;
		font-size: var(--font-size-xs);
		color: var(--color-gray-600);
		line-height: var(--line-height-tight);
	}
	
	.photo-date {
		color: var(--color-gray-500);
	}
	
	.photo-title {
		color: var(--color-gray-700);
		font-weight: var(--font-weight-medium);
	}
	
	.photo-imported {
		color: var(--color-gray-400);
		font-style: italic;
	}
	
	.photo-actions {
		display: flex;
		gap: var(--spacing-xs);
		margin-top: var(--spacing-sm);
		padding-top: var(--spacing-sm);
		border-top: 1px solid var(--border-light);
	}
	
	.action-btn {
		padding: var(--spacing-xs) var(--spacing-sm);
		border: 1px solid var(--border-medium);
		border-radius: var(--radius-sm);
		background: white;
		font-size: var(--font-size-xs);
		cursor: pointer;
		transition: all var(--transition-fast);
	}
	
	.action-btn:hover {
		background: var(--color-gray-50);
		border-color: var(--border-dark);
	}
</style>