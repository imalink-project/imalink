// Photos API client
import { apiClient } from './client';
import type { Photo, PaginatedResponse, PhotoSearchRequest, PhotoGroupBatchRequest, BatchPhotoResponse } from '../types/api';

export class PhotosApi {
  // Get paginated list of photos
  static async getPhotos(offset = 0, limit = 100, author_id?: number): Promise<PaginatedResponse<Photo>> {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString(),
    });
    
    if (author_id) {
      params.append('author_id', author_id.toString());
    }

    const response = await apiClient.get(`/photos?${params}`);
    return response.data;
  }

  // Get single photo by hash
  static async getPhoto(hothash: string): Promise<Photo> {
    const response = await apiClient.get(`/photos/${hothash}`);
    return response.data;
  }

  // Search photos with advanced criteria
  static async searchPhotos(searchRequest: PhotoSearchRequest): Promise<PaginatedResponse<Photo>> {
    const response = await apiClient.post('/photos/search', searchRequest);
    return response.data;
  }

  // Get photo statistics
  static async getStatistics(): Promise<any> {
    const response = await apiClient.get('/photos/statistics/overview');
    return response.data;
  }

  // Get hotpreview image URL
  static getHotpreviewUrl(hothash: string): string {
    return `${apiClient.defaults.baseURL}/photos/${hothash}/hotpreview`;
  }

  // Rotate photo
  static async rotatePhoto(hothash: string, clockwise = true): Promise<Photo> {
    const response = await apiClient.post(`/photos/${hothash}/rotate`, { clockwise });
    return response.data;
  }

  // Update photo metadata
  static async updatePhoto(hothash: string, updates: Partial<Photo>): Promise<Photo> {
    const response = await apiClient.put(`/photos/${hothash}`, updates);
    return response.data;
  }

  // Delete photo
  static async deletePhoto(hothash: string): Promise<void> {
    await apiClient.delete(`/photos/${hothash}`);
  }

  // Create multiple photos in batch (NEW - for File System Access API)
  static async createBatch(batchRequest: PhotoGroupBatchRequest): Promise<BatchPhotoResponse> {
    const response = await apiClient.post('/photos/batch', batchRequest);
    return response.data;
  }
}

export default PhotosApi;