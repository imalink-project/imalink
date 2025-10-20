# Frontend Integration Guide v2.0# Frontend Integration Guide v2.0



## 🔐 Authentication Flow## 🔐 Authentication Flow



### 1. User Registration/Login### 1. User Registration/Login

```typescript```typescript

// Register new user// Register new user

const registerUser = async (userData: {const registerUser = async (userData: {

  username: string;  username: string;

  email: string;  email: string;

  password: string;  password: string;

  display_name: string;  display_name: string;

}) => {}) => {

  const response = await fetch('/api/v1/auth/register', {  const response = await fetch('/api/v1/auth/register', {

    method: 'POST',    method: 'POST',

    headers: { 'Content-Type': 'application/json' },    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify(userData)    body: JSON.stringify(userData)

  });  });

  return response.json();  return response.json();

};};



// Login user// Login user

const loginUser = async (credentials: {const loginUser = async (credentials: {

  username: string;  username: string;

  password: string;  password: string;

}) => {}) => {

  const response = await fetch('/api/v1/auth/login', {  const response = await fetch('/api/v1/auth/login', {

    method: 'POST',    method: 'POST',

    headers: { 'Content-Type': 'application/json' },    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify(credentials)    body: JSON.stringify(credentials)

  });  });

  const data = await response.json();  const data = await response.json();

    

  // Store token for future requests  // Store token for future requests

  localStorage.setItem('access_token', data.access_token);  localStorage.setItem('access_token', data.access_token);

  localStorage.setItem('user', JSON.stringify(data.user));  localStorage.setItem('user', JSON.stringify(data.user));

    

  return data;  return data;

};};

``````



### 2. Authenticated API Calls### 2. Authenticated API Calls

```typescript```typescript

// Helper to get auth headers// Helper to get auth headers

const getAuthHeaders = () => {const getAuthHeaders = () => {

  const token = localStorage.getItem('access_token');  const token = localStorage.getItem('access_token');

  return {  return {

    'Content-Type': 'application/json',    'Content-Type': 'application/json',

    'Authorization': `Bearer ${token}`    'Authorization': `Bearer ${token}`

  };  };

};};



// Example authenticated request// Example authenticated request

const fetchUserPhotos = async (offset = 0, limit = 50) => {const fetchUserPhotos = async (offset = 0, limit = 50) => {

  const response = await fetch(`/api/v1/photos?offset=${offset}&limit=${limit}`, {  const response = await fetch(`/api/v1/photos?offset=${offset}&limit=${limit}`, {

    headers: getAuthHeaders()    headers: getAuthHeaders()

  });  });

  return response.json();  return response.json();

};};

``````



## 🖼️ Image Upload - Two Clear Paths## 🖼️ Image Upload - Two Clear Paths



### Path 1: Upload New Photo### Path 1: Upload New Photo

For completely new, unique photos:For completely new, unique photos:



```typescript```typescript

const uploadNewPhoto = async (imageData: {const uploadNewPhoto = async (imageData: {

  file: File;  file: File;

  exifData?: any;  exifData?: any;

  takenAt?: Date;  takenAt?: Date;

  gpsLocation?: { latitude: number; longitude: number };  gpsLocation?: { latitude: number; longitude: number };

}) => {}) => {

  // 1. Generate hotpreview (thumbnail)  // 1. Generate hotpreview (thumbnail)

  const hotpreview = await generateHotpreview(imageData.file);  const hotpreview = await generateHotpreview(imageData.file);

    

  // 2. Prepare request  // 2. Prepare request

  const requestData = {  const requestData = {

    filename: imageData.file.name,    filename: imageData.file.name,

    hotpreview: hotpreview, // Base64 encoded    hotpreview: hotpreview, // Base64 encoded

    file_size: imageData.file.size,    file_size: imageData.file.size,

    exif_dict: imageData.exifData,    exif_dict: imageData.exifData,

    taken_at: imageData.takenAt?.toISOString(),    taken_at: imageData.takenAt?.toISOString(),

    gps_latitude: imageData.gpsLocation?.latitude,    gps_latitude: imageData.gpsLocation?.latitude,

    gps_longitude: imageData.gpsLocation?.longitude    gps_longitude: imageData.gpsLocation?.longitude

  };  };

    

  // 3. Upload  // 3. Upload

  const response = await fetch('/api/v1/image-files/new-photo', {  const response = await fetch('/api/v1/image-files/new-photo', {

    method: 'POST',    method: 'POST',

    headers: getAuthHeaders(),    headers: getAuthHeaders(),

    body: JSON.stringify(requestData)    body: JSON.stringify(requestData)

  });  });

    

  const result = await response.json();  const result = await response.json();

    

  if (result.photo_created) {  if (result.photo_created) {

    console.log(`New photo created: ${result.photo_hothash}`);    console.log(`New photo created: ${result.photo_hothash}`);

  }  }

    

  return result;  return result;

};};

``````



### Path 2: Add Companion File### Path 2: Add Companion File

For RAW/JPEG pairs or additional formats:For RAW/JPEG pairs or additional formats:



```typescript```typescript

const addCompanionFile = async (imageData: {const addCompanionFile = async (imageData: {

  file: File;  file: File;

  photoHothash: string;  photoHothash: string;

  exifData?: any;  exifData?: any;

}) => {}) => {

  const requestData = {  const requestData = {

    filename: imageData.file.name,    filename: imageData.file.name,

    photo_hothash: imageData.photoHothash,    photo_hothash: imageData.photoHothash,

    file_size: imageData.file.size,    file_size: imageData.file.size,

    exif_dict: imageData.exifData    exif_dict: imageData.exifData

    // Note: NO hotpreview needed - photo already exists    // Note: NO hotpreview needed - photo already exists

  };  };

    

  const response = await fetch('/api/v1/image-files/add-to-photo', {  const response = await fetch('/api/v1/image-files/add-to-photo', {

    method: 'POST',    method: 'POST',

    headers: getAuthHeaders(),    headers: getAuthHeaders(),

    body: JSON.stringify(requestData)    body: JSON.stringify(requestData)

  });  });

    

  const result = await response.json();  const result = await response.json();

    

  if (!result.photo_created) {  if (!result.photo_created) {

    console.log(`Added companion file to existing photo: ${result.photo_hothash}`);    console.log(`Added companion file to existing photo: ${result.photo_hothash}`);

  }  }

    

  return result;  return result;

};};

``````

  "gps_latitude": 60.3913,

## 🔧 Helper Functions  "gps_longitude": 5.3221,

  "taken_at": "2024-10-19T15:30:45.123Z",

### Generate Hotpreview  // ... alle andre feltene som før

```typescript}

const generateHotpreview = async (file: File): Promise<string> => {```

  return new Promise((resolve, reject) => {

    const canvas = document.createElement('canvas');**🔄 VIKTIG ENDRING - Oktober 20, 2025:**

    const ctx = canvas.getContext('2d');Frontend må nå sende strukturerte felter i tillegg til `exif_dict`:

    const img = new Image();

    ```typescript

    img.onload = () => {// POST /api/v1/image-files

      // Calculate dimensions (max 200px){

      const maxSize = 200;  "filename": "IMG_2024.jpg",

      let { width, height } = img;  "hotpreview": "data:image/jpeg;base64,/9j/4AAQ...",

        "exif_dict": { /* Komplett EXIF data */ },

      if (width > height) {  

        if (width > maxSize) {  // 🆕 PÅKREVD: Frontend må ekstrahere og sende disse:

          height = (height * maxSize) / width;  "taken_at": "2024-10-19T15:30:45.123Z",

          width = maxSize;  "gps_latitude": 60.3913,

        }  "gps_longitude": 5.3221

      } else {}

        if (height > maxSize) {```

          width = (width * maxSize) / height;

          height = maxSize;**Frontend ansvar:**

        }- ✅ **Ekstrahere taken_at** fra EXIF og sende som ISO 8601 string

      }- ✅ **Ekstrahere GPS koordinater** fra EXIF og sende som tall

      - ✅ **Sende komplett exif_dict** (som før) for visning

      canvas.width = width;- ✅ **Backend parser ikke lenger** EXIF for strukturerte felter

      canvas.height = height;

      **Backend-endring:** `exif_dict` kommer fra den første (master) ImageFile knyttet til Photo. For JPEG/RAW-par blir vanligvis JPEG sin EXIF data vist.

      // Draw and get base64

      ctx.drawImage(img, 0, 0, width, height);---

      const dataUrl = canvas.toDataURL('image/jpeg', 0.8);

      resolve(dataUrl);## 🔗 Referering til Felles Dokumentasjon

    };

    ### For Qt Frontend Repository

    img.onerror = reject;

    img.src = URL.createObjectURL(file);I ditt frontend repository, legg til følgende i README.md:

  });

};```markdown

```## 📚 Dokumentasjon



### Parse EXIF Data**Viktig**: All dokumentasjon ligger i hovedrepoet for å unngå duplikater.

```typescript

// Using exif-js library- **[API Reference](https://github.com/kjelkols/imalink/blob/main/docs/api/API_REFERENCE.md)** - REST API dokumentasjon

const parseExifData = async (file: File): Promise<any> => {- **[EXIF Extraction Guide](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_EXTRACTION_GUIDE.md)** - Detaljert EXIF implementasjonsguide (påkrevd)

  return new Promise((resolve, reject) => {- **[EXIF Specification](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_SPECIFICATION.md)** - EXIF JSON strukturspesifikasjon

    EXIF.getData(file, function() {- **[Qt Frontend Guide](https://github.com/kjelkols/imalink/blob/main/docs/frontend/QT_FRONTEND_GUIDE.md)** - Qt utviklingsguide  

      const exifData = EXIF.getAllTags(this);- **[Dokumentasjonsoversikt](https://github.com/kjelkols/imalink/blob/main/docs/README.md)** - Alle dokumenter

      

      // Convert relevant fields### Lokalt oppsett

      const processed = {For lokal utvikling, klon hovedrepoet for tilgang til dokumentasjon:

        DateTime: exifData.DateTime,\`\`\`bash

        Make: exifData.Make,git clone https://github.com/kjelkols/imalink.git

        Model: exifData.Model,# Dokumentasjon ligger i imalink/docs/

        Orientation: exifData.Orientation,\`\`\`

        GPS: {```

          latitude: exifData.GPSLatitude,

          longitude: exifData.GPSLongitude,### For andre Frontend Technologies (Web, Mobile, etc.)

          latitudeRef: exifData.GPSLatitudeRef,

          longitudeRef: exifData.GPSLongitudeRef```markdown

        }## 📚 Dokumentasjon

      };

      Dette frontend-prosjektet bruker ImaLink backend API.

      resolve(processed);

    });- **[API Reference](https://github.com/kjelkols/imalink/blob/main/docs/api/API_REFERENCE.md)** - REST API dokumentasjon

  });- **[EXIF Extraction Guide](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_EXTRACTION_GUIDE.md)** - Praktisk implementasjonsguide (påkrevd)

};- **[EXIF Specification](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_SPECIFICATION.md)** - JSON strukturspesifikasjon

```- **[Backend Repository](https://github.com/kjelkols/imalink)** - Hovedrepo med full dokumentasjon



## 📱 Smart Upload Logic### Backend Setup

For lokal utvikling:

### Determine Upload Strategy\`\`\`bash

```typescriptgit clone https://github.com/kjelkols/imalink.git

const smartUpload = async (files: File[]) => {cd imalink/fase1

  const results = [];uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  \`\`\`

  for (const file of files) {

    // 1. Parse EXIFAPI vil være tilgjengelig på: \`http://localhost:8000/api/v1\`

    const exifData = await parseExifData(file);```

    

    // 2. Generate hotpreview## 🔄 Synkronisering av Dokumentasjon

    const hotpreview = await generateHotpreview(file);

    ### Når du oppdaterer API-er

    // 3. Check if photo already exists (by comparing hotpreview hash)1. Oppdater dokumentasjon i hovedrepoet (`imalink/docs/`)

    const existingPhoto = await checkPhotoExists(hotpreview);2. Commit endringer

    3. Informer frontend teams om oppdateringer

    if (existingPhoto) {

      // Add as companion file### For Frontend Utviklere

      const result = await addCompanionFile({1. Bookmark dokumentasjons-linkene over

        file,2. Sjekk for oppdateringer i hovedrepoet regelmessig

        photoHothash: existingPhoto.hothash,3. Ikke dupliser dokumentasjon i frontend repos

        exifData

      });## 📋 Fordeler med denne tilnærmingen

      results.push({ type: 'companion', result });

    } else {- ✅ **Single Source of Truth**: All dokumentasjon ligger ett sted

      // Upload as new photo- ✅ **Konsistens**: Alle teams ser samme informasjon  

      const result = await uploadNewPhoto({- ✅ **Vedlikehold**: Kun ett sted å oppdatere dokumentasjon

        file,- ✅ **Versjonering**: Dokumentasjon følger backend-versjoner

        exifData,- ✅ **Historie**: Full commit-historie for dokumentasjonsendringer

        takenAt: parseDate(exifData.DateTime),

        gpsLocation: parseGPS(exifData.GPS)## 🔍 Alternativer

      });

      results.push({ type: 'new', result });Hvis du foretrekker andre løsninger:

    }

  }### 1. Git Submodules

  ```bash

  return results;# I frontend repo:

};git submodule add https://github.com/kjelkols/imalink.git docs-source

# Dokumentasjon tilgjengelig i docs-source/docs/

const checkPhotoExists = async (hotpreview: string): Promise<Photo | null> => {```

  // Generate hash from hotpreview and check if photo exists

  // This would require a new API endpoint or client-side comparison### 2. GitHub Pages

  // For now, let the backend handle duplicate detectionHvis hovedrepoet publiserer docs til GitHub Pages, kan du referere direkte til de publiserte sidene.

  return null;

};### 3. Package Distribution  

```Dokumentasjon kan pakkes som NPM package eller PyPI package for automatisk distribusjon.



## 🎯 Error Handling---



### Comprehensive Error Handling**Anbefaling**: Start med direkte GitHub-links (alternativ 1 over). Det er enkelt og effektivt for de fleste brukstilfeller.
```typescript
const handleUploadError = (error: any, filename: string) => {
  if (error.status === 401) {
    // Redirect to login
    window.location.href = '/login';
  } else if (error.status === 409) {
    // Photo already exists - suggest using add-to-photo
    console.warn(`Photo already exists for ${filename}. Consider using add-to-photo endpoint.`);
  } else if (error.status === 413) {
    // File too large
    console.error(`File ${filename} is too large`);
  } else {
    console.error(`Upload failed for ${filename}:`, error);
  }
};
```

## 🔒 Security Considerations

### Token Management
```typescript
// Check token expiration
const isTokenValid = (): boolean => {
  const token = localStorage.getItem('access_token');
  if (!token) return false;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp > Date.now() / 1000;
  } catch {
    return false;
  }
};

// Auto-refresh or logout on token expiration
const checkAuthStatus = () => {
  if (!isTokenValid()) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }
};
```

### Secure File Handling
```typescript
// Validate file types
const isValidImageFile = (file: File): boolean => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/tiff'];
  return allowedTypes.includes(file.type);
};

// Size limits
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const isValidFileSize = (file: File): boolean => {
  return file.size <= MAX_FILE_SIZE;
};
```

## 📊 Progress Tracking

### Upload Progress
```typescript
const uploadWithProgress = async (
  file: File, 
  onProgress: (percent: number) => void
) => {
  // For large files, implement chunked upload
  // For now, track basic progress
  
  onProgress(0);
  
  try {
    const result = await uploadNewPhoto({ file });
    onProgress(100);
    return result;
  } catch (error) {
    onProgress(0);
    throw error;
  }
};
```

This guide provides a complete frontend integration strategy for the new ImaLink authentication and upload architecture!