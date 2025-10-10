<script lang="ts">
	import { InputHistoryService, type HistoryConfig } from '$lib/services/input-history.service';
	
	interface SelectOption {
		value: string | number;
		label: string;
		disabled?: boolean;
		isHistory?: boolean;
		isGroup?: boolean;
	}
	
	interface Props {
		label?: string;
		value?: string | number;
		options?: SelectOption[];
		required?: boolean;
		disabled?: boolean;
		error?: string;
		help?: string;
		placeholder?: string;
		multiple?: boolean;
		historyConfig?: HistoryConfig;
		onchange?: (event: Event) => void;
		onselect?: (value: string | number) => void;
	}
	
	let { 
		label,
		value = $bindable(''),
		options = [],
		required = false,
		disabled = false,
		error,
		help,
		placeholder = 'Velg en verdi...',
		multiple = false,
		historyConfig,
		onchange,
		onselect
	}: Props = $props();
	
	const selectId = Math.random().toString(36).substring(2, 9);
	const hasError = $derived(!!error);
	
	// Load recent values from history if configured
	let historyOptions = $derived.by(() => {
		if (!historyConfig) return [];
		
		const history = InputHistoryService.getHistory(historyConfig.key);
		return history.map(item => ({
			value: item,
			label: item,
			isHistory: true,
			disabled: false
		} as SelectOption));
	});
	
	// Combine options with history (history first)
	let allOptions = $derived.by(() => {
		const combined: SelectOption[] = [];
		
		// Add history options first if they exist
		if (historyOptions.length > 0) {
			combined.push({
				value: '',
				label: '--- Tidligere brukte verdier ---',
				disabled: true,
				isGroup: true
			});
			combined.push(...historyOptions);
		}
		
		// Add separator if both history and regular options exist
		if (historyOptions.length > 0 && options.length > 0) {
			combined.push({
				value: '',
				label: '--- Alle alternativer ---',
				disabled: true,
				isGroup: true
			});
		}
		
		// Add regular options
		combined.push(...options);
		
		return combined;
	});
	
	function handleChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		const selectedValue = target.value;
		
		// Save to history if configured and not empty
		if (historyConfig && selectedValue) {
			// Find the label for the selected value
			const selectedOption = options.find(opt => String(opt.value) === selectedValue);
			if (selectedOption) {
				InputHistoryService.addToHistory(historyConfig, selectedOption.label);
			}
		}
		
		onchange?.(event);
		onselect?.(selectedValue);
	}
</script>

<div class="form-group">
	{#if label}
		<label for={selectId} class="form-label">
			{label}
			{#if required}
				<span class="text-error">*</span>
			{/if}
		</label>
	{/if}
	
	{#if multiple}
		<select
			id={selectId}
			bind:value
			{required}
			{disabled}
			multiple
			class="form-select"
			class:form-select-error={hasError}
			onchange={handleChange}
			aria-invalid={hasError}
			aria-describedby={error ? `${selectId}-error` : help ? `${selectId}-help` : undefined}
		>
			{#if placeholder}
				<option value="" disabled>{placeholder}</option>
			{/if}
			{#each allOptions as option}
				{#if option.isGroup}
					<option value={option.value} disabled class="group-header">
						{option.label}
					</option>
				{:else}
					<option 
						value={option.value} 
						disabled={option.disabled}
						class:history-option={option.isHistory}
					>
						{option.label}
					</option>
				{/if}
			{/each}
		</select>
	{:else}
		<select
			id={selectId}
			bind:value
			{required}
			{disabled}
			class="form-select"
			class:form-select-error={hasError}
			onchange={handleChange}
			aria-invalid={hasError}
			aria-describedby={error ? `${selectId}-error` : help ? `${selectId}-help` : undefined}
		>
			{#if placeholder}
				<option value="" disabled>{placeholder}</option>
			{/if}
			{#each allOptions as option}
				{#if option.isGroup}
					<option value={option.value} disabled class="group-header">
						{option.label}
					</option>
				{:else}
					<option 
						value={option.value} 
						disabled={option.disabled}
						class:history-option={option.isHistory}
					>
						{option.label}
					</option>
				{/if}
			{/each}
		</select>
	{/if}
	
	{#if error}
		<div id="{selectId}-error" class="form-error">
			{error}
		</div>
	{/if}
	
	{#if help && !error}
		<div id="{selectId}-help" class="form-help">
			{help}
		</div>
	{/if}
</div>

<style>
	.form-group {
		margin-bottom: var(--spacing-md);
	}
	
	.form-select-error {
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
	
	.group-header {
		font-weight: var(--font-weight-semibold);
		color: var(--color-gray-600);
		background: var(--color-gray-100);
		font-style: italic;
	}
	
	.history-option {
		color: var(--color-primary);
		font-style: italic;
	}
</style>
