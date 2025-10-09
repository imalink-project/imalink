# Frontend Default Configuration Values

Dette dokumentet beskriver standardverdiene som skal brukes i frontend input-felter.

## Import/Storage Default Values

Disse verdiene brukes som placeholder/standardverdier i frontend input-felter og er **IKKE** hardkodet i backend:

### Import Directory Standards
- **Linux/WSL**: `/mnt/c/temp/PHOTOS_SRC_TEST_MINI`
- **Windows**: `C:\temp\PHOTOS_SRC_TEST_MINI`

### Storage Root Standards
- **Linux/WSL**: `/mnt/c/temp/storage`
- **Windows**: `C:\temp\storage`

### Test Storage (for development)
- **Linux/WSL**: `/tmp/imalink-test-storage`
- **Windows**: `%TEMP%\imalink-test-storage`

### Image Processing Standards
- **Pool Quality**: `85` (JPEG compression quality 1-100)
- **Thumbnail Size**: `200x200` (default thumbnail dimensions)

## Usage in Frontend

Disse verdiene skal:
1. **Brukes som placeholder-tekst** i input-felter
2. **Foreslås som standardverdier** til brukeren  
3. **IKKE hardkodes** - brukeren må alltid kunne overstyre dem
4. **Tilpasses OS** - frontend kan detektere OS og velge riktige path-formater

## Architecture Decision

**Backend** inneholder kun:
- Database configuration
- API keys og secrets
- Core system parameters

**Frontend** håndterer:
- User-spesifikke stier (import, storage)
- UI standardverdier og placehoders  
- Platform-spesifikke path handling

Dette sikrer at backend er platform-uavhengig og frontend kan tilpasse seg brukerens miljø.