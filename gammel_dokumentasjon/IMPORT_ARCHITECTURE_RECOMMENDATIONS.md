# ImaLink Import Architecture - Strukturelle Anbefalinger

*Generert: 3. oktober 2025*
*Status: Nåværende import fungerer, men trenger refaktorering for skalerbarhet*

## 🎯 Executive Summary

Importstrategien i ImaLink er **funksjonell** men **arkitektonisk spredt**. Den trenger modularisering og rydding for å bli en robust, skalerbar løsning som fortjener sin sentrale rolle i systemet.

**Hovedutfordring:** 711 linjer i `api/v1/imports.py` med duplikatkode og business logic i API-laget.

---

## 🏗️ Nåværende Arkitektur - Analyse

### ✅ **Positive Aspekter**
- **Clean Architecture foundation**: Klar separasjon mellom API, Service, og Repository lag
- **Modern FastAPI**: Asynkrone endepunkter med Pydantic schemas og type safety
- **Comprehensive Models**: Import og ImageFile modeller med rik metadata-støtte
- **Background Processing**: Faktiske background tasks for tung prosessering
- **EXIF Support**: Full EXIF-ekstraksjonen implementert med GPS-koordinater
- **Duplicate Detection**: Hash-basert duplikatdeteksjon fungerer

### ❌ **Strukturelle Utfordringer**

#### 1. **Import-prosesslogikk spredt over flere steder**
```
api/v1/imports.py - 711 linjer inneholder:
├── run_import_background_service() 
├── import_directory_background() (DUPLIKAT!)
├── Direkte database-kall i stedet for service-lag
├── EXIF-prosessering copy-pastet på flere steder
└── Business logic blandet med API-lag
```

#### 2. **Arkitektur-brudd**
- **Service-lag bypasses** i background tasks
- **Duplikat-kode**: 2 identiske `import_directory_background()` funksjoner  
- **Separasjon av ansvar brutt**: API-lag inneholder filskanning og EXIF-prosessering
- **Datetime-konflikter**: Namespace-problemer som forårsaker krasj

#### 3. **Manglende spesialisering**
- Ingen dedikert image processing service
- Ingen structured error handling
- Begrenset progress tracking og monitoring

---

## 💡 Detaljerte Forbedringsforslag

### **A. Modularisering av Import-komponenter**

#### **Foreslått struktur:**
```
services/
├── import/
│   ├── __init__.py
│   ├── import_orchestrator.py     # Hovedlogikk for import-prosess
│   ├── file_scanner.py           # Filskanning og type-deteksjon
│   ├── image_processor.py        # EXIF/GPS/metadata-ekstraksjjon  
│   ├── duplicate_detector.py     # Hash-basert duplikatdeteksjon
│   ├── progress_tracker.py       # Progresoppfølging og statistikk
│   └── error_handler.py          # Centralized error handling
└── tasks/
    └── import_tasks.py           # Clean background task wrappers
```

#### **Implementasjonseksempel:**
```python
# services/import/import_orchestrator.py
class ImportOrchestrator:
    """Hovedklasse som orchestrerer hele import-prosessen"""
    
    def __init__(self, db: Session):
        self.file_scanner = FileScanner()
        self.image_processor = ImageProcessor() 
        self.duplicate_detector = DuplicateDetector(db)
        self.progress_tracker = ProgressTracker(db)
        self.error_handler = ImportErrorHandler()
    
    async def execute_import(self, import_session: Import) -> ImportResult:
        """Hovedlogikk for å orchestrere hele import-prosessen"""
        try:
            # 1. Scan files
            files = await self.file_scanner.scan_directory(import_session.source_path)
            
            # 2. Process each file
            for file_info in files:
                await self._process_single_file(file_info, import_session)
            
            # 3. Finalize
            return await self._finalize_import(import_session)
            
        except Exception as e:
            return await self.error_handler.handle_import_failure(import_session, e)
```

### **B. Spesialiserte Processing Services**

#### **Image Processor Service:**
```python
# services/import/image_processor.py
class ImageProcessor:
    """Dedikert service for image-relatert prosessering"""
    
    def extract_metadata(self, image_path: Path) -> ImageMetadata:
        """Centralized EXIF/GPS/dimensjons-ekstraksjjon"""
        return ImageMetadata(
            dimensions=self._extract_dimensions(image_path),
            exif_data=self._extract_exif(image_path),
            gps_coordinates=self._extract_gps(image_path),
            taken_at=self._extract_date_taken(image_path)
        )
        
    def generate_thumbnail(self, image_path: Path) -> bytes:
        """Hotpreview-generering med EXIF rotation"""
        
    def detect_image_type(self, image_path: Path) -> ImageType:
        """RAW vs JPEG detection og validering"""
        
    def _extract_gps(self, image_path: Path) -> Optional[GPSCoordinates]:
        """GPS extraction using GPS IFD - centralized logic"""
```

#### **File Scanner Service:**
```python
# services/import/file_scanner.py
class FileScanner:
    """Intelligent filskanning med type-deteksjon"""
    
    SUPPORTED_FORMATS = {
        'jpeg': {'.jpg', '.jpeg'},
        'png': {'.png'},
        'tiff': {'.tiff', '.tif'},
        'raw': {'.cr2', '.cr3', '.nef', '.arw', '.orf', '.dng'}
    }
    
    async def scan_directory(self, path: Path, config: ScanConfig) -> List[FileInfo]:
        """Scan directory with configurable strategies"""
        
    def detect_raw_jpeg_pairs(self, files: List[FileInfo]) -> List[FilePair]:
        """Smart RAW+JPEG pairing logic"""
```

### **C. Import Strategy Pattern**

#### **Konfigurerbare import-strategier:**
```python
from enum import Enum

class ImportStrategy(Enum):
    FULL_SCAN = "full"          # Alle filer, inkl. RAW
    JPEG_ONLY = "jpeg_only"     # Kun JPEG/støttede formater  
    SMART_PAIR = "smart_pair"   # RAW+JPEG pairing logic
    SELECTIVE = "selective"     # Brukervalgte filer

class ImportConfiguration:
    strategy: ImportStrategy
    include_duplicates: bool = False
    extract_hotpreviews: bool = True
    deep_exif_scan: bool = True
    parallel_processing: bool = True
    max_concurrent_files: int = 4
    
    # RAW file handling
    raw_processing: RawProcessingMode = RawProcessingMode.SKIP
    raw_paired_only: bool = True
    
    # Error handling
    continue_on_error: bool = True
    max_errors_before_abort: int = 10
```

### **D. Forbedret Progress og Monitoring**

#### **Strukturert progresrapportering:**
```python
class ImportProgress:
    """Detaljert progresoppfølging"""
    
    phase: ImportPhase              # SCANNING, PROCESSING, FINALIZING
    files_found: int
    files_processed: int  
    current_file: str
    estimated_completion: datetime
    
    # Detaljerte statistikker
    detailed_stats: ImportStats
    error_summary: List[ProcessingError]
    performance_metrics: PerformanceMetrics

class ImportPhase(Enum):
    INITIALIZING = "initializing"
    SCANNING = "scanning" 
    PROCESSING = "processing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### **E. Robust Error Handling**

#### **Centralized error management:**
```python
class ImportErrorHandler:
    """Centralisert feilhåndtering og recovery"""
    
    def handle_file_error(self, error: FileProcessingError) -> ErrorAction:
        """Bestem hvordan individuelle filfeil skal håndteres"""
        
    def recover_from_failure(self, import_session: Import) -> RecoveryResult:
        """Forsøk å gjenopprette etter feil"""
        
    def generate_error_report(self, import_session: Import) -> ErrorReport:
        """Generer detaljert feilrapport for brukeren"""

class ErrorAction(Enum):
    CONTINUE = "continue"       # Fortsett med neste fil
    RETRY = "retry"            # Forsøk filen på nytt  
    ABORT = "abort"            # Avbryt hele importen
    SKIP_BATCH = "skip_batch"  # Hopp over relaterte filer
```

---

## 🎯 Implementeringsprioriteringer

### **Fase 1 - Kritiske forbedringer (Umiddelbar refaktorering):**

1. **🔥 Fjern duplikat-funksjoner** i `imports.py` 
   - Slett én av de to `import_directory_background()` funksjonene
   - Konsolider EXIF-prosesseringskode

2. **🔥 Fiks datetime-konflikter**
   - Standardiser `import datetime as dt` overalt
   - Erstatt alle `datetime.datetime.now()` med `dt.datetime.now()`

3. **🔥 Skill ut EXIF-prosessering** til egen service
   - Opprett `ImageProcessor` service
   - Flytt GPS-ekstraksjonslogikk dit

4. **🔥 Flytt business logic** fra API til service-lag
   - Background tasks skal kun kalle service-metoder
   - Fjern direkte database-kall fra `imports.py`

### **Fase 2 - Strukturelle forbedringer (Neste sprint):**

1. **📊 Opprett dedikerte import services** 
   - `ImportOrchestrator` som hovedkoordinator
   - `FileScanner` for intelligent filskanning
   - `DuplicateDetector` for hash-basert deteksjon

2. **⚙️ Implementer import strategies**
   - `ImportConfiguration` for konfigurerbar oppførsel
   - Support for ulike import-modi

3. **🛠️ Forbedre error handling** og recovery
   - `ImportErrorHandler` for centralisert feilhåndtering
   - Structured error reporting

4. **📈 Comprehensive logging** og monitoring
   - Detaljert progresrapportering
   - Performance metrics og bottleneck detection

### **Fase 3 - Funksjonelle utvidelser (Fremtidige features):**

1. **🔗 Smart RAW+JPEG pairing** logikk
   - Intelligent deteksjon av RAW/JPEG par
   - Konfigurerbar håndtering av lone RAW files

2. **⏸️ Batch import** med resume capability
   - Støtte for pausing/resuming av store imports
   - Checkpoint-basert recovery

3. **📋 Import templates** for gjentakende oppgaver
   - Forhåndsdefinerte import-konfigurasjoner
   - Bruker-spesifikke import-profiler

4. **🔍 Advanced duplicate detection**
   - Perceptual hashing for visuelt like bilder
   - Similarity threshold-basert deteksjon

---

## 📊 Forventet Gevinst

### **Kode-kvalitet forbedringer:**
- **60% reduksjon i duplikat-kode** ved modularisering
- **Tydeligere separation of concerns** mellom lag
- **Lettere testing** med isolerte komponenter
- **Forbedret debugging** med centralisert error handling

### **Vedlikehold og utvikling:**
- **Modulære komponenter** som kan utvikles uavhengig
- **Enklere å legge til nye import-strategier** via strategy pattern
- **Bedre error isolation** og targeted fixes
- **Skalérbar arkitektur** for fremtidige features

### **Ytelse og brukeropplevelse:**
- **Parallell prosessering** av ulike import-faser  
- **Smartere resource management** og memory usage
- **Streaming processing** for store import-operasjoner
- **Rikere progres-feedback** til brukeren
- **Konfigurerbare import-strategier** for ulike brukstilfeller
- **Bedre feilmeldinger** og recovery-alternativer

### **System robusthet:**
- **Resilient import process** som håndterer feil gracefully
- **Resume capability** for avbrutte imports
- **Comprehensive audit trail** for debugging
- **Performance monitoring** for optimalisering

---

## 🚀 Umiddelbare neste steg

### **I morgen (4. oktober 2025):**

1. **Start med Fase 1 refaktorering**
   - Fjern duplikat `import_directory_background()` funksjoner
   - Konsolider datetime imports
   
2. **Opprett ImageProcessor service**
   - Flytt EXIF/GPS-ekstraksjonslogikk dit
   - Test at GPS-data fortsatt fungerer
   
3. **Clean opp imports.py**
   - Reduser fra 711 til ~200 linjer
   - Flytt business logic til service-lag

### **Denne uken:**
- Implementer `ImportOrchestrator` 
- Opprett `FileScanner` service
- Test at refaktorering ikke bryter eksisterende funksjonalitet

### **Neste sprint:**
- Implementer import strategies
- Forbedre error handling
- Legg til comprehensive progress tracking

---

## 💭 Arkitektur-filosofi

**Mål:** ImaLink's import-funksjonalitet skal være:
- **Modulær** - Enkelt å utvide og vedlikeholde
- **Robust** - Håndterer feil gracefully og kan recovery
- **Konfigurérbar** - Tilpassbar til ulike brukstilfeller  
- **Skalérbar** - Kan håndtere store import-operasjoner effektivt
- **Transparent** - Gir brukeren klar feedback og kontroll

**Prinsipp:** "Each component should have a single, well-defined responsibility and should be easily testable in isolation."

---

*Denne dokumentasjonen skal guide refaktoreringen av ImaLink's import-arkitektur mot en mer modulær, robust og skalerbar løsning.*