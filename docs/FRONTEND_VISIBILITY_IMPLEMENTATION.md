# Frontend Implementation Guide - Phase 1 Visibility

**Status:** ✅ Backend deployed and ready  
**Date:** November 7, 2025  
**For:** imalink-web frontend developers

---

## Overview

Phase 1 adds **visibility control** to photos and PhotoText documents. Users can now choose whether content is:
- **Private** (default) - Only visible to the owner
- **Public** - Visible to everyone, including anonymous users

---

## API Changes

### 1. Photo Endpoints

#### Get Photo (supports anonymous access)
```http
GET /api/v1/photos/{hothash}
Authorization: Bearer {token}  # Optional - anonymous users can view public photos
```

**Response includes new field:**
```json
{
  "hothash": "abc123...",
  "visibility": "private",  // or "public"
  "rating": 3,
  // ... other fields
}
```

#### Update Photo Visibility
```http
PUT /api/v1/photos/{hothash}
Authorization: Bearer {token}  # Required
Content-Type: application/json

{
  "visibility": "public"  // or "private"
}
```

#### List Photos (supports anonymous access)
```http
GET /api/v1/photos
Authorization: Bearer {token}  # Optional
```

**Behavior:**
- **Anonymous users:** Only see public photos
- **Authenticated users:** See own photos + public photos from others

---

### 2. PhotoText Document Endpoints

#### Get Document (supports anonymous access)
```http
GET /api/v1/phototext/{document_id}
Authorization: Bearer {token}  # Optional
```

**Response includes:**
```json
{
  "id": 123,
  "title": "My Story",
  "visibility": "private",  // or "public"
  "is_published": true,
  "content": { ... },
  // ... other fields
}
```

#### Create Document with Visibility
```http
POST /api/v1/phototext
Authorization: Bearer {token}  # Required
Content-Type: application/json

{
  "title": "New Story",
  "document_type": "general",
  "content": { ... },
  "visibility": "private"  // Optional, defaults to "private"
}
```

#### Update Document Visibility
```http
PUT /api/v1/phototext/{document_id}
Authorization: Bearer {token}  # Required
Content-Type: application/json

{
  "visibility": "public"  // or "private"
}
```

#### List Documents (supports anonymous access)
```http
GET /api/v1/phototext
Authorization: Bearer {token}  # Optional
```

**Behavior:**
- **Anonymous users:** Only see public documents
- **Authenticated users:** See own documents + public documents from others

---

## UI Implementation Recommendations

### 1. Photo Detail View

Add a visibility toggle:

```vue
<template>
  <div class="photo-detail">
    <!-- Existing photo display -->
    
    <!-- NEW: Visibility control (only for owner) -->
    <div v-if="isOwner" class="visibility-control">
      <label>Visibility:</label>
      <select v-model="photo.visibility" @change="updateVisibility">
        <option value="private">🔒 Private (Only You)</option>
        <option value="public">🌍 Public (Everyone)</option>
      </select>
      
      <p v-if="photo.visibility === 'public'" class="warning">
        ⚠️ This photo is visible to everyone, including anonymous users
      </p>
    </div>
    
    <!-- NEW: Public indicator (for viewers) -->
    <div v-else-if="photo.visibility === 'public'" class="public-badge">
      🌍 Public Photo
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const photo = ref({ visibility: 'private' })

const isOwner = computed(() => {
  return photo.value.user_id === authStore.currentUser?.id
})

async function updateVisibility() {
  await fetch(`/api/v1/photos/${photo.value.hothash}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${authStore.token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      visibility: photo.value.visibility
    })
  })
}
</script>
```

### 2. Photo List/Gallery View

Add visual indicator for public photos:

```vue
<template>
  <div class="photo-grid">
    <div v-for="photo in photos" :key="photo.hothash" class="photo-card">
      <img :src="`/api/v1/photos/${photo.hothash}/hotpreview`" />
      
      <!-- NEW: Show visibility badge -->
      <span v-if="photo.visibility === 'public'" class="badge badge-public">
        🌍 Public
      </span>
      <span v-else class="badge badge-private">
        🔒 Private
      </span>
    </div>
  </div>
</template>

<style scoped>
.badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.badge-public {
  background: rgba(34, 197, 94, 0.9);
  color: white;
}

.badge-private {
  background: rgba(107, 114, 128, 0.9);
  color: white;
}
</style>
```

### 3. PhotoText Document Editor

Add visibility control to document settings:

```vue
<template>
  <div class="document-editor">
    <!-- Existing PhotoText editor -->
    
    <!-- NEW: Document settings panel -->
    <div class="document-settings">
      <h3>Settings</h3>
      
      <div class="setting">
        <label>Visibility</label>
        <select v-model="document.visibility">
          <option value="private">🔒 Private</option>
          <option value="public">🌍 Public</option>
        </select>
      </div>
      
      <div class="setting">
        <label>
          <input type="checkbox" v-model="document.is_published" />
          Published
        </label>
      </div>
      
      <p v-if="document.visibility === 'public'" class="info">
        💡 Public documents can be viewed by anyone, even without logging in
      </p>
    </div>
  </div>
</template>
```

---

## Backwards Compatibility

**All existing code will continue to work:**

✅ **Creating photos/documents without `visibility` field:**
```javascript
// This still works - defaults to 'private'
const response = await fetch('/api/v1/phototext', {
  method: 'POST',
  body: JSON.stringify({
    title: "My Story",
    document_type: "general",
    content: photoTextContent
    // visibility not specified - defaults to 'private'
  })
})
```

✅ **Listing photos without authentication:**
```javascript
// Anonymous users now see public photos
const response = await fetch('/api/v1/photos')
// No Authorization header needed for public content
```

✅ **Existing authenticated requests:**
```javascript
// All existing authenticated requests work unchanged
const response = await fetch('/api/v1/photos', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
// User sees their own photos + public photos
```

---

## Testing Checklist

### Photo Visibility
- [ ] Create photo - verify defaults to `private`
- [ ] Change photo to `public` - verify update successful
- [ ] View own `private` photo while logged in - should work
- [ ] View own `public` photo while logged in - should work
- [ ] View another user's `private` photo - should get 404
- [ ] View another user's `public` photo - should work
- [ ] View `public` photo while logged out - should work
- [ ] View `private` photo while logged out - should get 404
- [ ] List photos while logged out - should only see public
- [ ] List photos while logged in - should see own + public

### PhotoText Visibility
- [ ] Create document without `visibility` - verify defaults to `private`
- [ ] Create document with `visibility: "public"` - verify stored correctly
- [ ] Update document visibility to `public` - verify update successful
- [ ] View own `private` document while logged in - should work
- [ ] View own `public` document while logged in - should work
- [ ] View another user's `private` document - should get 404
- [ ] View another user's `public` document - should work
- [ ] View `public` document while logged out - should work
- [ ] View `private` document while logged out - should get 404
- [ ] List documents while logged out - should only see public
- [ ] List documents while logged in - should see own + public

### UI/UX
- [ ] Visibility toggle visible for photo owner
- [ ] Visibility toggle NOT visible for non-owners
- [ ] Warning shown when setting to `public`
- [ ] Public badge visible on public photos
- [ ] Private badge visible on private photos
- [ ] Public indicator on shared public content

---

## Example API Flows

### Flow 1: User Makes Photo Public

```javascript
// 1. Get current photo
const photoResponse = await fetch('/api/v1/photos/abc123', {
  headers: { 'Authorization': `Bearer ${token}` }
})
const photo = await photoResponse.json()
// { hothash: "abc123", visibility: "private", ... }

// 2. Update visibility
const updateResponse = await fetch('/api/v1/photos/abc123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ visibility: 'public' })
})

// 3. Photo is now public - anyone can view it
const publicView = await fetch('/api/v1/photos/abc123')
// No auth needed - returns photo data
```

### Flow 2: Anonymous User Browses Public Gallery

```javascript
// 1. List all photos (no auth)
const response = await fetch('/api/v1/photos')
const data = await response.json()

// Only public photos returned
data.photos.forEach(photo => {
  console.log(photo.visibility) // Always "public"
})

// 2. View individual public photo
const photoResponse = await fetch(`/api/v1/photos/${photo.hothash}`)
const publicPhoto = await photoResponse.json()
// Works without authentication
```

### Flow 3: User Creates Public PhotoText Story

```javascript
const response = await fetch('/api/v1/phototext', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "Summer Vacation 2024",
    document_type: "album",
    content: photoTextContent,
    visibility: "public",  // Make it public from the start
    is_published: true
  })
})

const document = await response.json()
console.log(document.visibility) // "public"

// Anyone can now view this story
const publicUrl = `https://imalink.no/stories/${document.id}`
```

---

## Error Handling

### 404 vs 403
The API returns **404 (Not Found)** for both "doesn't exist" and "no access" to prevent enumeration attacks.

```javascript
try {
  const response = await fetch('/api/v1/photos/private-hash')
  if (response.status === 404) {
    // Could be: photo doesn't exist OR user doesn't have access
    // Don't reveal which one
    showMessage("Photo not found")
  }
} catch (error) {
  console.error(error)
}
```

### Unauthorized Updates
Only the owner can change visibility:

```javascript
// Non-owner trying to update
const response = await fetch('/api/v1/photos/someone-elses-photo', {
  method: 'PUT',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ visibility: 'public' })
})

if (response.status === 404) {
  // Returns 404, not 403, to prevent enumeration
  showMessage("Photo not found")
}
```

---

## API Reference Summary

| Endpoint | Anonymous Access | Authenticated Access | Notes |
|----------|------------------|---------------------|-------|
| `GET /api/v1/photos` | ✅ Public only | ✅ Own + Public | List photos |
| `GET /api/v1/photos/{hash}` | ✅ Public only | ✅ Own + Public | Get single photo |
| `PUT /api/v1/photos/{hash}` | ❌ | ✅ Own only | Update (including visibility) |
| `DELETE /api/v1/photos/{hash}` | ❌ | ✅ Own only | Delete photo |
| `GET /api/v1/phototext` | ✅ Public only | ✅ Own + Public | List documents |
| `GET /api/v1/phototext/{id}` | ✅ Public only | ✅ Own + Public | Get document |
| `POST /api/v1/phototext` | ❌ | ✅ Own only | Create document |
| `PUT /api/v1/phototext/{id}` | ❌ | ✅ Own only | Update (including visibility) |
| `DELETE /api/v1/phototext/{id}` | ❌ | ✅ Own only | Delete document |

---

## Questions?

Contact: Kjell (kjelkols)  
Backend commit: `e14b2ff`  
Migration: `2025_11_07_1859-106636619401_add_visibility_to_photos_and_documents`

---

## Future Phases

This is **Phase 1** - Basic Visibility only.

**Phase 2 (Future):** Collaborators
- Share specific photos/documents with specific users
- View vs Edit permissions
- Email invitations

**Phase 3 (Future):** Spaces
- Shared workspaces for teams
- All members see space content
- Space-level permissions

For now, implement Phase 1 only. Backend is ready for Phase 2/3 when needed.
