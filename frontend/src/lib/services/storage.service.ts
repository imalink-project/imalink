/**
 * Storage service for managing permanent file archiving in ImportSession system
 */

export interface StorageProgress {
	import_id: number;
	status: 'not_started' | 'in_progress' | 'completed' | 'failed';
	progress_percentage: number;
	files_processed: number;
	total_files: number;
	files_copied: number;
	files_skipped: number;
	total_size_mb: number;
	current_file?: string;
	errors: string[];
	started_at?: string;
	completed_at?: string;
	storage_uuid?: string;
	storage_directory_name?: string;
	has_permanent_storage: boolean;
}

export interface StorageResult {
	success: boolean;
	message: string;
	import_id?: number;
	total_size_mb?: number;
	files_verified?: number;
	errors?: string[];
	storage_uuid?: string;
	storage_directory_name?: string;
}

/**
 * Service for handling permanent storage operations via ImportSession API
 */
export class StorageService {
	private baseUrl = 'http://localhost:8000/api/v1/import_sessions';

	/**
	 * Prepare permanent storage for an ImportSession
	 * Creates UUID-based storage directory and configures ImportSession
	 */
	async prepareStorage(importId: number, sessionName?: string): Promise<StorageResult> {
		try {
			const url = `${this.baseUrl}/${importId}/prepare-storage`;
			const body = sessionName ? { session_name: sessionName } : {};

			const response = await fetch(url, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(body)
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || `HTTP ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error('Failed to prepare storage:', error);
			return {
				success: false,
				message: `Failed to prepare storage: ${error instanceof Error ? error.message : String(error)}`
			};
		}
	}

	/**
	 * Start copying files to permanent storage
	 * Begins background process to copy all ImportSession files
	 */
	async startStorageCopy(importId: number): Promise<StorageResult> {
		try {
			const url = `${this.baseUrl}/${importId}/copy-to-permanent-storage`;

			const response = await fetch(url, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || `HTTP ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error('Failed to start storage copy:', error);
			return {
				success: false,
				message: `Failed to start storage copy: ${error instanceof Error ? error.message : String(error)}`
			};
		}
	}

	/**
	 * Get storage operation status and progress
	 * Returns current status of storage copy operation
	 */
	async getStorageStatus(importId: number): Promise<StorageProgress | null> {
		try {
			const url = `${this.baseUrl}/${importId}/storage-status`;

			const response = await fetch(url, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				if (response.status === 404) {
					return null; // ImportSession not found
				}
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || `HTTP ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error('Failed to get storage status:', error);
			return null;
		}
	}

	/**
	 * Verify storage integrity
	 * Checks that all files were copied correctly to permanent storage
	 */
	async verifyStorage(importId: number): Promise<StorageResult> {
		try {
			const url = `${this.baseUrl}/${importId}/verify-storage`;

			const response = await fetch(url, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || `HTTP ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error('Failed to verify storage:', error);
			return {
				success: false,
				message: `Failed to verify storage: ${error instanceof Error ? error.message : String(error)}`
			};
		}
	}

	/**
	 * Poll storage status until completion or failure
	 * Useful for monitoring background copy operations
	 */
	async pollStorageStatus(
		importId: number,
		onProgress?: (progress: StorageProgress) => void,
		pollInterval = 1000
	): Promise<StorageProgress | null> {
		return new Promise((resolve) => {
			const poll = async () => {
				const progress = await this.getStorageStatus(importId);
				
				if (!progress) {
					resolve(null);
					return;
				}

				if (onProgress) {
					onProgress(progress);
				}

				// Continue polling if still in progress
				if (progress.status === 'in_progress') {
					setTimeout(poll, pollInterval);
				} else {
					resolve(progress);
				}
			};

			poll();
		});
	}

	/**
	 * Get formatted storage size string
	 */
	formatStorageSize(sizeMb: number): string {
		if (sizeMb < 1024) {
			return `${sizeMb} MB`;
		} else {
			const sizeGb = (sizeMb / 1024).toFixed(1);
			return `${sizeGb} GB`;
		}
	}

	/**
	 * Get human-readable status description
	 */
	getStatusDescription(status: string): string {
		switch (status) {
			case 'not_started':
				return 'Not started';
			case 'in_progress':
				return 'Copying files...';
			case 'completed':
				return 'Copy completed successfully';
			case 'failed':
				return 'Copy failed';
			default:
				return 'Unknown status';
		}
	}
}

// Export singleton instance
export const storageService = new StorageService();