// Import Sessions API client with progress tracking
import { apiClient } from './client';
import type { ImportSession, ImportStartRequest } from '../types/api';

export class ImportSessionsApi {
  // Start new import session
  static async startImport(request: ImportStartRequest): Promise<{ import_id: number; status: string; message: string }> {
    const response = await apiClient.post('/import_sessions/start', request);
    return response.data;
  }

  // Upload files and start import session
  static async uploadAndImport(
    files: FileList, 
    onUploadProgress?: (progress: number) => void
  ): Promise<{ import_id: number; status: string; message: string }> {
    const formData = new FormData();
    
    // Add all files to form data with their relative paths
    Array.from(files).forEach((file, index) => {
      formData.append('files', file);
      
      // Extract relative path from file.webkitRelativePath if available (directory upload)
      // or use just the filename for individual file uploads
      const relativePath = (file as any).webkitRelativePath || file.name;
      formData.append('paths', relativePath);
    });

    const response = await apiClient.post('/import_sessions/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(progress);
        }
      }
    });
    
    return response.data;
  }

  // Get import session status
  static async getImportStatus(importId: number): Promise<ImportSession> {
    const response = await apiClient.get(`/import_sessions/status/${importId}`);
    return response.data;
  }

  // Get real-time import progress (NEW!)
  static async getImportProgress(importId: number): Promise<ImportSession> {
    const response = await apiClient.get(`/import_sessions/${importId}/progress`);
    return response.data;
  }

  // Cancel running import (NEW!)
  static async cancelImport(importId: number): Promise<{ success: boolean; message: string; status: string }> {
    const response = await apiClient.post(`/import_sessions/${importId}/cancel`);
    return response.data;
  }

  // List all import sessions
  static async listImports(): Promise<{ imports: ImportSession[]; total: number }> {
    const response = await apiClient.get('/import_sessions/');
    return response.data;
  }

  // Test single file import
  static async testSingleFile(filePath: string): Promise<any> {
    const response = await apiClient.post('/import_sessions/test-single', { file_path: filePath });
    return response.data;
  }

  // Get storage info
  static async getStorageInfo(subfolder?: string): Promise<any> {
    const params = subfolder ? `?subfolder=${encodeURIComponent(subfolder)}` : '';
    const response = await apiClient.get(`/import_sessions/storage-info${params}`);
    return response.data;
  }

  // Copy files from temp directory to storage location
  static async copyToStorage(
    importId: number, 
    storagePath: string,
    onProgress?: (progress: number) => void
  ): Promise<{ storage_path: string; files_copied: number }> {
    const response = await apiClient.post(`/import_sessions/${importId}/copy-to-storage`, {
      storage_path: storagePath
    });
    
    // For now, simulate progress since we don't have real-time progress from backend
    if (onProgress) {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        onProgress(progress);
        if (progress >= 100) {
          clearInterval(interval);
        }
      }, 100);
    }
    
    return response.data;
  }

  // Helper: Poll import progress until completion
  static async pollImportProgress(
    importId: number, 
    onProgress: (progress: ImportSession) => void,
    intervalMs = 1000
  ): Promise<ImportSession> {
    return new Promise((resolve, reject) => {
      const pollInterval = setInterval(async () => {
        try {
          const progress = await this.getImportProgress(importId);
          onProgress(progress);

          // Check if import is finished
          if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled') {
            clearInterval(pollInterval);
            resolve(progress);
          }
        } catch (error) {
          clearInterval(pollInterval);
          reject(error);
        }
      }, intervalMs);
    });
  }
}

export default ImportSessionsApi;