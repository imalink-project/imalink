# Frontend Event Implementation Guide

**For:** imalink-web and imalink-desktop frontend developers  
**Backend Version:** v3.1  
**Feature:** Events (Hierarchical Photo Organization)

## Overview

Events organize photos by hierarchical context (trips, occasions, projects). Unlike Collections (flat, curated sets), Events support parent-child relationships for natural organization.

**Key Concepts:**
- **Hierarchical**: Events can have parent-child relationships (e.g., "London 2025" → "Tower of London")
- **Many-to-many**: Photos can belong to multiple events
- **Recursive**: Can query all photos in event + descendants
- **User-scoped**: Each user has their own event hierarchy
- **Optional metadata**: Dates, location, GPS coordinates

## Data Model

### Event Schema

```typescript
interface Event {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  parent_event_id: number | null;
  
  // Temporal context (optional)
  start_date: string | null;  // ISO 8601
  end_date: string | null;    // ISO 8601
  
  // Spatial context (optional)
  location_name: string | null;
  gps_latitude: number | null;   // -90 to 90
  gps_longitude: number | null;  // -180 to 180
  
  // UI ordering
  sort_order: number;  // Default 0
  
  // Timestamps
  created_at: string;
  updated_at: string;
}
```

### Event with Photos Count

```typescript
interface EventWithPhotos extends Event {
  photo_count: number;  // Direct photos (not recursive)
}
```

### Event Tree Node (Recursive)

```typescript
interface EventTreeNode extends Event {
  children: EventTreeNode[];
  photo_count: number;  // Direct photos only
}

interface EventTreeResponse {
  events: EventTreeNode[];
  total_events: number;
}
```

## API Integration

### 1. List Events

**Endpoint:** `GET /api/v1/events/`

```typescript
// List root events
const rootEvents = await fetch('/api/v1/events/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// List children of specific event
const childEvents = await fetch('/api/v1/events/?parent_id=1', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

**Returns:** `EventWithPhotos[]`

### 2. Get Event Tree

**Endpoint:** `GET /api/v1/events/tree`

```typescript
// Get full tree
const tree = await fetch('/api/v1/events/tree', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Get subtree from specific event
const subtree = await fetch('/api/v1/events/tree?root_id=1', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

**Returns:** `EventTreeResponse`

**Use for:** Hierarchical navigation, breadcrumbs, tree visualizations

### 3. Create Event

**Endpoint:** `POST /api/v1/events/`

```typescript
const newEvent = await fetch('/api/v1/events/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "London Trip 2025",
    description: "Summer vacation",
    parent_event_id: null,  // null = root level
    start_date: "2025-07-01T00:00:00Z",
    end_date: "2025-07-10T00:00:00Z",
    location_name: "London, UK",
    gps_latitude: 51.5074,
    gps_longitude: -0.1278,
    sort_order: 0
  })
}).then(r => r.json());
```

**Required:** `name` only  
**Optional:** All other fields

### 4. Update Event

**Endpoint:** `PUT /api/v1/events/{event_id}`

```typescript
const updated = await fetch('/api/v1/events/1', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "Updated Name",
    description: "New description"
    // Only include fields to update
  })
}).then(r => r.json());
```

**All fields optional** - partial updates supported

### 5. Move Event

**Endpoint:** `POST /api/v1/events/{event_id}/move`

```typescript
// Move to new parent
await fetch('/api/v1/events/3/move', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    new_parent_id: 5  // or null for root level
  })
});
```

**Validation:** Backend prevents cycles (can't move to own descendant)

### 6. Delete Event

**Endpoint:** `DELETE /api/v1/events/{event_id}`

```typescript
await fetch('/api/v1/events/1', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

**Behavior:**
- Children become root events (parent_event_id → null)
- Photos remain but lose event association

### 7. Add Photos to Event

**Endpoint:** `POST /api/v1/events/{event_id}/photos`

```typescript
const result = await fetch('/api/v1/events/1/photos', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    hothashes: ["abc123...", "def456...", "ghi789..."]
  })
}).then(r => r.json());

// Returns: { event_id: 1, photos_added: 3 }
```

**Idempotent:** Duplicates skipped  
**Important:** Uses `hothashes` (not photo IDs) - ImaLink design philosophy

### 8. Remove Photos from Event

**Endpoint:** `DELETE /api/v1/events/{event_id}/photos`

```typescript
const result = await fetch('/api/v1/events/1/photos', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    hothashes: ["abc123...", "def456..."]
  })
}).then(r => r.json());

// Returns: { event_id: 1, photos_removed: 2 }
```

### 9. Get Event Photos

**Endpoint:** `GET /api/v1/events/{event_id}/photos`

```typescript
// Direct photos only
const photos = await fetch('/api/v1/events/1/photos', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Include all descendant events
const allPhotos = await fetch('/api/v1/events/1/photos?include_descendants=true', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

**Returns:** `PhotoResponse[]`

## UI Implementation Patterns

### Pattern 1: Event Browser (List View)

```typescript
// Show root events
const rootEvents = await api.getEvents();

// When user clicks event, show children
const children = await api.getEvents({ parent_id: selectedEvent.id });

// Breadcrumb navigation
const breadcrumbs = buildBreadcrumb(currentEvent);
```

**UI Components:**
- Event list/grid with photo counts
- Click to drill down to children
- Breadcrumb navigation (Home > Trip > Day)
- "Back to parent" button

### Pattern 2: Tree View

```typescript
// Fetch full tree
const { events, total_events } = await api.getEventTree();

// Render recursive tree
function EventTreeNode({ node }: { node: EventTreeNode }) {
  return (
    <div>
      <div onClick={() => selectEvent(node)}>
        {node.name} ({node.photo_count})
      </div>
      {node.children.map(child => (
        <EventTreeNode key={child.id} node={child} />
      ))}
    </div>
  );
}
```

**UI Components:**
- Collapsible tree view
- Drag-and-drop for rearranging
- Context menu (create child, delete, move)

### Pattern 3: Event Gallery

```typescript
// Show photos in event
const photos = await api.getEventPhotos(eventId, { 
  includeDescendants: false 
});

// Show all photos in event hierarchy
const allPhotos = await api.getEventPhotos(eventId, { 
  includeDescendants: true 
});
```

**UI Components:**
- Photo grid/masonry
- Toggle "include sub-events"
- Event info header (name, dates, location)

### Pattern 4: Photo Multi-Select + Add to Event

```typescript
// User selects photos, then picks event
const selectedHothashes = ["abc123...", "def456...", "ghi789..."];
const targetEventId = 5;

const result = await api.addPhotosToEvent(targetEventId, selectedHothashes);
console.log(`Added ${result.photos_added} photos`);
```

**UI Components:**
- Photo selection checkboxes
- "Add to Event" button → Event picker modal
- Success toast with count

### Pattern 5: Drag-and-Drop to Event

```typescript
// User drags photos onto event
function onDrop(hothashes: string[], eventId: number) {
  await api.addPhotosToEvent(eventId, hothashes);
  refreshGallery();
}
```

## State Management (Example with Zustand)

```typescript
import create from 'zustand';

interface EventStore {
  events: EventWithPhotos[];
  currentEvent: Event | null;
  eventTree: EventTreeNode[];
  
  fetchEvents: (parentId?: number) => Promise<void>;
  fetchEventTree: () => Promise<void>;
  createEvent: (data: CreateEventData) => Promise<Event>;
  updateEvent: (id: number, data: UpdateEventData) => Promise<Event>;
  deleteEvent: (id: number) => Promise<void>;
  addPhotos: (eventId: number, photoIds: number[]) => Promise<void>;
}

export const useEventStore = create<EventStore>((set, get) => ({
  events: [],
  currentEvent: null,
  eventTree: [],
  
  fetchEvents: async (parentId) => {
    const url = parentId 
      ? `/api/v1/events/?parent_id=${parentId}`
      : '/api/v1/events/';
    const events = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    set({ events });
  },
  
  fetchEventTree: async () => {
    const tree = await fetch('/api/v1/events/tree', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    set({ eventTree: tree.events });
  },
  
  // ... other actions
}));
```

## Validation Rules

### Frontend Validation

```typescript
function validateEvent(data: Partial<Event>): string[] {
  const errors: string[] = [];
  
  if (data.name && data.name.length === 0) {
    errors.push("Name is required");
  }
  if (data.name && data.name.length > 200) {
    errors.push("Name max 200 characters");
  }
  if (data.description && data.description.length > 2000) {
    errors.push("Description max 2000 characters");
  }
  if (data.gps_latitude && (data.gps_latitude < -90 || data.gps_latitude > 90)) {
    errors.push("Latitude must be between -90 and 90");
  }
  if (data.gps_longitude && (data.gps_longitude < -180 || data.gps_longitude > 180)) {
    errors.push("Longitude must be between -180 and 180");
  }
  
  return errors;
}
```

### Backend Validation (Reference)

Backend validates:
- ✅ Name required (1-200 chars)
- ✅ Description max 2000 chars
- ✅ Parent event exists and belongs to user
- ✅ Move operations don't create cycles
- ✅ GPS coordinates in valid range
- ✅ All photos exist and belong to user

## Comparison: Events vs Collections

| Feature | Events | Collections |
|---------|--------|-------------|
| Structure | Hierarchical (parent-child) | Flat |
| Purpose | Contextual organization | Curated sets |
| Metadata | Dates, location, GPS | Description only |
| Hierarchy | Unlimited depth | None |
| Use Case | Trips, projects, timeline | Portfolios, albums |
| Queries | Recursive (with descendants) | Direct only |

**When to use:**
- **Events**: "London Trip 2025" with sub-events like "Day 1", "Tower of London"
- **Collections**: "Best Portraits 2025", "Portfolio Selection"

## Testing Checklist

- [ ] List root events
- [ ] List children of specific event
- [ ] Get full event tree
- [ ] Create root event
- [ ] Create child event
- [ ] Update event name/description
- [ ] Move event to new parent
- [ ] Prevent cycle when moving (error handling)
- [ ] Delete event (children become roots)
- [ ] Add photos to event
- [ ] Remove photos from event
- [ ] Get event photos (direct)
- [ ] Get event photos (recursive with descendants)
- [ ] Display photo counts correctly
- [ ] Breadcrumb navigation
- [ ] Drag-and-drop photos to events

## Error Handling

```typescript
async function safeEventOperation<T>(
  operation: () => Promise<T>
): Promise<{ success: boolean; data?: T; error?: string }> {
  try {
    const data = await operation();
    return { success: true, data };
  } catch (error) {
    if (error.status === 404) {
      return { success: false, error: "Event not found" };
    }
    if (error.status === 422) {
      return { success: false, error: "Validation error (e.g., cycle detected)" };
    }
    return { success: false, error: "Unknown error" };
  }
}

// Usage
const result = await safeEventOperation(() => 
  api.moveEvent(eventId, newParentId)
);

if (!result.success) {
  showToast(result.error, 'error');
}
```

## Performance Tips

1. **Use Tree Endpoint Sparingly**: Full tree query is expensive for large hierarchies
2. **Cache Event Lists**: Events change less frequently than photos
3. **Lazy Load Children**: Only fetch children when user expands node
4. **Pagination**: For events with many photos, paginate photo lists
5. **Optimistic Updates**: Update UI immediately, sync with backend async

## Future Enhancements (Not Yet Implemented)

- Auto-suggest events from EXIF dates/locations (frontend intelligence)
- Bulk move photos between events
- Event templates
- Share events publicly (requires visibility field)
- Event statistics (photo count over time)

## Questions?

- **API Reference**: `/docs/API_REFERENCE.md` (section "Events")
- **Backend Tests**: `/tests/api/test_events_api.py` (21 comprehensive tests)
- **Backend Code**: `/src/api/v1/events.py`, `/src/services/event_service.py`

---

**Last Updated:** December 2, 2025  
**Backend Version:** v3.1 (Events feature)
