// Export all UI components for easy importing
export { default as Button } from './Button.svelte';
export { default as Card } from './Card.svelte';
export { default as Input } from './Input.svelte';
export { default as InputWithSuggestions } from './InputWithSuggestions.svelte';
export { default as SelectWithHistory } from './SelectWithHistory.svelte';
export { default as PageHeader } from './PageHeader.svelte';

// TypeScript types for better developer experience
export interface ButtonProps {
	variant?: 'primary' | 'success' | 'error' | 'outline';
	size?: 'sm' | 'md' | 'lg';
	disabled?: boolean;
	type?: 'button' | 'submit' | 'reset';
	loading?: boolean;
	onclick?: (event: MouseEvent) => void;
}

export interface CardProps {
	variant?: 'default' | 'compact' | 'elevated';
	padding?: 'sm' | 'md' | 'lg';
	shadow?: boolean;
}

export interface InputProps {
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

export interface PageHeaderProps {
	title: string;
	description?: string;
	icon?: string;
	actions?: any; // Snippet for action buttons
}