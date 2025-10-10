<!-- Reusable Input component using existing design tokens -->
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
		oninput?: (event: Event) => void;
		onchange?: (event: Event) => void;
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
		oninput,
		onchange
	}: Props = $props();
	
	const inputId = Math.random().toString(36).substr(2, 9);
	const hasError = $derived(!!error);
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
	
	<input
		id={inputId}
		{type}
		{placeholder}
		{required}
		{disabled}
		bind:value
		class="form-input"
		class:form-input-error={hasError}
		{oninput}
		{onchange}
		aria-invalid={hasError}
		aria-describedby={error ? `${inputId}-error` : help ? `${inputId}-help` : undefined}
	/>
	
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
</style>