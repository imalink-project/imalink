# Database Statistics Endpoint

## Overview
Endepunkt for å få oversikt over databasestørrelse og lagring.

## Endpoint
```
GET /api/v1/database-stats
```

## Authentication
❌ **Ingen autentisering påkrevd** - Dette endepunktet er ment for systemovervåkning og kan kalles uten innlogging.

## Response Schema

### DatabaseStatsResponse
```json
{
  "tables": {
    "table_name": {
      "name": "string",
      "record_count": 0,
      "size_bytes": 0,
      "size_mb": 0.0
    }
  },
  "coldstorage": {
    "path": "string",
    "total_files": 0,
    "total_size_bytes": 0,
    "total_size_mb": 0.0,
    "total_size_gb": 0.0
  },
  "database_file": "string",
  "database_size_bytes": 0,
  "database_size_mb": 0.0
}
```

## Example Response
```json
{
  "tables": {
    "photos": {
      "name": "photos",
      "record_count": 45,
      "size_bytes": 4612096,
      "size_mb": 4.4
    },
    "image_files": {
      "name": "image_files",
      "record_count": 45,
      "size_bytes": 92160,
      "size_mb": 0.09
    },
    "users": {
      "name": "users",
      "record_count": 2,
      "size_bytes": 8192,
      "size_mb": 0.01
    }
  },
  "coldstorage": {
    "path": "/mnt/c/temp/00imalink_data/coldpreviews",
    "total_files": 45,
    "total_size_bytes": 6656400,
    "total_size_mb": 6.35,
    "total_size_gb": 0.01
  },
  "database_file": "/mnt/c/temp/00imalink_data/imalink.db",
  "database_size_bytes": 8392704,
  "database_size_mb": 8.0
}
```

## Usage

### cURL
```bash
curl http://localhost:8000/api/v1/database-stats
```

### Python
```python
import requests

response = requests.get("http://localhost:8000/api/v1/database-stats")
stats = response.json()

print(f"Total photos: {stats['tables']['photos']['record_count']}")
print(f"Database size: {stats['database_size_mb']} MB")
print(f"Coldstorage size: {stats['coldstorage']['total_size_gb']} GB")
```

### Qt/C++
```cpp
QNetworkRequest request(QUrl("http://localhost:8000/api/v1/database-stats"));
QNetworkReply *reply = networkManager->get(request);
```

## Use Cases
- System monitoring dashboards
- Storage space alerts
- Database maintenance scheduling
- Performance analysis
- Capacity planning

## Notes
- **Table sizes** are approximate for SQLite (uses dbstat if available)
- **Coldstorage** includes all coldpreview files (800-1200px JPEG previews)
- **No authentication** - suitable for monitoring tools and system health checks
- Safe to call frequently - read-only operation with minimal overhead
