# PhotoStack Frontend Implementation Guide

This guide provides comprehensive instructions for implementing PhotoStack functionality in frontend applications.

## 🎯 Overview

PhotoStack allows users to organize photos into collections (stacks) for better UI organization. Key characteristics:

- **One-to-Many Relationship**: Each photo can belong to at most one stack
- **Automatic Moving**: Adding a photo to a stack removes it from any previous stack
- **User Isolation**: Users can only manage their own stacks
- **Optional Metadata**: Stacks can have types and cover photos

## 🏗️ Architecture

### Data Models

```typescript
interface PhotoStackSummary {
  id: number;
  stack_type?: string;
  cover_photo_hothash?: string;
  photo_count: number;
  created_at: string;
  updated_at: string;
}

interface PhotoStackDetail {
  id: number;
  stack_type?: string;
  cover_photo_hothash?: string;
  photo_hothashes: string[];
  created_at: string;
  updated_at: string;
}

interface PhotoStackCreateRequest {
  stack_type?: string;
  cover_photo_hothash?: string;
}

interface PhotoStackUpdateRequest {
  stack_type?: string;
  cover_photo_hothash?: string;
}
```

### API Service Layer

```typescript
class PhotoStackService {
  private baseUrl = '/api/v1/photo-stacks';
  
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };
    
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return response.json();
  }
  
  // List stacks with pagination
  async getStacks(offset = 0, limit = 50) {
    return this.request<{ data: PhotoStackSummary[], meta: any }>(`/?offset=${offset}&limit=${limit}`);
  }
  
  // Get stack details with photo list
  async getStack(stackId: number) {
    return this.request<PhotoStackDetail>(`/${stackId}`);
  }
  
  // Create new stack
  async createStack(data: PhotoStackCreateRequest) {
    return this.request<{ success: boolean, stack: PhotoStackDetail }>('/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  // Update stack metadata
  async updateStack(stackId: number, data: PhotoStackUpdateRequest) {
    return this.request<{ success: boolean, stack: PhotoStackDetail }>(`/${stackId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
  
  // Delete stack
  async deleteStack(stackId: number) {
    return this.request<{ success: boolean }>(`/${stackId}`, {
      method: 'DELETE',
    });
  }
  
  // Add photo to stack (moves from any previous stack)
  async addPhoto(stackId: number, photoHash: string) {
    return this.request<{ success: boolean, stack: PhotoStackDetail }>(`/${stackId}/photo`, {
      method: 'POST',
      body: JSON.stringify({ photo_hothash: photoHash }),
    });
  }
  
  // Remove photo from stack
  async removePhoto(stackId: number, photoHash: string) {
    return this.request<{ success: boolean, stack: PhotoStackDetail | null }>(`/${stackId}/photo/${photoHash}`, {
      method: 'DELETE',
    });
  }
  
  // Get photo's stack (returns single stack or null)
  async getPhotoStack(photoHash: string) {
    return this.request<PhotoStackSummary | null>(`/photos/${photoHash}/stack`);
  }
}

export const photoStackService = new PhotoStackService();
```

## ⚛️ React Integration

### Custom Hooks

```typescript
import { useState, useEffect, useCallback } from 'react';
import { photoStackService } from './photoStackService';

// Hook for managing stack list
export const usePhotoStacks = () => {
  const [stacks, setStacks] = useState<PhotoStackSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStacks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await photoStackService.getStacks();
      setStacks(response.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stacks');
    } finally {
      setLoading(false);
    }
  }, []);

  const createStack = async (data: PhotoStackCreateRequest) => {
    const result = await photoStackService.createStack(data);
    await fetchStacks(); // Refresh list
    return result;
  };

  const deleteStack = async (stackId: number) => {
    await photoStackService.deleteStack(stackId);
    await fetchStacks(); // Refresh list
  };

  useEffect(() => {
    fetchStacks();
  }, [fetchStacks]);

  return {
    stacks,
    loading,
    error,
    refresh: fetchStacks,
    createStack,
    deleteStack,
  };
};

// Hook for managing individual stack
export const usePhotoStack = (stackId: number | null) => {
  const [stack, setStack] = useState<PhotoStackDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStack = useCallback(async () => {
    if (!stackId) return;
    
    setLoading(true);
    setError(null);
    try {
      const stackData = await photoStackService.getStack(stackId);
      setStack(stackData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stack');
    } finally {
      setLoading(false);
    }
  }, [stackId]);

  const addPhoto = async (photoHash: string) => {
    if (!stackId) return;
    
    const result = await photoStackService.addPhoto(stackId, photoHash);
    await fetchStack(); // Refresh stack data
    return result;
  };

  const removePhoto = async (photoHash: string) => {
    if (!stackId) return;
    
    const result = await photoStackService.removePhoto(stackId, photoHash);
    await fetchStack(); // Refresh stack data
    return result;
  };

  useEffect(() => {
    fetchStack();
  }, [fetchStack]);

  return {
    stack,
    loading,
    error,
    refresh: fetchStack,
    addPhoto,
    removePhoto,
  };
};

// Hook for photo's current stack
export const usePhotoStack = (photoHash: string) => {
  const [currentStackId, setCurrentStackId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchCurrentStack = useCallback(async () => {
    setLoading(true);
    try {
      const response = await photoStackService.findStacksForPhoto(photoHash);
      const stacks = response.data || [];
      setCurrentStackId(stacks.length > 0 ? stacks[0].id : null);
    } catch (err) {
      console.error('Failed to fetch photo stack:', err);
      setCurrentStackId(null);
    } finally {
      setLoading(false);
    }
  }, [photoHash]);

  const moveToStack = async (newStackId: number | null) => {
    // Remove from current stack if exists
    if (currentStackId) {
      await photoStackService.removePhoto(currentStackId, photoHash);
    }
    
    // Add to new stack if specified
    if (newStackId) {
      await photoStackService.addPhoto(newStackId, photoHash);
    }
    
    setCurrentStackId(newStackId);
  };

  useEffect(() => {
    fetchCurrentStack();
  }, [fetchCurrentStack]);

  return {
    currentStackId,
    loading,
    moveToStack,
    refresh: fetchCurrentStack,
  };
};
```

### UI Components

```typescript
// Stack grid component
export const StackGrid: React.FC<{
  onStackSelect?: (stack: PhotoStackSummary) => void;
}> = ({ onStackSelect }) => {
  const { stacks, loading, createStack } = usePhotoStacks();
  const [showCreateForm, setShowCreateForm] = useState(false);

  if (loading) {
    return <div className="loading">Loading stacks...</div>;
  }

  return (
    <div className="stack-grid">
      <div className="stack-actions">
        <button onClick={() => setShowCreateForm(true)}>
          Create New Stack
        </button>
      </div>
      
      <div className="stacks">
        {stacks.map(stack => (
          <StackCard
            key={stack.id}
            stack={stack}
            onClick={() => onStackSelect?.(stack)}
          />
        ))}
      </div>
      
      {showCreateForm && (
        <StackCreateForm
          onClose={() => setShowCreateForm(false)}
          onSubmit={async (data) => {
            await createStack(data);
            setShowCreateForm(false);
          }}
        />
      )}
    </div>
  );
};

// Individual stack card
export const StackCard: React.FC<{
  stack: PhotoStackSummary;
  onClick?: () => void;
}> = ({ stack, onClick }) => {
  return (
    <div className="stack-card" onClick={onClick}>
      <div className="stack-cover">
        {stack.cover_photo_hothash ? (
          <img
            src={`/api/v1/photos/${stack.cover_photo_hothash}/hotpreview`}
            alt={`Stack ${stack.id}`}
            loading="lazy"
          />
        ) : (
          <div className="placeholder">No Cover</div>
        )}
      </div>
      <div className="stack-info">
        <h3>Stack {stack.id} {stack.stack_type && `(${stack.stack_type})`}</h3>
        <p>{stack.photo_count} photos</p>
        {stack.stack_type && (
          <span className="stack-type">{stack.stack_type}</span>
        )}
      </div>
    </div>
  );
};

// Stack selector for photos
export const PhotoStackSelector: React.FC<{
  photoHash: string;
  onChange?: (stackId: number | null) => void;
}> = ({ photoHash, onChange }) => {
  const { stacks } = usePhotoStacks();
  const { currentStackId, moveToStack } = usePhotoStack(photoHash);

  const handleChange = async (newStackId: number | null) => {
    try {
      await moveToStack(newStackId);
      onChange?.(newStackId);
    } catch (error) {
      console.error('Failed to move photo:', error);
    }
  };

  return (
    <select
      value={currentStackId || ''}
      onChange={(e) => handleChange(e.target.value ? Number(e.target.value) : null)}
    >
      <option value="">No Stack</option>
      {stacks.map(stack => (
        <option key={stack.id} value={stack.id}>
          Stack {stack.id} {stack.stack_type && `(${stack.stack_type})`} ({stack.photo_count})
        </option>
      ))}
    </select>
  );
};

// Create stack form
export const StackCreateForm: React.FC<{
  onSubmit: (data: PhotoStackCreateRequest) => void;
  onClose: () => void;
}> = ({ onSubmit, onClose }) => {
  const [formData, setFormData] = useState<PhotoStackCreateRequest>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="stack-create-form">
      <div className="form-group">
        <label>Type:</label>
        <select
          value={formData.stack_type || ''}
          onChange={(e) => setFormData({ ...formData, stack_type: e.target.value })}
        >
          <option value="">Select type...</option>
          <option value="album">Album</option>
          <option value="panorama">Panorama</option>
          <option value="burst">Burst</option>
          <option value="animation">Animation</option>
          <option value="hdr">HDR</option>
        </select>
      </div>
      
      <div className="form-actions">
        <button type="submit">Create Stack</button>
        <button type="button" onClick={onClose}>Cancel</button>
      </div>
    </form>
  );
};
```

## 🎨 CSS Styling

```css
/* Stack Grid */
.stack-grid {
  padding: 20px;
}

.stack-actions {
  margin-bottom: 20px;
}

.stacks {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

/* Stack Card */
.stack-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}

.stack-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.stack-cover {
  width: 100%;
  height: 150px;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stack-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stack-cover .placeholder {
  color: #999;
  font-size: 14px;
}

.stack-info {
  padding: 12px;
}

.stack-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
}

.stack-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.stack-type {
  display: inline-block;
  background: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  margin-top: 8px;
}

/* Form Styles */
.stack-create-form {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  max-width: 400px;
  margin: 20px auto;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.form-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.form-actions button[type="submit"] {
  background: #1976d2;
  color: white;
}

.form-actions button[type="button"] {
  background: #f5f5f5;
  color: #333;
}
```

## 🔄 State Management

### With React Context

```typescript
// Context for global stack state
const PhotoStackContext = createContext<{
  stacks: PhotoStackSummary[];
  refreshStacks: () => void;
  addStack: (stack: PhotoStackSummary) => void;
  updateStack: (id: number, updates: Partial<PhotoStackSummary>) => void;
  removeStack: (id: number) => void;
} | null>(null);

export const PhotoStackProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { stacks, refresh: refreshStacks, createStack } = usePhotoStacks();
  
  const addStack = useCallback((stack: PhotoStackSummary) => {
    refreshStacks(); // Simple refresh for now
  }, [refreshStacks]);
  
  // ... other methods
  
  return (
    <PhotoStackContext.Provider value={{
      stacks,
      refreshStacks,
      addStack,
      updateStack,
      removeStack,
    }}>
      {children}
    </PhotoStackContext.Provider>
  );
};
```

### With Redux Toolkit

```typescript
// Stack slice
const stackSlice = createSlice({
  name: 'photoStacks',
  initialState: {
    stacks: [] as PhotoStackSummary[],
    loading: false,
    error: null as string | null,
  },
  reducers: {
    setStacks: (state, action) => {
      state.stacks = action.payload;
    },
    addStack: (state, action) => {
      state.stacks.push(action.payload);
    },
    updateStack: (state, action) => {
      const { id, updates } = action.payload;
      const index = state.stacks.findIndex(s => s.id === id);
      if (index !== -1) {
        state.stacks[index] = { ...state.stacks[index], ...updates };
      }
    },
    removeStack: (state, action) => {
      state.stacks = state.stacks.filter(s => s.id !== action.payload);
    },
  },
});

// Async actions
export const fetchStacks = createAsyncThunk('stacks/fetch', async () => {
  const response = await photoStackService.getStacks();
  return response.data;
});

export const createNewStack = createAsyncThunk(
  'stacks/create',
  async (data: PhotoStackCreateRequest) => {
    const response = await photoStackService.createStack(data);
    return response.stack;
  }
);
```

## 🧪 Testing

### Unit Tests

```typescript
// Service tests
describe('PhotoStackService', () => {
  beforeEach(() => {
    fetchMock.resetMocks();
    localStorage.setItem('access_token', 'mock-token');
  });

  it('should fetch stacks with pagination', async () => {
    const mockStacks = [{ id: 1, stack_type: 'panorama', photo_count: 5 }];
    fetchMock.mockResponseOnce(JSON.stringify({ data: mockStacks }));

    const result = await photoStackService.getStacks(0, 10);
    
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/photo-stacks/?offset=0&limit=10', {
      headers: expect.objectContaining({
        'Authorization': 'Bearer mock-token',
      }),
    });
    expect(result.data).toEqual(mockStacks);
  });

  it('should create new stack', async () => {
    const mockStack = { id: 1, stack_type: 'panorama' };
    fetchMock.mockResponseOnce(JSON.stringify({ success: true, stack: mockStack }));

    const result = await photoStackService.createStack({ stack_type: 'panorama' });
    
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/photo-stacks/', {
      method: 'POST',
      headers: expect.any(Object),
      body: JSON.stringify({ stack_type: 'panorama' }),
    });
    expect(result.stack).toEqual(mockStack);
  });
});

// Component tests
describe('StackGrid', () => {
  it('should render stacks', () => {
    const mockStacks = [
      { id: 1, stack_type: 'panorama', photo_count: 5, created_at: '', updated_at: '' },
    ];
    
    render(
      <PhotoStackProvider>
        <StackGrid />
      </PhotoStackProvider>
    );
    
    expect(screen.getByText('Stack 1 (panorama)')).toBeInTheDocument();
    expect(screen.getByText('5 photos')).toBeInTheDocument();
  });
});
```

### Integration Tests

```typescript
// End-to-end workflow tests
describe('PhotoStack Workflow', () => {
  it('should create stack and add photos', async () => {
    // Create stack
    const createResponse = await photoStackService.createStack({
      stack_type: 'album',
    });
    
    expect(createResponse.success).toBe(true);
    const stackId = createResponse.stack.id;
    
    // Add photo
    const addResponse = await photoStackService.addPhoto(stackId, 'test-hash-123');
    expect(addResponse.success).toBe(true);
    
    // Verify photo is in stack
    const stackDetail = await photoStackService.getStack(stackId);
    expect(stackDetail.photo_hothashes).toContain('test-hash-123');
  });
});
```

## 📝 Best Practices

1. **Error Handling**: Always handle API errors gracefully
2. **Loading States**: Show loading indicators for async operations
3. **Optimistic Updates**: Update UI immediately, revert on error
4. **Caching**: Cache stack data to reduce API calls
5. **User Feedback**: Provide clear feedback for all actions
6. **Accessibility**: Ensure all components are accessible
7. **Performance**: Use React.memo for expensive components
8. **Type Safety**: Leverage TypeScript for better development experience

This guide provides a complete foundation for implementing PhotoStack functionality in modern frontend applications!