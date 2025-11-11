# Frontend Timeline Implementation Guide

**Last Updated:** November 10, 2025  
**API Version:** v2.2  
**Status:** Design Phase - API not yet implemented

## Overview

The Timeline API provides hierarchical time-based navigation for photos, enabling users to browse their photo library organized by year, month, day, and hour. This guide helps frontend developers implement an intuitive timeline interface.

## Quick Start

### Basic Timeline Request

```typescript
// Get years with photo counts
const response = await fetch('https://api.trollfjell.com/api/v1/timeline?granularity=year', {
  headers: {
    'Authorization': `Bearer ${userToken}` // Optional for anonymous access
  }
});

const timeline = await response.json();
console.log(timeline.data); // Array of year buckets with counts and previews
```

### Response Structure

All timeline responses follow this structure:

```typescript
interface TimelineBucket {
  year: number;
  month?: number;      // Only for month/day/hour granularity
  day?: number;        // Only for day/hour granularity
  hour?: number;       // Only for hour granularity
  count: number;       // Number of photos in this bucket
  preview_hothash: string;    // HotHash of representative photo
  preview_url: string;        // Direct URL to hotpreview
  date_range: {
    first: string;     // ISO 8601 timestamp of earliest photo
    last: string;      // ISO 8601 timestamp of latest photo
  };
}

interface TimelineResponse {
  data: TimelineBucket[];
  meta: {
    total_years?: number;   // Total years with photos
    total_months?: number;  // Total months (when filtering by year)
    total_days?: number;    // Total days (when filtering by month)
    total_hours?: number;   // Total hours (when filtering by day)
    total_photos: number;   // Total photos in current view
    granularity: 'year' | 'month' | 'day' | 'hour';
    year?: number;          // Present when filtered
    month?: number;         // Present when filtered
    day?: number;           // Present when filtered
  };
}
```

## Implementation Patterns

### 1. Year Overview Grid

Display years as cards with preview images and photo counts:

```typescript
async function loadYearOverview() {
  const response = await fetch('/api/v1/timeline?granularity=year', {
    headers: getAuthHeaders() // Your auth helper
  });
  
  const { data, meta } = await response.json();
  
  return data.map(bucket => ({
    year: bucket.year,
    photoCount: bucket.count,
    previewUrl: bucket.preview_url,
    dateRange: {
      from: new Date(bucket.date_range.first),
      to: new Date(bucket.date_range.last)
    }
  }));
}

// React component example
function YearGrid() {
  const [years, setYears] = useState([]);
  
  useEffect(() => {
    loadYearOverview().then(setYears);
  }, []);
  
  return (
    <div className="year-grid">
      {years.map(year => (
        <YearCard
          key={year.year}
          year={year.year}
          count={year.photoCount}
          previewUrl={year.previewUrl}
          onClick={() => navigateToYear(year.year)}
        />
      ))}
    </div>
  );
}
```

### 2. Hierarchical Drill-Down

Navigate from year → month → day → hour:

```typescript
interface TimelineState {
  granularity: 'year' | 'month' | 'day' | 'hour';
  year?: number;
  month?: number;
  day?: number;
}

async function loadTimeline(state: TimelineState) {
  const params = new URLSearchParams({
    granularity: state.granularity
  });
  
  if (state.year) params.append('year', state.year.toString());
  if (state.month) params.append('month', state.month.toString());
  if (state.day) params.append('day', state.day.toString());
  
  const response = await fetch(`/api/v1/timeline?${params}`, {
    headers: getAuthHeaders()
  });
  
  return response.json();
}

// Navigation example
function TimelineNavigator() {
  const [state, setState] = useState<TimelineState>({ granularity: 'year' });
  const [buckets, setBuckets] = useState([]);
  
  useEffect(() => {
    loadTimeline(state).then(data => setBuckets(data.data));
  }, [state]);
  
  const drillDown = (bucket: TimelineBucket) => {
    if (state.granularity === 'year') {
      setState({ granularity: 'month', year: bucket.year });
    } else if (state.granularity === 'month') {
      setState({ 
        granularity: 'day', 
        year: bucket.year, 
        month: bucket.month 
      });
    } else if (state.granularity === 'day') {
      setState({ 
        granularity: 'hour', 
        year: bucket.year, 
        month: bucket.month, 
        day: bucket.day 
      });
    }
  };
  
  const breadcrumbBack = () => {
    if (state.granularity === 'hour') {
      setState(prev => ({ ...prev, granularity: 'day', day: undefined }));
    } else if (state.granularity === 'day') {
      setState(prev => ({ ...prev, granularity: 'month', month: undefined }));
    } else if (state.granularity === 'month') {
      setState({ granularity: 'year' });
    }
  };
  
  return (
    <>
      <Breadcrumb state={state} onBack={breadcrumbBack} />
      <BucketGrid buckets={buckets} onSelect={drillDown} />
    </>
  );
}
```

### 3. Infinite Scroll Timeline

Load timeline data progressively for smooth scrolling:

```typescript
function InfiniteTimeline() {
  const [items, setItems] = useState<TimelineBucket[]>([]);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  
  const loadMoreYears = async () => {
    // Load one year at a time in month granularity
    const response = await fetch(
      `/api/v1/timeline?granularity=month&year=${currentYear}`,
      { headers: getAuthHeaders() }
    );
    
    const { data } = await response.json();
    setItems(prev => [...prev, ...data]);
    setCurrentYear(prev => prev - 1); // Load previous year next
  };
  
  return (
    <InfiniteScroll
      dataLength={items.length}
      next={loadMoreYears}
      hasMore={currentYear >= 2000} // Adjust based on your needs
      loader={<Spinner />}
    >
      {items.map((bucket, idx) => (
        <MonthSection
          key={`${bucket.year}-${bucket.month}`}
          bucket={bucket}
        />
      ))}
    </InfiniteScroll>
  );
}
```

### 4. Calendar View

Display months in a calendar grid:

```typescript
async function loadCalendarMonth(year: number, month: number) {
  const response = await fetch(
    `/api/v1/timeline?granularity=day&year=${year}&month=${month}`,
    { headers: getAuthHeaders() }
  );
  
  const { data } = await response.json();
  
  // Convert to calendar grid (day of month -> bucket)
  const calendar: Record<number, TimelineBucket> = {};
  data.forEach(bucket => {
    calendar[bucket.day] = bucket;
  });
  
  return calendar;
}

function CalendarMonth({ year, month }: { year: number; month: number }) {
  const [calendar, setCalendar] = useState<Record<number, TimelineBucket>>({});
  
  useEffect(() => {
    loadCalendarMonth(year, month).then(setCalendar);
  }, [year, month]);
  
  const daysInMonth = new Date(year, month, 0).getDate();
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  
  return (
    <div className="calendar-grid">
      {days.map(day => {
        const bucket = calendar[day];
        return (
          <CalendarDay
            key={day}
            day={day}
            hasPhotos={!!bucket}
            count={bucket?.count}
            previewUrl={bucket?.preview_url}
            onClick={() => bucket && navigateToDay(year, month, day)}
          />
        );
      })}
    </div>
  );
}
```

## Anonymous Access

Timeline API supports anonymous users viewing public photos:

```typescript
// Anonymous request (no Authorization header)
async function loadPublicTimeline() {
  const response = await fetch('/api/v1/timeline?granularity=year');
  // No auth header = only public photos
  
  const { data } = await response.json();
  // Returns only years/months/days with public photos
  return data;
}

// Use case: Public gallery page
function PublicGallery() {
  const [years, setYears] = useState([]);
  
  useEffect(() => {
    // Works without login
    loadPublicTimeline().then(setYears);
  }, []);
  
  return (
    <div className="public-gallery">
      <h1>Public Photo Gallery</h1>
      <YearGrid years={years} />
    </div>
  );
}
```

## Performance Optimization

### 1. Caching Strategy

```typescript
// Simple cache implementation
const timelineCache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 3600000; // 1 hour

async function getCachedTimeline(params: URLSearchParams) {
  const key = params.toString();
  const cached = timelineCache.get(key);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  
  const response = await fetch(`/api/v1/timeline?${params}`);
  const data = await response.json();
  
  timelineCache.set(key, { data, timestamp: Date.now() });
  return data;
}
```

### 2. Prefetching

```typescript
// Prefetch next level on hover
function YearCard({ year, onHover }: { year: number; onHover: () => void }) {
  const prefetchMonths = () => {
    // Preload month data for faster navigation
    fetch(`/api/v1/timeline?granularity=month&year=${year}`, {
      headers: getAuthHeaders()
    });
  };
  
  return (
    <div 
      className="year-card"
      onMouseEnter={prefetchMonths}
    >
      <h2>{year}</h2>
    </div>
  );
}
```

### 3. Progressive Enhancement

```typescript
// Load low-res previews first, then high-res
function BucketPreview({ previewUrl }: { previewUrl: string }) {
  const [loaded, setLoaded] = useState(false);
  
  return (
    <div className="preview-container">
      {!loaded && <Skeleton />}
      <img
        src={previewUrl}
        onLoad={() => setLoaded(true)}
        className={loaded ? 'visible' : 'hidden'}
        loading="lazy"
      />
    </div>
  );
}
```

## Visibility Handling

Timeline respects visibility levels (private/authenticated/public):

```typescript
// Authenticated user sees more buckets than anonymous
async function compareAnonymousVsAuthenticated() {
  // Anonymous request
  const publicResponse = await fetch('/api/v1/timeline?granularity=year');
  const publicData = await publicResponse.json();
  
  // Authenticated request
  const authResponse = await fetch('/api/v1/timeline?granularity=year', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const authData = await authResponse.json();
  
  console.log('Public years:', publicData.meta.total_years);
  console.log('Authenticated years:', authData.meta.total_years);
  // Authenticated typically shows more years (includes private photos)
}
```

**Visibility Rules:**
- **Anonymous:** Only `public` photos appear in timeline
- **Authenticated:** Own photos + `authenticated` + `public` photos
- Empty buckets (no accessible photos) are excluded from response

## UI/UX Recommendations

### 1. Breadcrumb Navigation

```typescript
function TimelineBreadcrumb({ state }: { state: TimelineState }) {
  return (
    <nav className="breadcrumb">
      <span onClick={() => goTo({ granularity: 'year' })}>All Years</span>
      {state.year && (
        <> / <span onClick={() => goTo({ granularity: 'month', year: state.year })}>
          {state.year}
        </span></>
      )}
      {state.month && (
        <> / <span onClick={() => goTo({ granularity: 'day', year: state.year, month: state.month })}>
          {getMonthName(state.month)}
        </span></>
      )}
      {state.day && (
        <> / <span>{state.day}</span></>
      )}
    </nav>
  );
}
```

### 2. Visual Density

Show photo counts and date ranges to help users navigate:

```tsx
function BucketCard({ bucket }: { bucket: TimelineBucket }) {
  const formatDateRange = () => {
    const first = new Date(bucket.date_range.first);
    const last = new Date(bucket.date_range.last);
    return `${first.toLocaleDateString()} - ${last.toLocaleDateString()}`;
  };
  
  return (
    <div className="bucket-card">
      <img src={bucket.preview_url} alt={`Preview for ${bucket.year}`} />
      <div className="bucket-info">
        <h3>{bucket.year} {bucket.month && `- ${getMonthName(bucket.month)}`}</h3>
        <p>{bucket.count} photos</p>
        <small>{formatDateRange()}</small>
      </div>
    </div>
  );
}
```

### 3. Empty States

Handle periods with no accessible photos gracefully:

```typescript
function TimelineView({ buckets }: { buckets: TimelineBucket[] }) {
  if (buckets.length === 0) {
    return (
      <div className="empty-timeline">
        <p>No photos found for this period</p>
        <button onClick={goBack}>Go Back</button>
      </div>
    );
  }
  
  return <BucketGrid buckets={buckets} />;
}
```

## Error Handling

```typescript
async function loadTimelineWithErrorHandling(params: URLSearchParams) {
  try {
    const response = await fetch(`/api/v1/timeline?${params}`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication required');
      } else if (response.status === 400) {
        throw new Error('Invalid timeline parameters');
      }
      throw new Error(`Timeline error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Timeline loading failed:', error);
    // Show error UI
    throw error;
  }
}
```

## Testing Considerations

### Mock Data for Development

```typescript
// Mock timeline response for testing
const mockTimelineYears: TimelineResponse = {
  data: [
    {
      year: 2024,
      count: 1247,
      preview_hothash: "abc123",
      preview_url: "/api/v1/photos/abc123/hotpreview",
      date_range: {
        first: "2024-01-05T08:23:12Z",
        last: "2024-12-28T19:45:00Z"
      }
    },
    {
      year: 2023,
      count: 892,
      preview_hothash: "def456",
      preview_url: "/api/v1/photos/def456/hotpreview",
      date_range: {
        first: "2023-02-14T10:30:00Z",
        last: "2023-12-31T23:59:59Z"
      }
    }
  ],
  meta: {
    total_years: 5,
    total_photos: 4521,
    granularity: "year"
  }
};
```

## Integration with Photos API

After selecting a time bucket, load actual photos:

```typescript
async function navigateToTimeRange(bucket: TimelineBucket) {
  // User clicked on a day bucket, load photos for that day
  const startDate = bucket.date_range.first;
  const endDate = bucket.date_range.last;
  
  // Use Photos API to get actual photos in this range
  const params = new URLSearchParams({
    taken_after: startDate,
    taken_before: endDate,
    page_size: '50'
  });
  
  const response = await fetch(`/api/v1/photos/?${params}`, {
    headers: getAuthHeaders()
  });
  
  const photos = await response.json();
  // Display photos in grid/lightbox
  showPhotoGallery(photos.data);
}
```

## Next Steps

1. **Wait for API implementation** - Timeline endpoints are designed but not yet deployed
2. **Test with real data** - Once deployed, test with your photo collection
3. **Optimize for your use case** - Adapt examples to your framework (React/Vue/Svelte)
4. **Monitor performance** - Watch for slow queries on large collections
5. **Provide feedback** - Report issues or suggestions for API improvements

## Related Documentation

- [Timeline API Specification](./TIMELINE_API.md) - Complete API design document
- [API Reference](./API_REFERENCE.md) - Full API documentation
- [Frontend Integration Guide](./FRONTEND_INTEGRATION.md) - General frontend integration
- [Visibility Implementation](./FRONTEND_VISIBILITY_IMPLEMENTATION.md) - Visibility system details

## Questions?

For questions about timeline implementation, refer to the complete [Timeline API Documentation](./TIMELINE_API.md) or contact the backend team.
