// Export domain-specific components
export { default as PhotoCard } from './PhotoCard.svelte';
export { default as PhotoGrid } from './PhotoGrid.svelte';

// TypeScript interfaces
export interface PhotoCardProps {
	photo: any;
	variant?: 'compact' | 'detailed' | 'grid' | 'list';
	showActions?: boolean;
	clickable?: boolean;
	onclick?: () => void;
}

export interface PhotoGridProps {
	photos: any[];
	layout?: 'grid' | 'list' | 'masonry';
	cardVariant?: 'compact' | 'detailed' | 'grid' | 'list';
	showActions?: boolean;
	onPhotoClick?: (photo: any) => void;
}