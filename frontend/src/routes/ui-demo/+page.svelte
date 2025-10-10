<!-- Demo page showing the new UI components -->
<script lang="ts">
	import { Button, Card, Input } from '$lib/components/ui';
	import { currentView } from '$lib/stores/app';
	
	// Set current view for navigation
	currentView.set('ui-demo' as any);
	
	let formData = $state({
		name: '',
		email: '',
		message: ''
	});
	
	let loading = $state(false);
	let submitted = $state(false);
	
	async function handleSubmit() {
		loading = true;
		// Simulate API call
		await new Promise(resolve => setTimeout(resolve, 2000));
		loading = false;
		submitted = true;
		
		setTimeout(() => {
			submitted = false;
			formData = { name: '', email: '', message: '' };
		}, 3000);
	}
</script>

<div class="space-y-lg">
	<div>
		<h1 class="text-3xl font-bold">UI Components Demo</h1>
		<p class="text-muted">Eksempler på hvordan de nye komponentene kan brukes</p>
	</div>

	<!-- Buttons Demo -->
	<Card>
		<h2 class="text-xl font-semibold">Buttons</h2>
		<div class="space-y-md">
			<div class="flex gap-md">
				<Button variant="primary">Primary</Button>
				<Button variant="success">Success</Button>
				<Button variant="error">Error</Button>
				<Button variant="outline">Outline</Button>
			</div>
			
			<div class="flex gap-md">
				<Button size="sm">Small</Button>
				<Button size="md">Medium</Button>
				<Button size="lg">Large</Button>
			</div>
			
			<div class="flex gap-md">
				<Button disabled>Disabled</Button>
				<Button loading={true}>Loading...</Button>
			</div>
		</div>
	</Card>

	<!-- Cards Demo -->
	<div class="grid grid-cols-3 gap-lg">
		<Card variant="default">
			<h3 class="font-semibold">Default Card</h3>
			<p class="text-sm text-muted">Standard card with default styling</p>
		</Card>
		
		<Card variant="compact" padding="sm">
			<h3 class="font-semibold">Compact Card</h3>
			<p class="text-sm text-muted">Smaller padding for tighter layouts</p>
		</Card>
		
		<Card variant="elevated" shadow={true}>
			<h3 class="font-semibold">Elevated Card</h3>
			<p class="text-sm text-muted">Enhanced shadow for prominence</p>
		</Card>
	</div>

	<!-- Form Demo -->
	<Card>
		<h2 class="text-xl font-semibold">Form Components</h2>
		
		{#if submitted}
			<div class="alert alert-success">
				Form submitted successfully! 🎉
			</div>
		{:else}
			<form class="space-y-md" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
				<Input
					label="Name"
					placeholder="Enter your name"
					bind:value={formData.name}
					required
					help="Your full name as you'd like it to appear"
				/>
				
				<Input
					type="email"
					label="Email"
					placeholder="your@email.com"
					bind:value={formData.email}
					required
					error={formData.email && !formData.email.includes('@') ? 'Please enter a valid email' : undefined}
				/>
				
				<Input
					label="Message"
					placeholder="Tell us something..."
					bind:value={formData.message}
					help="Optional message (max 500 characters)"
				/>
				
				<div class="flex gap-md">
					<Button type="submit" {loading} disabled={!formData.name || !formData.email}>
						{loading ? 'Submitting...' : 'Submit Form'}
					</Button>
					
					<Button 
						variant="outline" 
						type="button"
						onclick={() => formData = { name: '', email: '', message: '' }}
					>
						Reset
					</Button>
				</div>
			</form>
		{/if}
	</Card>

	<!-- Usage Example -->
	<Card variant="compact">
		<h2 class="text-lg font-semibold">How to Use</h2>
		<pre class="text-sm bg-gray-100 p-md rounded"><code>{`<script>
  import { Button, Card, Input } from '$lib/components/ui';
</script>

<Card>
  <Input label="Name" bind:value={name} required />
  <Button variant="primary" onclick={handleSubmit}>
    Submit
  </Button>
</Card>`}</code></pre>
	</Card>
</div>