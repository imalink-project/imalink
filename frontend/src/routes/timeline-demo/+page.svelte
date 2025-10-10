<script lang="ts">
	import { Button, Card, PageHeader } from '$lib/components/ui';
	import { currentView } from '$lib/stores/app';

	currentView.set('timeline');

	// Timeline state
	let currentZoom = $state<'year' | 'month' | 'day'>('year');
	let selectedYear = $state<number | null>(null);
	let selectedMonth = $state<number | null>(null);
	let loading = $state(false);
	let error = $state('');
	
	// Timeline data from API
	let timelineData = $state<any>({
		years: [],
		months: [],
		days: []
	});

	function handleYearClick(year: number) {
		selectedYear = year;
		selectedMonth = null;
		currentZoom = 'month';
		fetchMonths(year);
	}

	function handleMonthClick(month: number) {
		selectedMonth = month;
		currentZoom = 'day';
		if (selectedYear) {
			fetchDays(selectedYear, month);
		}
	}

	function goBack() {
		if (currentZoom === 'day') {
			selectedMonth = null;
			currentZoom = 'month';
		} else if (currentZoom === 'month') {
			selectedYear = null;
			currentZoom = 'year';
		}
	}

	function resetToYears() {
		selectedYear = null;
		selectedMonth = null;
		currentZoom = 'year';
		fetchYears();
	}

	// API functions
	async function fetchYears() {
		loading = true;
		error = '';
		try {
			const response = await fetch('/api/timeline/years');
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			const data = await response.json();
			timelineData.years = data.years || [];
		} catch (e) {
			console.error('Error fetching timeline years:', e);
			error = 'Kunne ikke hente timeline data';
		} finally {
			loading = false;
		}
	}

	async function fetchMonths(year: number) {
		loading = true;
		error = '';
		try {
			const response = await fetch(`/api/timeline/years/${year}/months`);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			const data = await response.json();
			timelineData.months = data.months || [];
		} catch (e) {
			console.error('Error fetching timeline months:', e);
			error = 'Kunne ikke hente måneder';
		} finally {
			loading = false;
		}
	}

	async function fetchDays(year: number, month: number) {
		loading = true;
		error = '';
		try {
			const response = await fetch(`/api/timeline/years/${year}/months/${month}/days`);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			const data = await response.json();
			timelineData.days = data.days || [];
		} catch (e) {
			console.error('Error fetching timeline days:', e);
			error = 'Kunne ikke hente dager';
		} finally {
			loading = false;
		}
	}

	// Initialize with years data
	$effect(() => {
		if (currentZoom === 'year') {
			fetchYears();
		}
	});

	// Get current data based on zoom level
	const currentData = $derived.by(() => {
		if (currentZoom === 'year') {
			return timelineData.years;
		} else if (currentZoom === 'month') {
			return timelineData.months;
		} else if (currentZoom === 'day') {
			return timelineData.days;
		}
		return [];
	});

	const breadcrumb = $derived.by(() => {
		if (currentZoom === 'year') return 'Timeline';
		if (currentZoom === 'month') return `${selectedYear}`;
		if (currentZoom === 'day') {
			const monthName = timelineData.months.find((m: any) => m.month === selectedMonth)?.name;
			return `${selectedYear} › ${monthName}`;
		}
		return 'Timeline';
	});
</script>

<svelte:head>
	<title>Timeline Demo - ImaLink</title>
</svelte:head>

<div class="timeline-container">
	<PageHeader 
		title="📅 Timeline Demo" 
		description="Naviger gjennom bilder basert på tid - nå med ekte API data!"
	>
		<div class="zoom-controls">
			<Button 
				variant={currentZoom === 'year' ? 'primary' : 'outline'}
				onclick={resetToYears}
			>
				År
			</Button>
			<Button 
				variant={currentZoom === 'month' ? 'primary' : 'outline'}
				disabled={!selectedYear}
			>
				Måneder
			</Button>
			<Button 
				variant={currentZoom === 'day' ? 'primary' : 'outline'}
				disabled={!selectedMonth}
			>
				Dager
			</Button>
		</div>
	</PageHeader>

	<!-- Breadcrumb Navigation -->
	<div class="breadcrumb">
		<span class="breadcrumb-text">{breadcrumb}</span>
		{#if currentZoom !== 'year'}
			<Button variant="outline" size="sm" onclick={goBack}>
				← Tilbake
			</Button>
		{/if}
	</div>

	<!-- Error message -->
	{#if error}
		<div class="error-message">
			❌ {error}
		</div>
	{/if}

	<!-- Loading indicator -->
	{#if loading}
		<div class="loading">
			<div class="loading-spinner"></div>
			<p>Laster timeline data...</p>
		</div>
	{/if}

	<!-- Timeline Content -->
	<div class="timeline-content">
		{#each currentData as item}
			<Card>
				<div class="timeline-entry">
					<div class="timeline-image">
						<img 
							src={item.pilot_image?.thumbnail_url || 'https://picsum.photos/200/150?random=1'} 
							alt="Timeline"
							loading="lazy"
						/>
					</div>
					<div class="timeline-info">
						<div class="timeline-title">
							{#if currentZoom === 'year'}
								{item.year}
							{:else if currentZoom === 'month'}
								{item.name}
							{:else}
								{item.day}. oktober
							{/if}
						</div>
						<div class="timeline-stats">
							<span class="photo-count">📸 {item.photo_count} bilder</span>
							{#if currentZoom === 'year' && item.month_count}
								<span class="month-count">📅 {item.month_count} måneder</span>
							{/if}
						</div>
						<div class="timeline-actions">
							{#if currentZoom === 'year'}
								<Button size="sm" onclick={() => handleYearClick(item.year)}>
									Utforsk år
								</Button>
							{:else if currentZoom === 'month'}
								<Button size="sm" onclick={() => handleMonthClick(item.month)}>
									Vis dager
								</Button>
							{:else}
								<Button size="sm" variant="primary">
									Se bilder
								</Button>
							{/if}
						</div>
					</div>
				</div>
			</Card>
		{/each}

		{#if !loading && currentData.length === 0 && !error}
			<div class="empty-state">
				<p>Ingen data funnet for dette tidsintervallet.</p>
				<p>Prøv å importere noen bilder først.</p>
			</div>
		{/if}
	</div>

	<!-- Demo Info -->
	<Card>
		<h3>🚀 Live Timeline API Demo</h3>
		<p>Dette er nå koblet til den faktiske backend API-en og viser ekte data fra databasen:</p>
		<ul>
			<li><strong>År-visning:</strong> Viser alle år som har importerte bilder</li>
			<li><strong>Måned-visning:</strong> Måneder med bilder for det valgte året</li>
			<li><strong>Dag-visning:</strong> Spesifikke dager med bilder for den valgte måneden</li>
		</ul>
		<p>API-endepunkter som brukes:</p>
		<div class="demo-features">
			<div class="feature">
				<strong>🔗 /api/timeline/years:</strong> Henter år med bilde-counts og pilot-bilder
			</div>
			<div class="feature">
				<strong>🔗 /api/timeline/years/[year]/months:</strong> Henter måneder for et bestemt år
			</div>
			<div class="feature">
				<strong>🔗 /api/timeline/years/[year]/months/[month]/days:</strong> Henter dager for en måned
			</div>
		</div>
	</Card>
</div>

<style>
	.timeline-container {
		max-width: 1000px;
		margin: 0 auto;
		padding: var(--spacing-xl);
		gap: var(--spacing-lg);
		display: flex;
		flex-direction: column;
	}

	.zoom-controls {
		display: flex;
		gap: var(--spacing-sm);
	}

	.breadcrumb {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-md);
		background: var(--color-gray-50);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-lg);
	}

	.breadcrumb-text {
		font-weight: var(--font-weight-semibold);
		color: var(--color-gray-700);
		font-size: var(--font-size-lg);
	}

	.error-message {
		background: var(--bg-error);
		border: 1px solid var(--border-error);
		color: var(--color-error);
		padding: var(--spacing-md);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-lg);
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--color-gray-600);
	}

	.empty-state {
		text-align: center;
		padding: var(--spacing-xl);
		color: var(--color-gray-500);
	}

	.timeline-content {
		display: grid;
		gap: var(--spacing-lg);
	}

	.timeline-entry {
		display: flex;
		gap: var(--spacing-lg);
		align-items: center;
	}

	.timeline-image {
		flex-shrink: 0;
		width: 120px;
		height: 90px;
		border-radius: var(--radius-lg);
		overflow: hidden;
		background: var(--color-gray-100);
	}

	.timeline-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		transition: transform var(--transition-normal);
	}

	.timeline-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.timeline-title {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-gray-800);
	}

	.timeline-stats {
		display: flex;
		gap: var(--spacing-md);
		color: var(--color-gray-600);
		font-size: var(--font-size-sm);
	}

	.photo-count, .month-count {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.timeline-actions {
		margin-top: var(--spacing-xs);
	}

	h3 {
		margin: 0 0 var(--spacing-md) 0;
		color: var(--color-blue-800);
	}

	p {
		margin-bottom: var(--spacing-md);
		color: var(--color-gray-700);
	}

	ul {
		margin-bottom: var(--spacing-md);
		padding-left: var(--spacing-lg);
	}

	li {
		margin-bottom: var(--spacing-xs);
		color: var(--color-gray-700);
	}

	.demo-features {
		display: grid;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-md);
	}

	.feature {
		padding: var(--spacing-sm);
		background: white;
		border-radius: var(--radius-md);
		color: var(--color-gray-700);
		font-size: var(--font-size-sm);
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.timeline-entry {
			flex-direction: column;
			text-align: center;
			gap: var(--spacing-md);
		}

		.timeline-image {
			width: 100%;
			max-width: 200px;
			height: 150px;
		}

		.timeline-stats {
			justify-content: center;
		}

		.breadcrumb {
			flex-direction: column;
			gap: var(--spacing-sm);
		}

		.zoom-controls {
			justify-content: center;
			flex-wrap: wrap;
		}
	}
</style>