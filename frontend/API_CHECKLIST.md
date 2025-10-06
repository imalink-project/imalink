# API Endpoint Checklist
## Sist oppdatert: 2025-10-05

### ✅ IMPLEMENTERT I api.js:
- [x] GET /health - `healthCheck()`
- [x] GET /api/v1/images/ - `getImages()`
- [x] GET /api/v1/images/{id} - `getImage(imageId)`
- [x] GET /api/v1/images/{id}/hotpreview - `getThumbnailUrl(imageId)` (URL helper)
- [x] GET /api/v1/images/{id}/pool/{size} - `getImageUrl(imageId)` (URL helper)
- [x] GET /api/v1/authors/ - `getAuthors()`
- [x] GET /api/v1/authors/{id} - `getAuthor(authorId)`
- [x] GET /api/v1/import_sessions/ - `getImportSessions()`
- [x] POST /api/v1/import_sessions/ - `createImportSession(sourcePath)`
- [x] GET /api/v1/import_sessions/status/{id} - `getImportSessionStatus(sessionId)`

### 🔄 NYLIG LAGT TIL:
- [x] GET /api/v1/images/search - `searchImages(query, offset, limit)`
- [x] GET /api/v1/images/statistics/overview - `getImageStatistics()`
- [x] GET /api/v1/images/recent - `getRecentImages(limit)`
- [x] POST /api/v1/images/{id}/rotate - `rotateImage(imageId, degrees)`
- [x] PUT /api/v1/images/{id} - `updateImage(imageId, updateData)`
- [x] DELETE /api/v1/images/{id} - `deleteImage(imageId)`
- [x] PUT /api/v1/authors/{id} - `updateAuthor(authorId, updateData)`
- [x] DELETE /api/v1/authors/{id} - `deleteAuthor(authorId)`
- [x] GET /api/v1/authors/search/ - `searchAuthors(query)`

### ✅ NYLIG IMPLEMENTERT (2025-10-05):
- [x] POST /api/v1/images/ - `createImage(imageFile, metadata)` (FormData file upload)
- [x] GET /api/v1/images/author/{author_id} - `getImagesByAuthor(authorId)`
- [x] POST /api/v1/authors/ - `createAuthor(authorData)`
- [x] GET /api/v1/authors/statistics/ - `getAuthorStatistics()`
- [x] GET /api/v1/authors/with-images/ - `getAuthorsWithImages()`
- [x] POST /api/v1/import_sessions/start - `startImportSession(sourcePath)`
- [x] POST /api/v1/import_sessions/test-single - `testSingleImage(imagePath)`
- [x] GET /api/v1/import_sessions/storage-info - `getStorageInfo()`
- [x] GET /api/v1/import_sessions/test - `testImportEndpoint()`

### 🎉 STATUS: FULLSTENDIG SYNKRONISERT!

### 🔧 WORKFLOW:
1. Gjør endringer i backend
2. Kjør: `Invoke-WebRequest -Uri "http://localhost:8000/debug/routes"`
3. Sammenlign med denne sjekklisten
4. Oppdater api.js med nye/endrede endepunkter
5. Oppdater denne sjekklisten
6. Test frontend integrasjon