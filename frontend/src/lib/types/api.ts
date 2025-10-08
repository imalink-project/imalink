// TypeScript types for API responses
export interface Photo {
  hothash: string;
  title?: string;
  description?: string;
  tags?: string[];
  rating?: number;
  user_rotation: number;
  author_id?: number;
  import_session_id?: number;
  created_at: string;
  updated_at: string;
  files: Image[];
}

export interface Image {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  format: string;
  taken_at?: string;
  camera_make?: string;
  camera_model?: string;
  width?: number;
  height?: number;
  gps_latitude?: number;
  gps_longitude?: number;
  hothash: string;
  import_session_id?: number;
  created_at: string;
  updated_at: string;
}

export interface ImportSession {
  id: number;
  started_at?: string;
  completed_at?: string;
  status: 'in_progress' | 'completed' | 'failed' | 'cancelled';
  source_path: string;
  source_description?: string;
  total_files_found: number;
  images_imported: number;
  duplicates_skipped: number;
  errors_count: number;
  progress_percentage: number;
  files_processed: number;
  current_file?: string;
  is_cancelled: boolean;
}

export interface Author {
  id: number;
  name: string;
  email?: string;
  bio?: string;
  created_at: string;
  updated_at: string;
}

// Request types
export interface ImportStartRequest {
  source_path: string;
  source_description?: string;
}

export interface PhotoSearchRequest {
  q?: string;
  author_id?: number;
  tags?: string[];
  rating_min?: number;
  rating_max?: number;
  offset?: number;
  limit?: number;
}

// Response wrappers
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// Batch photo creation types (NEW - for File System Access API)
export interface ImageCreateRequest {
  filename: string;
  hothash: string;
  file_size?: number;
  exif_data?: ArrayBuffer;
  import_session_id?: number;
}

export interface PhotoGroupRequest {
  hothash: string;
  hotpreview?: string;
  width?: number;
  height?: number;
  taken_at?: string;
  gps_latitude?: number;
  gps_longitude?: number;
  title?: string;
  description?: string;
  tags?: string[];
  rating?: number;
  user_rotation?: number;
  import_session_id?: number;
  images: ImageCreateRequest[];
}

export interface PhotoGroupBatchRequest {
  photo_groups: PhotoGroupRequest[];
  author_id?: number;
}

export interface PhotoGroupResult {
  success: boolean;
  hothash: string;
  photo?: Photo;
  images_created: number;
  error?: string;
  images_failed: number;
}

export interface BatchPhotoResponse {
  success: boolean;
  total_requested: number;
  photos_created: number;
  photos_failed: number;
  images_created: number;
  images_failed: number;
  processing_time_seconds: number;
  results: PhotoGroupResult[];
  error?: string;
}