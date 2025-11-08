# Frontend Implementation Guide - Phase 1 Visibility

**Status:** ✅ Backend deployed and ready  
**Date:** November 8, 2025  
**For:** imalink-web frontend developers

---

## Overview

Phase 1 adds **visibility control** to photos and PhotoText documents. Users can now choose whether content is:
- **Private** (default) - Only visible to the owner
- **Space** (Phase 2) - Visible to members of specific spaces (NOT YET IMPLEMENTED)
- **Authenticated** - Visible to all logged-in users
- **Public** - Visible to everyone, including anonymous users

**Important:** Phase 1 implements the database schema and API for all four levels, but **Space functionality is not yet available**. The UI should show all four options, but Space should be disabled with a tooltip "Coming in Phase 2".

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
  "visibility": "private",  // "private", "space", "authenticated", or "public"
  "rating": 3,
  // ... other fields
}
```

**Note:** `visibility="space"` is accepted by the API but has no effect in Phase 1 (treated as private).

#### Update Photo Visibility
```http
PUT /api/v1/photos/{hothash}
Authorization: Bearer {token}  # Required
Content-Type: application/json

{
  "visibility": "authenticated"  // "private", "space", "authenticated", or "public"
}
```

**Note:** Setting `visibility="space"` is accepted but not functional in Phase 1.

#### List Photos (supports anonymous access)
```http
GET /api/v1/photos
Authorization: Bearer {token}  # Optional
```

**Behavior:**
- **Anonymous users:** Only see `public` photos
- **Authenticated users:** See own photos + `authenticated` photos + `public` photos
- **Note:** `space` visibility is not yet functional (treated as private)

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
  "visibility": "private",  // "private", "space", "authenticated", or "public"
  "is_published": true,
  "content": { ... },
  // ... other fields
}
```

**Note:** `visibility="space"` accepted but not functional in Phase 1.

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
  "visibility": "authenticated"  // "private", "space", "authenticated", or "public"
}
```

**Note:** `visibility="space"` accepted but not functional in Phase 1.

#### List Documents (supports anonymous access)
```http
GET /api/v1/phototext
Authorization: Bearer {token}  # Optional
```

**Behavior:**
- **Anonymous users:** Only see `public` documents
- **Authenticated users:** See own documents + `authenticated` documents + `public` documents
- **Note:** `space` visibility is not yet functional (treated as private)

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
        <option value="space" disabled>👥 Space (Coming in Phase 2)</option>
        <option value="authenticated">🌍 Authenticated (All Users)</option>
        <option value="public">� Public (Everyone)</option>
      </select>
      
      <p v-if="photo.visibility === 'public'" class="warning">
        ⚠️ This photo is visible to everyone, including anonymous users
      </p>
      <p v-else-if="photo.visibility === 'authenticated'" class="info">
        👥 This photo is visible to all logged-in users
      </p>
      <p v-else-if="photo.visibility === 'space'" class="info">
        🚧 Space functionality coming in Phase 2
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
        � Public
      </span>
      <span v-else-if="photo.visibility === 'authenticated'" class="badge badge-authenticated">
        👥 Users
      </span>
      <span v-else-if="photo.visibility === 'space'" class="badge badge-space">
        👥 Space
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

.badge-authenticated {
  background: rgba(59, 130, 246, 0.9);
  color: white;
}

.badge-space {
  background: rgba(139, 92, 246, 0.9);
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
          <option value="space" disabled>👥 Space (Phase 2)</option>
          <option value="authenticated">🌍 Authenticated</option>
          <option value="public">� Public</option>
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
      <p v-else-if="document.visibility === 'authenticated'" class="info">
        💡 Authenticated documents can be viewed by all logged-in users
      </p>
      <p v-else-if="document.visibility === 'space'" class="info">
        🚧 Space functionality coming in Phase 2
      </p>
    </div>
  </div>
</template>
```

---

## PhotoText Document and Photo Synchronization

**⚠️ IMPORTANT:** When a PhotoText document's visibility is set or changed, all photos referenced in the document are **automatically updated** to match the document's visibility level.

### Synchronization Behavior

1. **Creating a document:**
   - Document created with `visibility: "public"`
   - All photos referenced in the document are **automatically set to `public`**
   - Applies to:
     - Photos in `image` blocks
     - Photos in `collage` blocks (all images in the collage)
     - Cover image (if specified)

2. **Updating document visibility:**
   - Document visibility changed from `private` → `authenticated`
   - All referenced photos are **automatically updated to `authenticated`**

3. **Why this matters:**
   - Ensures consistency: A public document should not reference private photos
   - Prevents broken images: Anonymous users can view all photos in a public document
   - Simplifies UX: Users don't need to manually update each photo

### Example Workflow

```javascript
// User creates a public PhotoText document
const doc = {
  title: "My Public Story",
  visibility: "public",
  content: {
    version: "1.0",
    documentType: "general",
    title: "My Public Story",
    blocks: [
      {
        type: "image",
        hash: "abc123...",  // This photo was private
        alt: "Beautiful sunset"
      },
      {
        type: "collage",
        layout: "grid",
        images: [
          { hash: "def456...", alt: "Photo 1" },  // These were private too
          { hash: "ghi789...", alt: "Photo 2" }
        ]
      }
    ]
  }
}

// Backend automatically updates ALL referenced photos to "public"
await fetch('/api/v1/phototext', {
  method: 'POST',
  body: JSON.stringify(doc)
})

// After this call:
// - Document visibility = "public"
// - Photo abc123... visibility = "public" (was private)
// - Photo def456... visibility = "public" (was private)
// - Photo ghi789... visibility = "public" (was private)
```

### UI Recommendations

**Warning when changing document visibility:**

```vue
<template>
  <div class="visibility-warning" v-if="willAffectPhotos">
    <h3>⚠️ This will update {{ photoCount }} photos</h3>
    <p>
      Changing this document's visibility to <strong>{{ newVisibility }}</strong>
      will automatically update all {{ photoCount }} referenced photos to
      match this visibility level.
    </p>
    
    <ul>
      <li v-for="hash in affectedPhotoHashes" :key="hash">
        Photo {{ hash.substring(0, 8) }}... will become {{ newVisibility }}
      </li>
    </ul>
    
    <button @click="confirmUpdate">Continue</button>
    <button @click="cancelUpdate">Cancel</button>
  </div>
</template>
```

**Explanation in document editor:**

```vue
<div class="visibility-explainer">
  <p class="info-text">
    💡 <strong>Tip:</strong> When you set a document's visibility, all photos
    in the document will automatically be updated to match. This ensures
    that viewers can see all content consistently.
  </p>
</div>
```

### Edge Cases

1. **Photo not owned by user:**
   - Photos not owned by the document creator are **skipped**
   - Only the user's own photos are updated

2. **Photo doesn't exist:**
   - Missing photo hashes are **silently ignored**
   - Document creation/update continues normally

3. **Multiple documents referencing same photo:**
   - Photo visibility reflects the **most recent** document update
   - Users should be aware that editing one document may affect photos in other documents

---

## Backwards Compatibility
````

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

### Flow 1: User Makes Photo Authenticated

```javascript
// 1. Get current photo
const photoResponse = await fetch('/api/v1/photos/abc123', {
  headers: { 'Authorization': `Bearer ${token}` }
})
const photo = await photoResponse.json()
// { hothash: "abc123", visibility: "private", ... }

// 2. Update visibility to authenticated (all users)
const updateResponse = await fetch('/api/v1/photos/abc123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ visibility: 'authenticated' })
})

// 3. Photo is now visible to all logged-in users
// Anonymous users CANNOT see it
```

### Flow 2: Anonymous User Browses Public Gallery

```javascript
// 1. List all photos (no auth)
const response = await fetch('/api/v1/photos')
const data = await response.json()

// Only PUBLIC photos returned (not authenticated or private)
data.photos.forEach(photo => {
  console.log(photo.visibility) // Always "public"
})

// 2. View individual public photo
const photoResponse = await fetch(`/api/v1/photos/${photo.hothash}`)
const publicPhoto = await photoResponse.json()
// Works without authentication

// 3. Try to view authenticated photo - fails
const authPhoto = await fetch('/api/v1/photos/auth-only-hash')
// Returns 404 - requires login
```

### Flow 3: Logged-in User Browses Community Content

```javascript
// User sees: own photos + authenticated photos + public photos
const response = await fetch('/api/v1/photos', {
  headers: { 'Authorization': `Bearer ${token}` }
})
const data = await response.json()

data.photos.forEach(photo => {
  // Can be "private" (own), "authenticated", or "public"
  console.log(photo.visibility, photo.user_id)
})
```

### Flow 4: Create Public PhotoText Story

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
    visibility: "public",  // Completely public
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
| `GET /api/v1/photos` | ✅ Public only | ✅ Own + Authenticated + Public | List photos (space N/A in Phase 1) |
| `GET /api/v1/photos/{hash}` | ✅ Public only | ✅ Own + Authenticated + Public | Get single photo |
| `PUT /api/v1/photos/{hash}` | ❌ | ✅ Own only | Update (including visibility) |
| `DELETE /api/v1/photos/{hash}` | ❌ | ✅ Own only | Delete photo |
| `GET /api/v1/phototext` | ✅ Public only | ✅ Own + Authenticated + Public | List documents (space N/A in Phase 1) |
| `GET /api/v1/phototext/{id}` | ✅ Public only | ✅ Own + Authenticated + Public | Get document |
| `POST /api/v1/phototext` | ❌ | ✅ Own only | Create document |
| `PUT /api/v1/phototext/{id}` | ❌ | ✅ Own only | Update (including visibility) |
| `DELETE /api/v1/phototext/{id}` | ❌ | ✅ Own only | Delete document |

**Note:** `visibility="space"` is accepted by all endpoints but treated as `private` until Phase 2 implements Space infrastructure.

---

## Questions?

Contact: Kjell (kjelkols)  
Backend commit: `e14b2ff`  
Migration: `2025_11_07_1859-106636619401_add_visibility_to_photos_and_documents`

---

## Future Phases

This is **Phase 1** - Basic Visibility with four levels defined.

**Phase 2 (Future):** Spaces Infrastructure
- Create and manage shared workspaces
- Invite members to spaces
- Share photos/documents to multiple spaces
- `visibility="space"` becomes functional
- Space-based content discovery

For now, implement Phase 1 with Space option visible but disabled. Backend accepts `visibility="space"` for forward compatibility.
