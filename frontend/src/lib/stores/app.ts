// Svelte stores for state management
import { writable, derived, type Writable } from 'svelte/store';
import type { Photo, ImportSession, Image } from '../types/api';

// Photos store
export const photos: Writable<Photo[]> = writable([]);
export const selectedPhoto: Writable<Photo | null> = writable(null);
export const photosLoading: Writable<boolean> = writable(false);
export const photosError: Writable<string | null> = writable(null);

// Import sessions store
export const importSessions: Writable<ImportSession[]> = writable([]);
export const activeImport: Writable<ImportSession | null> = writable(null);
export const importLoading: Writable<boolean> = writable(false);
export const importError: Writable<string | null> = writable(null);
export const importSessionsLoading: Writable<boolean> = writable(false);
export const importSessionsError: Writable<string | null> = writable(null);

// UI state
export const currentView: Writable<'photos' | 'imports' | 'authors'> = writable('photos');
export const sidebarOpen: Writable<boolean> = writable(false);

// Derived stores
export const photosCount = derived(photos, ($photos) => $photos.length);
export const hasActiveImport = derived(activeImport, ($activeImport) => 
  $activeImport?.status === 'in_progress' && !$activeImport?.is_cancelled
);

// Helper functions for stores
export const photosStore = {
  // Set photos
  set: (newPhotos: Photo[]) => photos.set(newPhotos),
  
  // Add photo
  add: (photo: Photo) => photos.update(current => [...current, photo]),
  
  // Update photo
  update: (hothash: string, updates: Partial<Photo>) => 
    photos.update(current => 
      current.map(p => p.hothash === hothash ? { ...p, ...updates } : p)
    ),
  
  // Remove photo
  remove: (hothash: string) => 
    photos.update(current => current.filter(p => p.hothash !== hothash)),
  
  // Set loading state
  setLoading: (loading: boolean) => photosLoading.set(loading),
  
  // Set error
  setError: (error: string | null) => photosError.set(error),
  
  // Clear error
  clearError: () => photosError.set(null)
};

export const importStore = {
  // Set active import
  setActive: (importSession: ImportSession | null) => activeImport.set(importSession),
  
  // Update active import progress
  updateProgress: (progress: Partial<ImportSession>) => 
    activeImport.update(current => current ? { ...current, ...progress } : null),
  
  // Add to import history
  addToHistory: (importSession: ImportSession) =>
    importSessions.update(current => [importSession, ...current]),
  
  // Set loading state
  setLoading: (loading: boolean) => importLoading.set(loading),
  
  // Set error
  setError: (error: string | null) => importError.set(error),
  
  // Clear active import
  clearActive: () => activeImport.set(null)
};

export const importSessionsStore = {
  // Set import sessions
  set: (newSessions: ImportSession[]) => importSessions.set(newSessions),
  
  // Add import session
  add: (session: ImportSession) => importSessions.update(current => [session, ...current]),
  
  // Update import session
  updateSession: (id: number, updates: Partial<ImportSession>) => 
    importSessions.update(current => 
      current.map(s => s.id === id ? { ...s, ...updates } : s)
    ),
  
  // Remove import session
  remove: (id: number) => 
    importSessions.update(current => current.filter(s => s.id !== id)),
  
  // Set loading state
  setLoading: (loading: boolean) => importSessionsLoading.set(loading),
  
  // Set error
  setError: (error: string | null) => importSessionsError.set(error),
  
  // Clear error
  clearError: () => importSessionsError.set(null)
};