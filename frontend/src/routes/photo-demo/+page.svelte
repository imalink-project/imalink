<!-- Demo side for PhotoCard varianter -->
<script lang="ts">
	import { PageHeader, Button, Card } from '$lib/components/ui';
	import PhotoCard from '$lib/components/domain/PhotoCard.svelte';
	import PhotoGrid from '$lib/components/domain/PhotoGrid.svelte';
	import { currentView } from '$lib/stores/app';
	
	// Set current view for navigation
	currentView.set('photo-demo' as any);
	
	// Sample photo data
	const samplePhoto = {
		primary_filename: "sunset_beach.jpg",
		hothash: "abc123def456",
		hotpreview: null, // Vil vise placeholder
		taken_at: "2024-08-15T18:30:00Z",
		title: "Beautiful Sunset at the Beach",
		description: "A stunning sunset captured during our vacation at the coast.",
		author: { name: "John Doe" },
		width: 3840,
		height: 2160,
		rating: 4,
		has_gps: true,
		gps_latitude: 59.9139,
		gps_longitude: 10.7522,
		has_raw_companion: true,
		files: ["sunset_beach.jpg", "sunset_beach.raw"],
		tags: ["sunset", "beach", "vacation", "nature"],
		created_at: "2024-08-16T10:15:00Z"
	};
	
	const samplePhotos = Array(6).fill(null).map((_, i) => ({
		...samplePhoto,
		primary_filename: `photo_${i + 1}.jpg`,
		hothash: `hash${i + 1}`,
		rating: Math.floor(Math.random() * 5) + 1
	}));
	
	let selectedLayout = $state('grid');
	let selectedVariant = $state('grid');
	let showActions = $state(false);
	
	function handlePhotoClick(photo: any) {
		alert(`Clicked on: ${photo.primary_filename}`);
	}
</script>

<div class="demo-page">
	<PageHeader 
		title="PhotoCard Variants Demo" 
		icon="🖼️"
		description="Se forskjellige versjoner av bildevisningskortet"
	/>

	<!-- Controls -->
	<Card>
		<h3>Kontroller</h3>
		<div class="controls">
			<div class="control-group">
				<label>Layout:</label>
				<select bind:value={selectedLayout}>
					<option value="grid">Grid</option>
					<option value="list">List</option>
					<option value="masonry">Masonry</option>
				</select>
			</div>
			
			<div class="control-group">
				<label>Card Variant:</label>
				<select bind:value={selectedVariant} disabled={selectedLayout === 'list'}>
					<option value="compact">Compact</option>
					<option value="grid">Grid (standard)</option>
					<option value="detailed">Detailed</option>
				</select>
			</div>
			
			<div class="control-group">
				<label>
					<input type="checkbox" bind:checked={showActions} />
					Vis actions
				</label>
			</div>
		</div>
	</Card>

	<!-- Single Card Examples -->
	<Card>
		<h3>Enkelte Kort Eksempler</h3>
		<div class="single-examples">
			<div class="example">
				<h4>Compact</h4>
				<div class="example-card">
					<PhotoCard photo={samplePhoto} variant="compact" showActions={true} />
				</div>
			</div>
			
			<div class="example">
				<h4>Grid (Standard)</h4>
				<div class="example-card">
					<PhotoCard photo={samplePhoto} variant="grid" showActions={true} />
				</div>
			</div>
			
			<div class="example">
				<h4>Detailed</h4>
				<div class="example-card">
					<PhotoCard photo={samplePhoto} variant="detailed" showActions={true} />
				</div>
			</div>
			
			<div class="example">
				<h4>List</h4>
				<div class="example-card-wide">
					<PhotoCard photo={samplePhoto} variant="list" showActions={true} />
				</div>
			</div>
		</div>
	</Card>

	<!-- PhotoGrid Demo -->
	<Card>
		<h3>PhotoGrid Demo - {selectedLayout} layout</h3>
		<PhotoGrid 
			photos={samplePhotos}
			layout={selectedLayout}
			cardVariant={selectedVariant}
			{showActions}
			onPhotoClick={handlePhotoClick}
		/>
	</Card>

	<!-- Usage Examples -->
	<Card>
		<h3>Hvordan Bruke</h3>
		<div class="usage-examples">
			<h4>Enkelt PhotoCard:</h4>
			<pre><code>{`<script>
  import PhotoCard from '$lib/components/domain/PhotoCard.svelte';
</script>

<!-- Compact variant -->
<PhotoCard photo={photo} variant="compact" />

<!-- Detailed variant med actions -->
<PhotoCard 
  photo={photo} 
  variant="detailed" 
  showActions={true}
  clickable={true}
  onclick={() => openPhoto(photo)}
/>

<!-- List variant -->
<PhotoCard photo={photo} variant="list" />`}</code></pre>

			<h4>PhotoGrid:</h4>
			<pre><code>{`<script>
  import PhotoGrid from '$lib/components/domain/PhotoGrid.svelte';
</script>

<!-- Grid layout med compact cards -->
<PhotoGrid 
  photos={photos}
  layout="grid"
  cardVariant="compact"
  showActions={true}
  onPhotoClick={handlePhotoClick}
/>

<!-- List layout -->
<PhotoGrid 
  photos={photos}
  layout="list"
  onPhotoClick={handlePhotoClick}
/>

<!-- Masonry layout -->
<PhotoGrid 
  photos={photos}
  layout="masonry"
  cardVariant="detailed"
/>`}</code></pre>
		</div>
	</Card>
</div>

<style>
	.demo-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: var(--spacing-lg);
		space: var(--spacing-lg);
	}
	
	.demo-page > :global(* + *) {
		margin-top: var(--spacing-lg);
	}
	
	.controls {
		display: flex;
		gap: var(--spacing-lg);
		flex-wrap: wrap;
		align-items: center;
	}
	
	.control-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}
	
	.control-group label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-gray-700);
	}
	
	.control-group select {
		padding: var(--spacing-sm);
		border: 1px solid var(--border-medium);
		border-radius: var(--radius-md);
		font-size: var(--font-size-sm);
	}
	
	.single-examples {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: var(--spacing-lg);
	}
	
	.example h4 {
		margin-bottom: var(--spacing-sm);
		font-size: var(--font-size-sm);
		color: var(--color-gray-600);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.example-card {
		max-width: 300px;
	}
	
	.example-card-wide {
		max-width: 600px;
	}
	
	.usage-examples {
		space: var(--spacing-md);
	}
	
	.usage-examples > * + * {
		margin-top: var(--spacing-md);
	}
	
	.usage-examples h4 {
		margin-bottom: var(--spacing-sm);
		color: var(--color-gray-700);
	}
	
	.usage-examples pre {
		background: var(--color-gray-50);
		padding: var(--spacing-md);
		border-radius: var(--radius-md);
		overflow-x: auto;
		font-size: var(--font-size-sm);
		border: 1px solid var(--border-light);
	}
	
	.usage-examples code {
		color: var(--color-gray-800);
	}
</style>