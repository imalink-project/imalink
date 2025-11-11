# Timeline API - Photo Time-Based Navigation

**Status:** 📝 Design Document  
**Date:** November 10, 2025  
**Inspired by:** Immich, Apple Photos, Google Photos

---

## Overview

The Timeline API provides hierarchical time-based navigation of photos with automatic aggregation, representative previews, and visibility-aware filtering. Users can drill down from years → months → days → hours to explore their photo collection chronologically.

### Key Features

- ✅ **Hierarchical navigation** - Year/Month/Day/Hour granularity
- ✅ **Representative previews** - Smart selection of best photo per period
- ✅ **Visibility filtering** - Respects private/authenticated/public access
- ✅ **Anonymous support** - Public photos visible without authentication
- ✅ **Performance optimized** - Aggregation on server, lazy loading
- ✅ **Scalable** - Handles millions of photos efficiently

---

## API Endpoints

### Base Endpoint

```
GET /api/v1/timeline
```

All timeline queries use a single flexible endpoint with query parameters.

### Query Parameters

| Parameter | Type | Required | Description | Values |
|-----------|------|----------|-------------|--------|
| `granularity` | string | No | Time bucket size | `year`, `month`, `day`, `hour` (default: `year`) |
| `year` | integer | No | Filter to specific year | 1900-2100 |
| `month` | integer | No | Filter to specific month | 1-12 (requires `year`) |
| `day` | integer | No | Filter to specific day | 1-31 (requires `year` and `month`) |

### Authentication

- **Optional** - Works for both authenticated and anonymous users
- **Anonymous users** see only `public` photos
- **Authenticated users** see: own photos + `authenticated` + `public` photos

---

## Response Format

### Years Aggregation

```http
GET /api/v1/timeline?granularity=year
Authorization: Bearer <token>  # Optional
```

**Response** (`200 OK`):
```json
{
  "data": [
    {
      "year": 2024,
      "count": 1247,
      "preview_hothash": "abc123...",
      "preview_url": "/api/v1/photos/abc123.../hotpreview",
      "date_range": {
        "first": "2024-01-05T08:23:12Z",
        "last": "2024-12-28T19:45:00Z"
      }
    },
    {
      "year": 2023,
      "count": 892,
      "preview_hothash": "def456...",
      "preview_url": "/api/v1/photos/def456.../hotpreview",
      "date_range": {
        "first": "2023-02-14T10:30:00Z",
        "last": "2023-12-31T23:59:59Z"
      }
    }
  ],
  "meta": {
    "total_years": 5,
    "total_photos": 4521,
    "granularity": "year"
  }
}
```

### Months Aggregation

```http
GET /api/v1/timeline?granularity=month&year=2024
Authorization: Bearer <token>  # Optional
```

**Response** (`200 OK`):
```json
{
  "data": [
    {
      "year": 2024,
      "month": 12,
      "count": 156,
      "preview_hothash": "xyz789...",
      "preview_url": "/api/v1/photos/xyz789.../hotpreview",
      "date_range": {
        "first": "2024-12-01T09:15:00Z",
        "last": "2024-12-28T19:45:00Z"
      }
    },
    {
      "year": 2024,
      "month": 11,
      "count": 203,
      "preview_hothash": "uvw456...",
      "preview_url": "/api/v1/photos/uvw456.../hotpreview",
      "date_range": {
        "first": "2024-11-03T14:22:00Z",
        "last": "2024-11-29T21:10:00Z"
      }
    }
  ],
  "meta": {
    "total_months": 12,
    "total_photos": 1247,
    "granularity": "month",
    "year": 2024
  }
}
```

### Days Aggregation

```http
GET /api/v1/timeline?granularity=day&year=2024&month=12
Authorization: Bearer <token>  # Optional
```

**Response** (`200 OK`):
```json
{
  "data": [
    {
      "year": 2024,
      "month": 12,
      "day": 28,
      "count": 45,
      "preview_hothash": "rst123...",
      "preview_url": "/api/v1/photos/rst123.../hotpreview",
      "date_range": {
        "first": "2024-12-28T08:00:00Z",
        "last": "2024-12-28T19:45:00Z"
      }
    },
    {
      "year": 2024,
      "month": 12,
      "day": 25,
      "count": 89,
      "preview_hothash": "opq789...",
      "preview_url": "/api/v1/photos/opq789.../hotpreview",
      "date_range": {
        "first": "2024-12-25T06:30:00Z",
        "last": "2024-12-25T23:15:00Z"
      }
    }
  ],
  "meta": {
    "total_days": 28,
    "total_photos": 156,
    "granularity": "day",
    "year": 2024,
    "month": 12
  }
}
```

### Hours Aggregation

```http
GET /api/v1/timeline?granularity=hour&year=2024&month=12&day=28
Authorization: Bearer <token>  # Optional
```

**Response** (`200 OK`):
```json
{
  "data": [
    {
      "year": 2024,
      "month": 12,
      "day": 28,
      "hour": 14,
      "count": 12,
      "preview_hothash": "lmn456...",
      "preview_url": "/api/v1/photos/lmn456.../hotpreview",
      "date_range": {
        "first": "2024-12-28T14:05:32Z",
        "last": "2024-12-28T14:58:41Z"
      }
    },
    {
      "year": 2024,
      "month": 12,
      "day": 28,
      "hour": 10,
      "count": 8,
      "preview_hothash": "ijk789...",
      "preview_url": "/api/v1/photos/ijk789.../hotpreview",
      "date_range": {
        "first": "2024-12-28T10:12:00Z",
        "last": "2024-12-28T10:45:30Z"
      }
    }
  ],
  "meta": {
    "total_hours": 6,
    "total_photos": 45,
    "granularity": "hour",
    "year": 2024,
    "month": 12,
    "day": 28
  }
}
```

---

## Representative Preview Selection

The API selects the "best" photo to represent each time period using the following priority:

### Selection Algorithm

```python
def select_representative_photo(photos):
    """
    Priority order for selecting preview photo:
    1. Highest rated photo (rating 4-5)
    2. Temporally centered photo (middle of period)
    3. First photo in period (fallback)
    """
    
    # Priority 1: Highest rated photos
    highly_rated = [p for p in photos if p.rating >= 4]
    if highly_rated:
        return max(highly_rated, key=lambda p: (p.rating, p.taken_at))
    
    # Priority 2: Middle photo (temporal center)
    if len(photos) > 1:
        return sorted(photos, key=lambda p: p.taken_at)[len(photos) // 2]
    
    # Priority 3: First photo
    return photos[0]
```

### Future Enhancements

Planned improvements for preview selection:
- **Face detection** - Prioritize photos with people
- **Quality score** - Image sharpness and composition analysis
- **GPS clustering** - Prefer photos from unique locations
- **Event detection** - First photo of detected "events"

---

## Visibility Filtering

### Access Rules

The timeline respects the same visibility rules as the Photos API:

| User Type | Sees Photos With Visibility |
|-----------|------------------------------|
| Anonymous | `public` only |
| Authenticated | Own photos + `authenticated` + `public` |
| Owner | All own photos (any visibility) |

### Implementation

```python
def apply_visibility_filter(query, user_id: Optional[int]):
    """Apply visibility filtering based on user authentication"""
    if user_id:
        # Authenticated: own + authenticated + public
        query = query.filter(
            db.or_(
                Photo.user_id == user_id,
                Photo.visibility == 'public',
                Photo.visibility == 'authenticated'
            )
        )
    else:
        # Anonymous: public only
        query = query.filter(Photo.visibility == 'public')
    
    return query
```

### Empty Periods

**Behavior:** If a time period has no accessible photos (due to visibility), it is **not included** in the response.

**Example:**
- User has 100 private photos in January 2024
- Anonymous request for 2024 months
- January 2024 **not returned** (no public photos)

---

## Performance Considerations

### Database Indexes

Required indexes for optimal performance:

```sql
-- Primary timeline index
CREATE INDEX idx_photos_taken_at ON photos(taken_at);

-- Visibility + time composite index
CREATE INDEX idx_photos_visibility_taken_at 
ON photos(visibility, taken_at);

-- User + time index for authenticated queries
CREATE INDEX idx_photos_user_taken_at 
ON photos(user_id, taken_at);
```

### Query Optimization

**Aggregation query example:**
```sql
-- Years aggregation with visibility filtering
SELECT 
    EXTRACT(YEAR FROM taken_at) as year,
    COUNT(*) as count,
    MIN(taken_at) as first_date,
    MAX(taken_at) as last_date
FROM photos
WHERE 
    visibility = 'public' OR user_id = ?
GROUP BY year
ORDER BY year DESC;
```

### Caching Strategy

**Recommended caching:**
- Cache year/month aggregations for 1 hour
- Invalidate on photo upload/delete/visibility change
- Per-user cache for authenticated requests
- Global cache for anonymous requests

```python
@cache(key="timeline:years:{user_id}", expire=3600)
def get_timeline_years(user_id: Optional[int]):
    # Expensive aggregation cached for 1 hour
    pass
```

---

## Use Cases

### 1. Year Overview Grid

```typescript
// Frontend: Load all years
const response = await fetch('/api/v1/timeline?granularity=year');
const { data: years } = await response.json();

// Display grid of year cards
years.map(year => (
  <YearCard 
    year={year.year}
    count={year.count}
    preview={year.preview_url}
    onClick={() => expandYear(year.year)}
  />
))
```

### 2. Month Expansion

```typescript
// User clicks on 2024 year card
const expandYear = async (year: number) => {
  const response = await fetch(
    `/api/v1/timeline?granularity=month&year=${year}`
  );
  const { data: months } = await response.json();
  
  // Show months for 2024
  setExpandedMonths(months);
};
```

### 3. Lazy Loading Timeline

```typescript
// Infinite scroll timeline
const TimelineScroll = () => {
  const [years, setYears] = useState([]);
  const [expandedYears, setExpandedYears] = useState(new Set());
  
  // Load years on mount
  useEffect(() => {
    fetch('/api/v1/timeline?granularity=year')
      .then(r => r.json())
      .then(data => setYears(data.data));
  }, []);
  
  // Lazy load months when year expanded
  const onYearExpand = async (year: number) => {
    const response = await fetch(
      `/api/v1/timeline?granularity=month&year=${year}`
    );
    const { data: months } = await response.json();
    
    setExpandedYears(prev => new Set(prev).add(year));
    setMonthsCache(prev => ({ ...prev, [year]: months }));
  };
  
  return (
    <div>
      {years.map(year => (
        <YearSection
          key={year.year}
          {...year}
          expanded={expandedYears.has(year.year)}
          onExpand={() => onYearExpand(year.year)}
        />
      ))}
    </div>
  );
};
```

### 4. Public Gallery (Anonymous)

```typescript
// No authentication - shows only public photos
const PublicGallery = () => {
  const { data: years } = useFetch('/api/v1/timeline?granularity=year');
  
  return (
    <div className="public-gallery">
      <h1>Photo Gallery</h1>
      {years.map(year => (
        <YearGrid year={year} />
      ))}
      <LoginPrompt>Sign in to see more photos</LoginPrompt>
    </div>
  );
};
```

---

## Error Responses

### 400 Bad Request

Invalid query parameters:

```json
{
  "detail": "Invalid granularity. Must be one of: year, month, day, hour"
}
```

```json
{
  "detail": "Month parameter requires year parameter"
}
```

### 404 Not Found

No photos found for the specified period (all filtered out by visibility):

```json
{
  "data": [],
  "meta": {
    "total_years": 0,
    "total_photos": 0,
    "granularity": "year"
  }
}
```

**Note:** Empty results are **200 OK** with empty array, not 404.

---

## Future Enhancements

### Phase 2: Event Detection

Auto-detect "events" by clustering photos:

```json
GET /api/v1/timeline/events?year=2024

{
  "data": [
    {
      "event_id": "auto-001",
      "name": "Oslo Trip",  // Auto-generated or user-defined
      "count": 142,
      "date_range": {
        "start": "2024-07-15T08:00:00Z",
        "end": "2024-07-22T20:00:00Z"
      },
      "location": {
        "lat": 59.9139,
        "lon": 10.7522,
        "name": "Oslo, Norway"
      },
      "preview_hothash": "event123..."
    }
  ]
}
```

**Event clustering rules:**
- Time gap > 8 hours = new event
- Distance gap > 50km = new event  
- Same import session = same event

### Phase 3: Smart Buckets

Adaptive bucket sizes based on photo density:

```json
{
  "data": [
    {
      "bucket_type": "month",
      "period": "2024-12",
      "count": 500,
      "reason": "high_density"
    },
    {
      "bucket_type": "day",
      "period": "2024-11-15",
      "count": 200,
      "reason": "single_event"
    },
    {
      "bucket_type": "quarter",
      "period": "2024-Q1",
      "count": 10,
      "reason": "low_density"
    }
  ]
}
```

### Phase 4: Materialized Views

For extreme performance with millions of photos:

```sql
CREATE MATERIALIZED VIEW timeline_cache AS
SELECT 
    EXTRACT(YEAR FROM taken_at) as year,
    EXTRACT(MONTH FROM taken_at) as month,
    visibility,
    user_id,
    COUNT(*) as count,
    MIN(taken_at) as first_date,
    MAX(taken_at) as last_date
FROM photos
GROUP BY year, month, visibility, user_id;

-- Refresh periodically or on photo changes
REFRESH MATERIALIZED VIEW timeline_cache;
```

---

## Related APIs

- **[Photos API](./API_REFERENCE.md#-photos)** - Retrieve individual photos
- **[Visibility System](./FRONTEND_VISIBILITY_IMPLEMENTATION.md)** - Access control details
- **[Search API](./API_REFERENCE.md#-search)** - Advanced photo filtering

---

## References

**Inspired by:**
- [Immich](https://github.com/immich-app/immich) - Timeline buckets API
- [PhotoPrism](https://github.com/photoprism/photoprism) - Moments feature
- Apple Photos - Years/Months/Days navigation
- Google Photos - Timeline clustering

**Implementation guides:**
- [Immich Timeline Service](https://github.com/immich-app/immich/blob/main/server/src/domain/timeline/timeline.service.ts)
- [PostgreSQL Date/Time Functions](https://www.postgresql.org/docs/current/functions-datetime.html)
- [SQLAlchemy Date Aggregation](https://docs.sqlalchemy.org/en/14/core/functions.html#sqlalchemy.sql.functions.func.extract)

---

**Next Steps:**
1. Review this design document
2. Implement `TimelineRepository` with aggregation queries
3. Create `TimelineService` with visibility filtering
4. Add `/api/v1/timeline` endpoint
5. Write comprehensive tests
6. Add database indexes
7. Implement caching layer
8. Update `API_REFERENCE.md` with timeline endpoints
