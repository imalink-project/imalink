/**
 * Service for managing input history and suggestions in localStorage
 */

export interface HistoryConfig {
	key: string;
	maxItems?: number;
	unique?: boolean;
}

export class InputHistoryService {
	private static readonly DEFAULT_MAX_ITEMS = 20;
	
	/**
	 * Add a value to history for a specific key
	 */
	static addToHistory(config: HistoryConfig, value: string): void {
		if (!value || !value.trim()) return;
		
		const { key, maxItems = this.DEFAULT_MAX_ITEMS, unique = true } = config;
		const trimmedValue = value.trim();
		
		try {
			const existing = this.getHistory(key);
			let updated = [trimmedValue];
			
			if (unique) {
				// Remove existing instance and add to front
				updated = [trimmedValue, ...existing.filter(item => item !== trimmedValue)];
			} else {
				// Just add to front
				updated = [trimmedValue, ...existing];
			}
			
			// Limit size
			if (updated.length > maxItems) {
				updated = updated.slice(0, maxItems);
			}
			
			localStorage.setItem(key, JSON.stringify(updated));
		} catch (error) {
			console.warn(`Failed to save history for ${key}:`, error);
		}
	}
	
	/**
	 * Get history for a specific key
	 */
	static getHistory(key: string): string[] {
		try {
			const stored = localStorage.getItem(key);
			if (stored) {
				const parsed = JSON.parse(stored);
				return Array.isArray(parsed) ? parsed : [];
			}
		} catch (error) {
			console.warn(`Failed to load history for ${key}:`, error);
		}
		return [];
	}
	
	/**
	 * Clear history for a specific key
	 */
	static clearHistory(key: string): void {
		try {
			localStorage.removeItem(key);
		} catch (error) {
			console.warn(`Failed to clear history for ${key}:`, error);
		}
	}
	
	/**
	 * Get filtered suggestions based on current input
	 */
	static getSuggestions(key: string, currentValue: string, maxItems: number = 10): string[] {
		if (!currentValue) return this.getHistory(key).slice(0, maxItems);
		
		const history = this.getHistory(key);
		const query = currentValue.toLowerCase();
		
		return history
			.filter(item => item.toLowerCase().includes(query))
			.slice(0, maxItems);
	}
}

// Pre-defined history keys for common use cases
export const HISTORY_KEYS = {
	AUTHOR_NAMES: 'author_names_history',
	IMPORT_PATHS: 'import_paths_history',
	STORAGE_PATHS: 'storage_paths_history',
	PHOTO_TITLES: 'photo_titles_history',
	PHOTO_DESCRIPTIONS: 'photo_descriptions_history',
	PHOTO_TAGS: 'photo_tags_history',
	LOCATIONS: 'locations_history'
} as const;