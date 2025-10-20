# Konsistent Duplikatsjekking - Implementasjonsguide

## 📋 Oversikt

Dette dokumentet beskriver hvordan konsistent duplikatsjekking skal implementeres i ImaLink systemet. Løsningen sikrer at samme bilde alltid får samme `hothash` uavhengig av når det importeres eller hvilken frontend som brukes.

## 🎯 Målsettinger

- **Konsistent duplikatdeteksjon**: Samme bilde skal alltid få samme `hothash`
- **Frontend-agnostisk**: Nye frontends kan følge standardiserte spesifikasjoner
- **Testbar synkronisering**: Validering av frontend-backend konsistens
- **Feilsikret**: Fallback-mekanismer ved backend-utilgjengelighet

## 🏗️ Arkitektur

### Backend-autoritet for hash-generering

Backend er den autoritative kilden for `hothash`-generering. Dette sikrer konsistens på tvers av alle frontends og importsesjoner.

```
Frontend (metadata) → Backend (hash-generering) → Konsistent hothash
```

### Deterministisk hash-algoritme

```typescript
function generateHash(filename: string, fileSize: number, width?: number, height?: number): string {
  // 1. Normaliser filnavn
  const normalizedFilename = normalizeFilename(filename);
  
  // 2. Bygg hash-input
  const hashInput = [normalizedFilename, fileSize.toString()];
  if (width && height) {
    hashInput.push(width.toString(), height.toString());
  }
  
  // 3. Generer MD5 hash
  const combined = hashInput.join('|');
  return MD5(combined).substring(0, 32);
}
```

## 📡 API Endepunkter

### 1. Pilot Hash Testing

```http
GET /api/v1/test/pilot-hash
```

Returnerer hardkodet pilot-data for testing av konsistens:

```json
{
  "pilot_image": {
    "filename": "pilot_test.jpg",
    "width": 1920,
    "height": 1080,
    "file_size": 2458762,
    "expected_hothash": "pilot_test_consistent_hash_v1"
  },
  "hotpreview_spec": {
    "width": 300,
    "height": 300,
    "format": "JPEG",
    "quality": 85,
    "crop": "center",
    "color_space": "sRGB"
  },
  "hash_algorithm": "deterministic_content_based",
  "version": "v1"
}
```

### 2. Hash Generering

```http
POST /api/v1/test/generate-hash?filename=test.jpg&file_size=1000000&width=1920&height=1080
```

Genererer konsistent hash fra metadata:

```json
{
  "hothash": "a1b2c3d4e5f6789012345678901234567",
  "algorithm": "deterministic_metadata_based_v1",
  "input": {
    "filename": "test.jpg",
    "file_size": 1000000,
    "width": 1920,
    "height": 1080
  }
}
```

### 3. Frontend Validering

```http
POST /api/v1/test/validate-frontend
Content-Type: application/json

{
  "filename": "test.jpg",
  "file_size": 1000000,
  "width": 1920,
  "height": 1080,
  "frontend_hash": "a1b2c3d4e5f6789012345678901234567"
}
```

Validerer at frontend genererer samme hash som backend:

```json
{
  "valid": true,
  "frontend_hash": "a1b2c3d4e5f6789012345678901234567",
  "backend_hash": "a1b2c3d4e5f6789012345678901234567",
  "message": "Hash validation successful",
  "algorithm_version": "v1"
}
```

## 🖼️ Hotpreview Spesifikasjon

Alle frontends må følge samme hotpreview-spesifikasjon for konsistens:

```typescript
const HOTPREVIEW_SPEC = {
  width: 300,
  height: 300,
  format: 'JPEG',
  quality: 85,
  crop: 'center',        // Center crop for aspect ratio mismatch
  colorSpace: 'sRGB'     // Standard color space
} as const;
```

### Implementering

```typescript
export async function generateHotpreview(file: File): Promise<string | null> {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const img = new Image();
  
  return new Promise((resolve) => {
    img.onload = () => {
      // Sett canvas størrelse i henhold til spec
      canvas.width = HOTPREVIEW_SPEC.width;
      canvas.height = HOTPREVIEW_SPEC.height;
      
      // Beregn crop-dimensjoner (center crop)
      const sourceAspect = img.width / img.height;
      const targetAspect = HOTPREVIEW_SPEC.width / HOTPREVIEW_SPEC.height;
      
      let sourceX = 0, sourceY = 0, sourceWidth = img.width, sourceHeight = img.height;
      
      if (sourceAspect > targetAspect) {
        // Kilde er bredere - crop horisontalt
        sourceWidth = img.height * targetAspect;
        sourceX = (img.width - sourceWidth) / 2;
      } else {
        // Kilde er høyere - crop vertikalt
        sourceHeight = img.width / targetAspect;
        sourceY = (img.height - sourceHeight) / 2;
      }
      
      // Tegn croppet og skalert bilde
      ctx?.drawImage(
        img,
        sourceX, sourceY, sourceWidth, sourceHeight,
        0, 0, HOTPREVIEW_SPEC.width, HOTPREVIEW_SPEC.height
      );
      
      // Konverter til base64 med spesifisert kvalitet
      const dataUrl = canvas.toDataURL('image/jpeg', HOTPREVIEW_SPEC.quality / 100);
      const base64 = dataUrl.split(',')[1];
      resolve(base64);
    };
    
    img.onerror = () => resolve(null);
    img.src = URL.createObjectURL(file);
  });
}
```

## 🔄 Frontend Implementering

### 1. Hash Service

```typescript
// src/lib/services/hash-generation.service.ts

export async function generateConsistentHash(
  filename: string,
  fileSize: number,
  width?: number,
  height?: number
): Promise<string> {
  try {
    const params = new URLSearchParams({
      filename,
      file_size: fileSize.toString(),
      ...(width && { width: width.toString() }),
      ...(height && { height: height.toString() })
    });
    
    const response = await fetch(`/api/v1/test/generate-hash?${params}`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error(`Hash generation failed: ${response.status}`);
    }
    
    const result = await response.json();
    return result.hothash;
  } catch (error) {
    console.error('Failed to generate consistent hash:', error);
    // Fallback til lokal hash hvis backend er utilgjengelig
    return generateFallbackHash(filename, fileSize, width, height);
  }
}
```

### 2. Batch Import Oppdatering

```typescript
// I import-logikken
for (const photo of photos) {
  // Generer konsistent hash via backend
  const hothash = await generateConsistentHash(
    primaryFile.filename,
    primaryFile.size,
    photo.width,
    photo.height
  );
  
  // Bruk hashen i batch-requesten
  const photoGroup = {
    hothash,
    hotpreview: await generateHotpreview(primaryFile),
    width: photo.width,
    height: photo.height,
    // ... resten av dataene
  };
}
```

## 🧪 Testing og Validering

### Automatisk Frontend-validering

```typescript
export async function validateFrontendSync(): Promise<boolean> {
  try {
    // 1. Hent pilot-data fra backend
    const pilotResponse = await fetch('/api/v1/test/pilot-hash');
    const pilotData = await pilotResponse.json();
    const pilot = pilotData.pilot_image;
    
    // 2. Generer hash med vår funksjon
    const frontendHash = await generateConsistentHash(
      pilot.filename,
      pilot.file_size,
      pilot.width,
      pilot.height
    );
    
    // 3. Valider med backend
    const validateResponse = await fetch('/api/v1/test/validate-frontend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: pilot.filename,
        file_size: pilot.file_size,
        width: pilot.width,
        height: pilot.height,
        frontend_hash: frontendHash
      })
    });
    
    const validation = await validateResponse.json();
    return validation.valid;
  } catch (error) {
    console.error('Frontend sync validation failed:', error);
    return false;
  }
}
```

### Manual Testing

Test-script for browser console (`frontend/hash-test.js`):

```javascript
// Test konsistens og validering
async function testHashGeneration() {
  const testData = {
    filename: 'test_image.jpg',
    file_size: 2458762,
    width: 1920,
    height: 1080
  };
  
  // Generer hash to ganger - skal være identisk
  const hash1 = await generateHash(testData);
  const hash2 = await generateHash(testData);
  
  console.log('Hash consistency:', hash1 === hash2);
  console.log('Hash:', hash1);
}
```

## 🚀 Implementeringssteg

### 1. Backend Setup

1. **Implementer test-endepunkter** (`src/api/v1/test.py`)
2. **Registrer ruter** i `main.py`
3. **Oppdater PhotoService** med konsistent hash-generering
4. **Test endepunkter** med curl/Postman

### 2. Frontend Integration

1. **Opprett hash service** (`src/lib/services/hash-generation.service.ts`)
2. **Oppdater import-logikk** til å bruke backend-hash
3. **Implementer hotpreview-generering** i henhold til spec
4. **Legg til validering** i app-oppstart

### 3. Testing

1. **Kjør backend-tester** for hash-konsistens
2. **Test frontend-validering** via browser console
3. **Kjør ende-til-ende import-test** med duplikater
4. **Verifiser cross-browser kompatibilitet**

## 🔧 Troubleshooting

### Hash Inkonsistens

**Problem**: Forskjellige hashes for samme bilde
**Løsning**: 
- Sjekk filnavn-normalisering
- Verifiser metadata-ekstrahering
- Test med pilot-data

### Frontend Sync Feil

**Problem**: Frontend validering feiler
**Løsning**:
- Kjør `validateFrontendSync()` for detaljert feilinfo
- Sammenlign hash-algoritmer
- Sjekk API-endepunkt tilgjengelighet

### Performance Issues

**Problem**: Slow hash-generering
**Løsning**:
- Implementer caching av hashes
- Batch hash-genereringer
- Bruk fallback ved timeout

## 📚 Referanser

- **Backend Implementation**: `src/api/v1/test.py`
- **Frontend Service**: `src/lib/services/hash-generation.service.ts`
- **Test Script**: `frontend/hash-test.js`
- **Batch Import**: `src/routes/import/+page.svelte`

## 🔄 Versjonering

- **v1**: Inicial implementering med MD5-basert hash
- **v2** (planlagt): Perceptual hashing for bedre duplikatdeteksjon
- **v3** (planlagt): GPU-akselerert hash-generering

---

*Sist oppdatert: Oktober 2025*