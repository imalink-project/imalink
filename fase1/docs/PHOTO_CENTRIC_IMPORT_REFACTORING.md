# Photo-Centric Import Architecture Refactoring

**Dato:** 6. oktober 2025  
**Status:** Design dokument - Klar for implementasjon  
**Mål:** Klarere ansvarsfordeling mellom ImportSession, Photo og Image modeller

## Oversikt

Denne refaktoriseringen flytter content-generering logikk fra ImportSession til Photo modellen, som gir klarere separasjon av ansvar og bedre testbarhet.

## Nåværende arkitektur (Problemer)

### Import-prosessen i dag:
```
ImportSession → Skanner filer individuelt → Prosesserer hver fil → Lager Image records
                            ↓
                Exif/hotpreview/hothash logikk spredt i import-koden
                Mixed ansvar: fil-skanning + content-analyse
```

### Problemer:
- **Blandet ansvar**: ImportSession håndterer både fil-skanning og metadata-generering
- **Spredt logikk**: EXIF/hotpreview kode spredt i import-servicen
- **Vanskelig testing**: Kan ikke teste metadata-generering isolert
- **RAW/JPEG kobling**: Kompleks logikk for å håndtere fil-par
- **Duplikatsjekk**: Skjer på fil-nivå i stedet for photo-nivå

## Foreslått arkitektur (Løsning)

### Ny import-prosess:
```
ImportSession → Skanner katalog → Grupperer RAW/JPEG par → Delegerer til Photo
                    ↓                      ↓
             Filskanning og           Photo.create_from_file_group()
             organisering                     ↓
                                   Analyserer og genererer alt content
                                   Sjekker duplikater på photo-nivå
                                   Oppretter Photo + Image records
```

## Ansvarsfordeling

### 1. ImportSession (Orkestrator)
**Ansvar:** Filskanning, gruppering, og prosess-styring

```python
class ImportSessionsBackgroundService:
    def process_directory_import(self, session_id: int) -> bool:
        """Main import workflow - now much cleaner!"""
        
        # 1. Skann katalog for bildefiler
        image_files = self._scan_directory_for_images(source_path)
        
        # 2. Grupper RAW/JPEG par
        file_groups = self._group_raw_jpeg_pairs(image_files)
        
        # 3. Behandle hver gruppe via Photo
        for group in file_groups:
            try:
                # Photo håndterer all content-logikk
                photo = Photo.create_from_file_group(group, session_id)
                self._handle_successful_import(photo)
                
            except DuplicatePhotoError:
                self._handle_duplicate_photo(group)
            except PhotoCreationError as e:
                self._handle_photo_error(group, e)
        
        return True
    
    def _scan_directory_for_images(self, path: str) -> List[Path]:
        """Rekursivt skann for alle bildefiler"""
        
    def _group_raw_jpeg_pairs(self, files: List[Path]) -> List[List[Path]]:
        """
        Grupper filer i RAW/JPEG par basert på filnavn.
        
        Input: ["IMG_1234.jpg", "IMG_1234.CR2", "IMG_5678.jpg"]
        Output: [["IMG_1234.jpg", "IMG_1234.CR2"], ["IMG_5678.jpg"]]
        
        Forutsetter: Ingen navnekollisjoner (ytterst sjelden)
        """
```

### 2. Photo (Content Creator)
**Ansvar:** Content-analyse, metadata-generering, duplikatsjekk

```python
class Photo(Base, TimestampMixin):
    """Primary photo model with smart content creation"""
    
    @classmethod
    def create_from_file_group(cls, file_group: List[Path], import_session_id: int) -> 'Photo':
        """
        Smart constructor - hovedinngangen for Photo-opprettelse.
        Håndterer all content-analyse og generering.
        
        Args:
            file_group: Liste med filer som tilhører samme foto (1-2 filer)
            import_session_id: Referanse til import session
            
        Returns:
            Ferdig Photo med tilknyttede Image records
            
        Raises:
            DuplicatePhotoError: Hvis foto allerede eksisterer
            PhotoCreationError: Ved feil i prosessering
        """
        
        # 1. Analyser filgruppe og velg primær fil
        primary_file = cls._choose_primary_file(file_group)
        
        # 2. Generer content-basert hash (blir primary key)
        hothash = cls._generate_content_hash(primary_file)
        
        # 3. Duplikatsjekk på photo-nivå
        if cls._exists_by_hash(hothash):
            raise DuplicatePhotoError(f"Photo exists: {hothash}")
        
        # 4. Ekstraher metadata fra primær fil
        metadata = cls._extract_photo_metadata(primary_file)
        
        # 5. Generer hotpreview for galleries
        hotpreview = cls._generate_hotpreview(primary_file)
        
        # 6. Opprett Photo record
        photo = cls(
            hothash=hothash,
            hotpreview=hotpreview,
            width=metadata.width,
            height=metadata.height,
            taken_at=metadata.taken_at,
            gps_latitude=metadata.gps_latitude,
            gps_longitude=metadata.gps_longitude,
            import_session_id=import_session_id
        )
        
        # 7. Opprett Image records for alle filer i gruppen
        for file_path in file_group:
            image = Image.create_from_file(file_path, hothash, import_session_id)
            photo.files.append(image)
        
        # 8. Lagre til database (transaction håndteres av service layer)
        return photo
    
    @staticmethod
    def _choose_primary_file(files: List[Path]) -> Path:
        """
        Velg beste fil for metadata-ekstrahering.
        Prioritering: JPEG > RAW (JPEG er enklere å prosessere)
        """
        jpeg_files = [f for f in files if f.suffix.lower() in ['.jpg', '.jpeg']]
        return jpeg_files[0] if jpeg_files else files[0]
    
    @staticmethod
    def _generate_content_hash(file_path: Path) -> str:
        """
        Generer perceptual hash av bildeinnhold.
        Dette blir Photo sin primary key og deles mellom RAW/JPEG.
        
        Implementasjon: Bruk ImageProcessor eller perceptual hashing library
        """
        pass
    
    @staticmethod
    def _extract_photo_metadata(file_path: Path) -> 'PhotoMetadata':
        """
        Ekstraher EXIF, GPS, dimensjoner fra bildefil.
        Returnerer strukturert metadata objekt.
        """
        pass
    
    @staticmethod
    def _generate_hotpreview(file_path: Path) -> bytes:
        """
        Generer optimalisert thumbnail for gallery-visning.
        Fast cached version for UI performance.
        """
        pass
    
    @classmethod
    def _exists_by_hash(cls, hothash: str) -> bool:
        """Sjekk om Photo allerede eksisterer med denne hashen"""
        pass
```

### 3. Image (File Handler)
**Ansvar:** Fil-spesifikk metadata og lagring

```python
class Image(Base, TimestampMixin):
    """Simple file-level representation"""
    
    @classmethod
    def create_from_file(cls, file_path: Path, photo_hash: str, import_session_id: int) -> 'Image':
        """
        Enkel constructor for fil-metadata.
        Fokuserer kun på fil-spesifikke egenskaper.
        """
        return cls(
            filename=file_path.name,
            file_size=file_path.stat().st_size,
            exif_data=cls._extract_raw_exif(file_path),  # Raw EXIF som binary blob
            photo_hash=photo_hash,
            import_session_id=import_session_id
        )
    
    @staticmethod
    def _extract_raw_exif(file_path: Path) -> Optional[bytes]:
        """Ekstraher rå EXIF data for avanserte brukere"""
        pass
```

## Tekniske detaljer

### Filgruppering-algoritme
```python
def _group_raw_jpeg_pairs(self, files: List[Path]) -> List[List[Path]]:
    """
    Grupperingslogikk for RAW/JPEG par:
    
    1. Identifiser filnavn uten extension (stem)
    2. Grupper filer med samme stem
    3. Håndter edge cases (kun RAW, kun JPEG)
    
    Eksempel:
    - Input: ["IMG_1234.jpg", "IMG_1234.CR2", "IMG_5678.DNG"]  
    - Output: [["IMG_1234.jpg", "IMG_1234.CR2"], ["IMG_5678.DNG"]]
    """
    groups = {}
    for file in files:
        stem = file.stem  # Filnavn uten extension
        if stem not in groups:
            groups[stem] = []
        groups[stem].append(file)
    
    return list(groups.values())
```

### Duplikatsjekk-strategi
```python
# Før: Duplikatsjekk per fil (suboptimalt)
if image_repo.exists_by_hash(file_hash):
    skip_file()

# Etter: Duplikatsjekk per photo (riktig nivå)  
if Photo._exists_by_hash(content_hash):
    raise DuplicatePhotoError()
```

### Feilhåndtering
```python
# ImportSession håndterer Photo-level feil:
try:
    photo = Photo.create_from_file_group(group, session_id)
except DuplicatePhotoError:
    # Inkremente duplicates_skipped telleren
    self.import_repo.increment_duplicates_skipped(session_id)
except PhotoCreationError as e:
    # Logg spesifikk feil og fortsett med neste gruppe
    self.import_repo.increment_errors_count(session_id)
    self._log_photo_error(group, e)
```

## Implementasjonsplan

### Fase 1: Photo factory methods
1. ✅ Opprett `Photo.create_from_file_group()` metode
2. ✅ Implementer `_choose_primary_file()` logikk  
3. ✅ Implementer `_group_raw_jpeg_pairs()` i ImportSession

### Fase 2: Content generering
1. ✅ Implementer `_generate_content_hash()` 
2. ✅ Implementer `_extract_photo_metadata()`
3. ✅ Implementer `_generate_hotpreview()`

### Fase 3: Integration 
1. ✅ Refaktorer ImportSessionsBackgroundService
2. ✅ Oppdater Image.create_from_file()
3. ✅ Oppdater feilhåndtering

### Fase 4: Testing
1. ✅ Unit tests for Photo.create_from_file_group()
2. ✅ Integration tests for fil-gruppering
3. ✅ End-to-end import tests

## Fordeler ved ny arkitektur

### For utviklere:
- **🎯 Intuitiv:** `Photo.create_from_file_group()` er selvforklarende
- **🔍 Debugbar:** Enkel å spore hvor metadata-logikk ligger
- **📝 Maintainable:** EXIF/hotpreview kode samlet på ett sted
- **🧪 Testbar:** Hver komponent kan testes isolert

### For systemet:
- **⚡ Performance:** Duplikatsjekk på riktig nivå (photo vs fil)
- **🔄 Gjenbruk:** Photo creation kan brukes utenom import
- **🛡️ Robust:** Bedre feilhåndtering per foto-gruppe  
- **📊 Accurate:** Statistikk på photo-nivå i stedet for fil-nivå

### For brukere:
- **🖼️ Konsistent:** RAW/JPEG behandles som samme foto
- **⚡ Rask:** Hotpreview generering optimalisert
- **📍 Nøyaktig:** Metadata ekstrahert fra beste tilgjengelige fil

## Risiko og mitigering

### Potensielle problemer:
1. **Navnekollisjoner:** RAW og JPEG med samme navn i forskjellige mapper
   - **Mitigering:** Sjelden problem, kan håndteres med path-aware gruppering
   
2. **Performance:** Metadata-generering kan være treg
   - **Mitigering:** Asynkron prosessering, progress tracking
   
3. **Rollback kompleksitet:** Hvis Photo creation feiler midt i prosessen  
   - **Mitigering:** Database transactions, atomiske operasjoner

### Testing strategi:
- Mock `Path` objekter for unit testing
- Test fil-gruppering med ulike scenarier
- Performance testing med store kataloger
- Error injection testing

## Konklusjon

Denne refaktoriseringen gir en mye renere og mer modulær arkitektur hvor hver komponent har klart definerte ansvarsområder:

- **ImportSession**: Orkestrering og filskanning
- **Photo**: Content-analyse og metadata-generering  
- **Image**: Enkel fil-representasjon

Resultatet blir enklere vedlikehold, bedre testbarhet og klarere feilhåndtering.

---

**Neste steg:** Implementer Fase 1 - Photo factory methods