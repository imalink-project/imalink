# Frontend Integration Guide

This guide provides a complete frontend integration strategy for the new ImaLink authentication and upload architecture!

## 🔐 Authentication Flow

### 1. User Registration/Login

```typescript
// Register new user
const registerUser = async (userData: {
  username: string;
  email: string;
  password: string;
  display_name: string;
}) => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  
  if (!response.ok) {
    throw new Error('Registration failed');
  }
  
  return await response.json();
};

// Login user
const loginUser = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  const data = await response.json();
  
  // Store token
  localStorage.setItem('access_token', data.access_token);
  
  return data;
};
```

### 2. Token Management

```typescript
// Get auth headers with token
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

// Check if user is authenticated
const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

// Logout
const logout = () => {
  localStorage.removeItem('access_token');
  window.location.href = '/login';
};
```

## 📤 Upload Architecture

### New Upload Endpoints

The system now has two distinct upload endpoints:

1. **`/api/v1/image-files/new-photo`** - Creates both ImageFile and Photo
2. **`/api/v1/image-files/add-to-photo`** - Adds ImageFile to existing Photo

### 1. Upload New Photo (Creates Photo + ImageFile)

```typescript
const uploadNewPhoto = async (file: File, metadata?: {
  author_id?: number;
  rating?: number;
}) => {
  // 1. Validate file
  if (!file.type.startsWith('image/')) {
    throw new Error('Only image files are allowed');
  }
  
  // 2. Generate hotpreview
  const hotpreview = await generateHotpreview(file);
  
  // 3. Upload
  const response = await fetch('/api/v1/image-files/new-photo', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      filename: file.name,
      file_size: file.size,
      mime_type: file.type,
      hotpreview_base64: hotpreview,
      author_id: metadata?.author_id,
      rating: metadata?.rating,
    }),
  });
  
  if (!response.ok) {
    throw new Error('Upload failed');
  }
  
  return await response.json();
};
```

### 2. Add to Existing Photo

```typescript
const addToExistingPhoto = async (file: File, photoHothash: string) => {
  // 1. Validate file
  if (!file.type.startsWith('image/')) {
    throw new Error('Only image files are allowed');
  }
  
  // 2. Generate hotpreview
  const hotpreview = await generateHotpreview(file);
  
  // 3. Upload
  const response = await fetch('/api/v1/image-files/add-to-photo', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      photo_hothash: photoHothash,
      filename: file.name,
      file_size: file.size,
      mime_type: file.type,
      hotpreview_base64: hotpreview,
    }),
  });
  
  if (!response.ok) {
    throw new Error('Upload failed');
  }
  
  return await response.json();
};
```

## 🖼️ Hotpreview Generation

```typescript
const generateHotpreview = async (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      // Set canvas to 150x150
      canvas.width = 150;
      canvas.height = 150;
      
      // Calculate aspect ratio
      const aspectRatio = img.width / img.height;
      let drawWidth = 150;
      let drawHeight = 150;
      let offsetX = 0;
      let offsetY = 0;
      
      if (aspectRatio > 1) {
        // Landscape
        drawHeight = 150 / aspectRatio;
        offsetY = (150 - drawHeight) / 2;
      } else {
        // Portrait
        drawWidth = 150 * aspectRatio;
        offsetX = (150 - drawWidth) / 2;
      }
      
      // Fill background
      ctx!.fillStyle = '#f0f0f0';
      ctx!.fillRect(0, 0, 150, 150);
      
      // Draw image
      ctx!.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
      
      // Convert to base64 (without data URL prefix)
      const base64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
      resolve(base64);
    };
    
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = URL.createObjectURL(file);
  });
};
```

## 📊 User Statistics & Data Model Updates

### User Response Model
The user object now includes comprehensive statistics:
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  
  // Statistics
  photos_count: number;
  import_sessions_count: number;
  authors_count: number;
  image_files_count: number;    // NEW!
}
```

### ImageFile Model Updates
ImageFile now has user ownership:
```typescript
interface ImageFile {
  id: number;
  user_id: number;              // NEW: User ownership
  photo_hothash: string;
  filename: string;
  file_size: number;
  mime_type: string;
  hotpreview_base64: string;
  upload_timestamp: string;
}
```

### Dashboard Implementation
```typescript
// Get user statistics for dashboard
const fetchUserStats = async () => {
  const response = await fetch('/api/v1/users/me', {
    headers: getAuthHeaders()
  });
  
  const user = await response.json();
  
  return {
    photos: user.photos_count,
    sessions: user.import_sessions_count,
    authors: user.authors_count,
    files: user.image_files_count
  };
};
```

## 🎯 Symmetric Architecture Benefits

All major data models now follow the same user ownership pattern:
- `Photo.user_id` → User's photos
- `Author.user_id` → User's photographers  
- `ImportSession.user_id` → User's import sessions
- `ImageFile.user_id` → User's image files

This provides:
- **Consistent API patterns** across all endpoints
- **Complete data isolation** between users
- **Simplified frontend logic** with predictable user scoping

## 🚦 Error Handling Strategy

```typescript
class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

const handleAPIResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    
    switch (response.status) {
      case 401:
        logout(); // Token expired or invalid
        throw new APIError('Authentication required', 401, errorData);
      case 403:
        throw new APIError('Access denied', 403, errorData);
      case 422:
        throw new APIError('Validation error', 422, errorData);
      default:
        throw new APIError(
          errorData.detail || 'An error occurred',
          response.status,
          errorData
        );
    }
  }
  
  return await response.json();
};
```

## 📱 Reactive UI Patterns

### Auth State Management

```typescript
// Using a simple reactive store pattern
class AuthStore {
  private listeners: Set<() => void> = new Set();
  private _user: User | null = null;
  
  get user() {
    return this._user;
  }
  
  get isAuthenticated() {
    return !!this._user;
  }
  
  setUser(user: User | null) {
    this._user = user;
    this.notify();
  }
  
  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  private notify() {
    this.listeners.forEach(listener => listener());
  }
  
  async loadUser() {
    if (!isAuthenticated()) return;
    
    try {
      const response = await fetch('/api/v1/users/me', {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const user = await response.json();
        this.setUser(user);
      } else {
        this.setUser(null);
      }
    } catch (error) {
      this.setUser(null);
    }
  }
}

export const authStore = new AuthStore();
```

### Upload Progress Tracking

```typescript
interface UploadProgress {
  filename: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
}

class UploadManager {
  private uploads: Map<string, UploadProgress> = new Map();
  private listeners: Set<() => void> = new Set();
  
  async uploadFile(file: File, metadata?: any) {
    const uploadId = `${Date.now()}-${file.name}`;
    
    // Initialize progress
    this.uploads.set(uploadId, {
      filename: file.name,
      progress: 0,
      status: 'pending'
    });
    this.notify();
    
    try {
      // Update to uploading
      this.updateUpload(uploadId, { status: 'uploading', progress: 10 });
      
      // Generate hotpreview
      this.updateUpload(uploadId, { progress: 30 });
      const hotpreview = await generateHotpreview(file);
      
      // Upload
      this.updateUpload(uploadId, { status: 'processing', progress: 50 });
      const result = await uploadNewPhoto(file, metadata);
      
      // Complete
      this.updateUpload(uploadId, { status: 'complete', progress: 100 });
      
      return result;
    } catch (error) {
      this.updateUpload(uploadId, {
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed'
      });
      throw error;
    }
  }
  
  private updateUpload(id: string, updates: Partial<UploadProgress>) {
    const current = this.uploads.get(id);
    if (current) {
      this.uploads.set(id, { ...current, ...updates });
      this.notify();
    }
  }
  
  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  private notify() {
    this.listeners.forEach(listener => listener());
  }
  
  getUploads() {
    return Array.from(this.uploads.values());
  }
}

export const uploadManager = new UploadManager();
```

## 🔍 Data Fetching Patterns

### Photos API

```typescript
// Get user's photos with pagination
const fetchPhotos = async (page = 1, limit = 20) => {
  const response = await fetch(
    `/api/v1/photos/?skip=${(page - 1) * limit}&limit=${limit}`,
    { headers: getAuthHeaders() }
  );
  
  return handleAPIResponse(response);
};

// Get single photo with image files
const fetchPhoto = async (hothash: string) => {
  const response = await fetch(
    `/api/v1/photos/${hothash}`,
    { headers: getAuthHeaders() }
  );
  
  return handleAPIResponse(response);
};

// Get image files for a photo
const fetchPhotoImages = async (hothash: string) => {
  const response = await fetch(
    `/api/v1/photos/${hothash}/image-files`,
    { headers: getAuthHeaders() }
  );
  
  return handleAPIResponse(response);
};
```

### Authors API

```typescript
// Get user's authors
const fetchAuthors = async () => {
  const response = await fetch('/api/v1/authors/', {
    headers: getAuthHeaders()
  });
  
  return handleAPIResponse(response);
};

// Create new author
const createAuthor = async (authorData: {
  name: string;
  email?: string;
  bio?: string;
}) => {
  const response = await fetch('/api/v1/authors/', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(authorData),
  });
  
  return handleAPIResponse(response);
};
```

## � Photo Stack Management

Photo stacks organize photos into collections. Each photo can belong to at most one stack, supporting various UI organization needs.

### Core Stack Operations

```typescript
// PhotoStack TypeScript interfaces
interface PhotoStackSummary {
  id: number;
  stack_type?: string;
  cover_photo_hothash?: string;
  photo_count: number;
  created_at: string;
  updated_at: string;
}

interface PhotoStackDetail extends PhotoStackSummary {
  photo_hothashes: string[];
}

interface PhotoStackCreateRequest {
  stack_type?: string;
  cover_photo_hothash?: string;
}

// Stack management functions
const createStack = async (stackData: PhotoStackCreateRequest) => {
  const response = await fetch('/api/v1/photo-stacks/', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(stackData),
  });
  
  return handleAPIResponse(response);
};

const getStacks = async (offset = 0, limit = 50) => {
  const response = await fetch(
    `/api/v1/photo-stacks/?offset=${offset}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    }
  );
  
  return handleAPIResponse(response);
};

const getStackDetail = async (stackId: number) => {
  const response = await fetch(`/api/v1/photo-stacks/${stackId}`, {
    headers: getAuthHeaders(),
  });
  
  return handleAPIResponse(response);
};

const addPhotoToStack = async (stackId: number, photoHash: string) => {
  const response = await fetch(`/api/v1/photo-stacks/${stackId}/photo`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ photo_hothash: photoHash }),
  });
  
  return handleAPIResponse(response);
};

const removePhotoFromStack = async (stackId: number, photoHash: string) => {
  const response = await fetch(
    `/api/v1/photo-stacks/${stackId}/photo/${photoHash}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders(),
    }
  );
  
  return handleAPIResponse(response);
};

const findStacksForPhoto = async (photoHash: string) => {
  const response = await fetch(
    `/api/v1/photo-stacks/photo/${photoHash}/stacks`,
    {
      headers: getAuthHeaders(),
    }
  );
  
  return handleAPIResponse(response);
};
```

### React Hook for Stack Management

```typescript
import { useState, useEffect } from 'react';

export const usePhotoStacks = () => {
  const [stacks, setStacks] = useState<PhotoStackSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStacks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getStacks();
      setStacks(response.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stacks');
    } finally {
      setLoading(false);
    }
  };

  const createNewStack = async (stackData: PhotoStackCreateRequest) => {
    try {
      const newStack = await createStack(stackData);
      await fetchStacks(); // Refresh list
      return newStack;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create stack');
      throw err;
    }
  };

  const addPhotoToExistingStack = async (stackId: number, photoHash: string) => {
    try {
      await addPhotoToStack(stackId, photoHash);
      await fetchStacks(); // Refresh to update counts
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add photo');
      throw err;
    }
  };

  useEffect(() => {
    fetchStacks();
  }, []);

  return {
    stacks,
    loading,
    error,
    refresh: fetchStacks,
    createStack: createNewStack,
    addPhoto: addPhotoToExistingStack,
  };
};
```

### UI Integration Patterns

```typescript
// Stack selector component
const StackSelector: React.FC<{
  photoHash: string;
  onStackChange?: (stackId: number | null) => void;
}> = ({ photoHash, onStackChange }) => {
  const { stacks } = usePhotoStacks();
  const [currentStack, setCurrentStack] = useState<number | null>(null);

  // Find current stack for photo
  useEffect(() => {
    findStacksForPhoto(photoHash).then(response => {
      const photoStacks = response.data || [];
      setCurrentStack(photoStacks.length > 0 ? photoStacks[0].id : null);
    });
  }, [photoHash]);

  const handleStackChange = async (newStackId: number | null) => {
    try {
      if (currentStack) {
        await removePhotoFromStack(currentStack, photoHash);
      }
      if (newStackId) {
        await addPhotoToStack(newStackId, photoHash);
      }
      setCurrentStack(newStackId);
      onStackChange?.(newStackId);
    } catch (error) {
      console.error('Failed to change stack:', error);
    }
  };

  return (
    <select 
      value={currentStack || ''} 
      onChange={(e) => handleStackChange(e.target.value ? Number(e.target.value) : null)}
    >
      <option value="">No Stack</option>
      {stacks.map(stack => (
        <option key={stack.id} value={stack.id}>
          {stack.stack_type || `Stack ${stack.id}`} ({stack.photo_count} photos)
        </option>
      ))}
    </select>
  );
};

// Stack grid component
const StackGrid: React.FC = () => {
  const { stacks, loading } = usePhotoStacks();

  if (loading) return <div>Loading stacks...</div>;

  return (
    <div className="stack-grid">
      {stacks.map(stack => (
        <div key={stack.id} className="stack-card">
          {stack.cover_photo_hothash && (
            <img 
              src={`/api/v1/photos/${stack.cover_photo_hothash}/hotpreview`}
              alt={stack.stack_type || `Stack ${stack.id}`}
            />
          )}
          <div className="stack-info">
            <h3>{stack.stack_type || `Stack ${stack.id}`}</h3>
            <p>{stack.photo_count} photos</p>
          </div>
        </div>
      ))}
    </div>
  );
};
```

### Key Considerations

- **One-to-Many Relationship**: Each photo can belong to at most one stack
- **Automatic Moving**: Adding a photo to a stack automatically removes it from any previous stack
- **Cover Photo**: Must be a photo that exists and belongs to the user
- **Stack Types**: Optional categorization (album, panorama, burst, animation, etc.)
- **User Isolation**: Users can only manage their own stacks and photos

## �💾 Local Storage & Caching

```typescript
// Simple cache with expiration
class Cache {
  private store = new Map<string, { data: any; expires: number }>();
  
  set(key: string, data: any, ttlSeconds = 300) {
    this.store.set(key, {
      data,
      expires: Date.now() + (ttlSeconds * 1000)
    });
  }
  
  get(key: string) {
    const item = this.store.get(key);
    if (!item) return null;
    
    if (Date.now() > item.expires) {
      this.store.delete(key);
      return null;
    }
    
    return item.data;
  }
  
  clear() {
    this.store.clear();
  }
}

export const cache = new Cache();

// Cached API calls
const fetchPhotosWithCache = async (page = 1, limit = 20) => {
  const cacheKey = `photos-${page}-${limit}`;
  const cached = cache.get(cacheKey);
  
  if (cached) {
    return cached;
  }
  
  const data = await fetchPhotos(page, limit);
  cache.set(cacheKey, data, 60); // Cache for 1 minute
  
  return data;
};
```

## 🎨 UI Component Patterns

### Authentication Form

```typescript
// React example (adaptable to other frameworks)
import { useState } from 'react';

const LoginForm = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await loginUser(credentials.username, credentials.password);
      await authStore.loadUser();
      // Redirect handled by auth store
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Username"
        value={credentials.username}
        onChange={e => setCredentials(prev => ({
          ...prev,
          username: e.target.value
        }))}
        required
      />
      
      <input
        type="password"
        placeholder="Password"
        value={credentials.password}
        onChange={e => setCredentials(prev => ({
          ...prev,
          password: e.target.value
        }))}
        required
      />
      
      {error && <div className="error">{error}</div>}
      
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};
```

### File Upload Component

```typescript
const FileUploader = () => {
  const [dragOver, setDragOver] = useState(false);
  
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    for (const file of imageFiles) {
      try {
        await uploadManager.uploadFile(file);
      } catch (error) {
        console.error('Upload failed:', error);
      }
    }
  };
  
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    for (const file of files) {
      try {
        await uploadManager.uploadFile(file);
      } catch (error) {
        console.error('Upload failed:', error);
      }
    }
  };
  
  return (
    <div
      className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
      onDragOver={e => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <input
        type="file"
        multiple
        accept="image/*"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        id="file-input"
      />
      
      <label htmlFor="file-input">
        <div>Drop images here or click to select</div>
      </label>
    </div>
  );
};
```

## 🔄 Real-time Updates

```typescript
// Simple polling for updates (can be replaced with WebSocket)
class UpdatePoller {
  private intervals: Set<NodeJS.Timeout> = new Set();
  
  startPolling(callback: () => void, intervalMs = 30000) {
    const interval = setInterval(callback, intervalMs);
    this.intervals.add(interval);
    
    return () => {
      clearInterval(interval);
      this.intervals.delete(interval);
    };
  }
  
  stopAll() {
    this.intervals.forEach(interval => clearInterval(interval));
    this.intervals.clear();
  }
}

export const updatePoller = new UpdatePoller();

// Usage example
const usePhotosWithUpdates = () => {
  const [photos, setPhotos] = useState([]);
  
  useEffect(() => {
    const loadPhotos = async () => {
      try {
        const data = await fetchPhotosWithCache();
        setPhotos(data.items);
      } catch (error) {
        console.error('Failed to load photos:', error);
      }
    };
    
    // Initial load
    loadPhotos();
    
    // Poll for updates
    const stopPolling = updatePoller.startPolling(loadPhotos, 30000);
    
    return stopPolling;
  }, []);
  
  return photos;
};
```

## 🏗️ Application Architecture

### Recommended Project Structure

```
src/
├── services/
│   ├── api.ts          # Core API functions
│   ├── auth.ts         # Authentication service
│   ├── upload.ts       # Upload management
│   └── cache.ts        # Caching utilities
├── stores/
│   ├── auth.ts         # Authentication state
│   ├── photos.ts       # Photos state
│   └── uploads.ts      # Upload state
├── components/
│   ├── Auth/
│   │   ├── LoginForm.tsx
│   │   └── RegisterForm.tsx
│   ├── Upload/
│   │   ├── FileUploader.tsx
│   │   └── UploadProgress.tsx
│   └── Photos/
│       ├── PhotoGrid.tsx
│       └── PhotoDetail.tsx
├── pages/
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   └── Photos.tsx
├── types/
│   └── api.ts          # TypeScript interfaces
└── utils/
    ├── hotpreview.ts   # Image processing
    └── errors.ts       # Error handling
```

## 🔧 Development Tools

### API Client Generator

Consider using tools like OpenAPI Generator with the provided `openapi.json`:

```bash
# Generate TypeScript client from OpenAPI spec
npx @openapitools/openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-fetch \
  -o src/generated/api
```

### Testing Helpers

```typescript
// Mock auth for testing
export const mockAuth = {
  login: jest.fn().mockResolvedValue({ access_token: 'mock-token' }),
  getAuthHeaders: jest.fn().mockReturnValue({
    'Authorization': 'Bearer mock-token',
    'Content-Type': 'application/json'
  })
};

// Test upload helper
export const createMockFile = (
  name = 'test.jpg',
  size = 1024,
  type = 'image/jpeg'
) => {
  const file = new File(['mock-content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};
```

This guide provides a comprehensive foundation for integrating with the ImaLink API. The authentication system ensures complete user data isolation, while the new upload architecture provides flexibility for different use cases.