# Timeline API Proposal

## Oversikt
Timeline API-et gir strukturert tilgang til bilder organisert etter tidsintervaller (år, måned, dag). Dette støtter effektiv navigasjon gjennom store bildekolleksjoner.

## API Endpoints

### 1. Get Timeline Years
```
GET /api/v1/timeline/years
```
**Respons:**
```json
{
  "years": [
    {
      "year": 2024,
      "photo_count": 245,
      "pilot_image": {
        "id": 123,
        "thumbnail_url": "/api/v1/image-files/123/thumbnail",
        "title": "IMG_20241015.jpg"
      },
      "month_count": 12,
      "date_range": {
        "first": "2024-01-05T08:30:00Z",
        "last": "2024-12-28T19:45:00Z"
      }
    }
  ]
}
```

### 2. Get Timeline Months for Year
```
GET /api/v1/timeline/years/{year}/months
```
**Respons:**
```json
{
  "year": 2024,
  "months": [
    {
      "month": 12,
      "name": "Desember",
      "photo_count": 45,
      "pilot_image": {
        "id": 456,
        "thumbnail_url": "/api/v1/image-files/456/thumbnail",
        "title": "IMG_20241215.jpg"
      },
      "day_count": 8,
      "date_range": {
        "first": "2024-12-01T12:00:00Z",
        "last": "2024-12-28T19:45:00Z"
      }
    }
  ]
}
```

### 3. Get Timeline Days for Month
```
GET /api/v1/timeline/years/{year}/months/{month}/days
```
**Respons:**
```json
{
  "year": 2024,
  "month": 12,
  "days": [
    {
      "day": 15,
      "photo_count": 12,
      "pilot_image": {
        "id": 789,
        "thumbnail_url": "/api/v1/image-files/789/thumbnail",
        "title": "IMG_20241215_143022.jpg"
      },
      "time_range": {
        "first": "2024-12-15T08:30:00Z",
        "last": "2024-12-15T20:15:00Z"
      }
    }
  ]
}
```

### 4. Get Photos for Specific Day
```
GET /api/v1/timeline/years/{year}/months/{month}/days/{day}/photos
```
**Query Parameters:**
- `offset`: Skip number of photos (default: 0)
- `limit`: Max photos to return (default: 100)
- `sort_by`: Sort field (default: "taken_at")
- `sort_order`: "asc" or "desc" (default: "asc")

**Respons:**
```json
{
  "date": "2024-12-15",
  "total": 12,
  "offset": 0,
  "limit": 100,
  "photos": [
    {
      "id": 789,
      "title": "IMG_20241215_143022.jpg",
      "taken_at": "2024-12-15T14:30:22Z",
      "thumbnail_url": "/api/v1/image-files/789/thumbnail",
      "full_url": "/api/v1/image-files/789/file",
      "author": {
        "id": 1,
        "name": "John Doe"
      },
      "location": "Oslo, Norway",
      "rating": 4
    }
  ]
}
```

## Timeline med Søk og Filtrering

### 5. Timeline Years med Søk
```
GET /api/v1/timeline/years?q=beach&author_id=1&has_gps=true
```
Samme respons som #1, men kun år som inneholder bilder som matcher søkekriteriene.

### 6. Timeline Months med Søk
```
GET /api/v1/timeline/years/{year}/months?q=beach&author_id=1
```

### 7. Timeline Days med Søk
```
GET /api/v1/timeline/years/{year}/months/{month}/days?q=beach&author_id=1
```

## Teknisk Implementering

### Database Optimaliseringer
- Indeks på `taken_at` feltet for rask dato-gruppering
- Materialiserte views for år/måned aggregeringer
- Caching av pilot-bilder per tidsperiode

### Pilot Image Logikk
1. **Kvalitet**: Høyest rating først
2. **Representativt**: Mest populær/typisk for perioden
3. **Fallback**: Første bilde kronologisk

### Performance Considerations
- Lazy loading av bilder
- Thumbnail pre-generering
- Response caching (Redis)
- Batch-operasjoner for store tidsperioder

## Frontend Integration

### Timeline Demo → Real API
```typescript
// Erstatt mock data med:
const response = await fetch('/api/timeline/years');
const data = await response.json();
setTimelineData(data.years);
```

### Søkeintegrasjon
```typescript
// Timeline med søk
const searchParams = new URLSearchParams({
  q: searchQuery,
  author_id: selectedAuthor?.toString(),
  has_gps: includeGPS?.toString()
});

const response = await fetch(`/api/timeline/years?${searchParams}`);
```

## Fremtidige Utvidelser
- **Zoom-nivåer**: Time-of-day (morgen/middag/kveld)
- **Hendelser**: Automatisk gruppering av bilder fra samme event
- **Steder**: Geografisk gruppering av bilder
- **Smart Albums**: AI-basert innholdskategorisering