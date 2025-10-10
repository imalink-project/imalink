<!-- Enhanced Input component with autocomplete/suggestions support -->
<script lang="ts">
	interface Props {
		label?: string;
		placeholder?: string;
		value?: string;
		type?: 'text' | 'email' | 'password' | 'number' | 'url';
		required?: boolean;
		disabled?: boolean;
		error?: string;
		help?: string;
		suggestions?: string[];
		maxSuggestions?: number;
		oninput?: (event: Event) => void;
		onchange?: (event: Event) => void;
		onselect?: (value: string) => void;
	}
	
	let { 
		label,
		placeholder,
		value = $bindable(''),
		type = 'text',
		required = false,
		disabled = false,
		error,
		help,
		suggestions = [],
		maxSuggestions = 10,
		oninput,
		onchange,
		onselect
	}: Props = $props();
	
	const inputId = Math.random().toString(36).substring(2, 9);
	const listId = `${inputId}-suggestions`;
	const hasError = $derived(!!error);
	
	let showSuggestions = $state(false);
	let filteredSuggestions = $derived.by(() => {
		if (!value || !suggestions.length) return [];
		
		const query = value.toLowerCase();
		return suggestions
			.filter(suggestion => suggestion.toLowerCase().includes(query))
			.slice(0, maxSuggestions);
	});
	
	function handleInput(event: Event) {
		showSuggestions = true;
		oninput?.(event);
	}
	
	function handleChange(event: Event) {
		showSuggestions = false;
		onchange?.(event);
	}
	
	function selectSuggestion(suggestion: string) {
		value = suggestion;
		showSuggestions = false;
		onselect?.(suggestion);
	}
	
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			showSuggestions = false;
		}
	}
	
	function handleBlur() {
		// Delay hiding suggestions to allow clicks
		setTimeout(() => {
			showSuggestions = false;
		}, 200);
	}
	
	function handleFocus() {
		if (filteredSuggestions.length > 0) {
			showSuggestions = true;
		}
	}
</script>

<div class="form-group">
	{#if label}
		<label for={inputId} class="form-label">
			{label}
			{#if required}
				<span class="text-error">*</span>
			{/if}
		</label>
	{/if}
	
	<div class="input-container">
		<input
			id={inputId}
			{type}
			{placeholder}
			{required}
			{disabled}
			bind:value
			class="form-input"
			class:form-input-error={hasError}
			oninput={handleInput}
			onchange={handleChange}
			onkeydown={handleKeydown}
			onfocus={handleFocus}
			onblur={handleBlur}
			aria-invalid={hasError}
			aria-describedby={error ? `${inputId}-error` : help ? `${inputId}-help` : undefined}
			list={suggestions.length > 0 ? listId : undefined}
		/>
		
		{#if showSuggestions && filteredSuggestions.length > 0}
			<div class="suggestions-dropdown">
				{#each filteredSuggestions as suggestion}
					<button
						type="button"
						class="suggestion-item"
						onclick={() => selectSuggestion(suggestion)}
					>
						{suggestion}
					</button>
				{/each}
			</div>
		{/if}
	</div>
	
	{#if error}
		<div id="{inputId}-error" class="form-error">
			{error}
		</div>
	{/if}
	
	{#if help && !error}
		<div id="{inputId}-help" class="form-help">
			{help}
		</div>
	{/if}
</div>

<style>
	.form-group {
		margin-bottom: var(--spacing-md);
	}
	
	.input-container {
		position: relative;
	}
	
	.form-input-error {
		border-color: var(--color-error) !important;
		box-shadow: 0 0 0 1px var(--color-error) !important;
	}
	
	.form-error {
		color: var(--color-error);
		font-size: var(--font-size-sm);
		margin-top: var(--spacing-xs);
	}
	
	.form-help {
		color: var(--color-gray-500);
		font-size: var(--font-size-sm);
		margin-top: var(--spacing-xs);
	}
	
	.suggestions-dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		background: white;
		border: 1px solid var(--border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-lg);
		z-index: 1000;
		max-height: 200px;
		overflow-y: auto;
	}
	
	.suggestion-item {
		display: block;
		width: 100%;
		padding: var(--spacing-sm) var(--spacing-md);
		border: none;
		background: transparent;
		text-align: left;
		cursor: pointer;
		font-size: var(--font-size-base);
		color: var(--color-gray-700);
		transition: background-color 0.2s ease;
	}
	
	.suggestion-item:hover {
		background: var(--color-gray-50);
	}
	
	.suggestion-item:focus {
		background: var(--color-primary-50);
		outline: none;
	}
</style>