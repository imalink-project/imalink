# ImportSession Storage System - Arkitektur og Implementering

## 📋 Oversikt

ImportSession skal utvides til å bli et komplett arkiveringssystem som kopierer kildebilder til permanent storage og gjør systemet uavhengig av originalkilden. Dette sikrer at bilder aldri går tapt selv om originalkatalogen blir flyttet eller slettet.

## 🎯 Målsettinger

- **Permanent arkivering**: Kopier alle importerte bilder til dedikert storage
- **Kilde-uavhengighet**: Systemet skal aldri trenge tilgang til originalkatalog etter import
- **Sporbarhet**: Bevar informasjon om opprinnelig sti for historiske formål
- **Portable storage**: UUID-baserte kataloger som kan flyttes mellom disker
- **Feilsikker import**: Transaksjonell kopiering med rollback ved feil

## 🏗️ Arkitektur

### Storage Struktur

```
/storage-root/
├── 20241009_import_vacation_photos_abc12345/     # Datoveiledning + beskrivelse + UUID
│   ├── metadata.json                             # Session metadata
│   ├── files/                                    # Bildekatalog (samme struktur som kilde)
│   │   ├── subfolder1/
│   │   │   ├── IMG_001.jpg
│   │   │   └── IMG_001.raw
│   │   └── IMG_002.jpg
│   └── thumbnails/                               # Genererte thumbnails (valgfritt)
├── 20241008_import_wedding_photos_def67890/      # Annen ImportSession
│   └── ...
└── config.json                                  # Storage konfiguration
```

**Katalognavn Format**: `YYYYMMDD_import_<beskrivelse>_<uuid_8_tegn>`
- **Dato-prefix**: Gjør det enkelt å sortere og finne importer kronologisk
- **Beskrivelse**: Brukerdefinert eller standard (session, batch, etc.)
- **UUID-suffiks**: Garanterer unikhet og muliggjør universell søking

### Metadata Format

```json
{
  "import_session_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-10-09T10:30:00Z",
  "source_path": "/original/source/directory",
  "total_files": 1250,
  "total_size_bytes": 52428800000,
  "photos_created": 847,
  "duplicates_skipped": 203,
  "copy_status": "completed",
  "copy_completed_at": "2025-10-09T12:45:30Z",
  "file_manifest": [
    {
      "original_path": "subfolder1/IMG_001.jpg",
      "storage_path": "files/subfolder1/IMG_001.jpg", 
      "file_size": 2458762,
      "sha256": "abc123...",
      "copied_at": "2025-10-09T12:35:15Z"
    }
  ]
}
```

## 🗃️ Database Schema Utvidelser

### ImportSession Model

```python
class ImportSession(Base, TimestampMixin):
    # Eksisterende felter...
    
    # Nye storage-relaterte felter
    storage_uuid = Column(String(36), nullable=True, index=True)
    storage_directory_name = Column(String(255), nullable=True, index=True)  # Kun katalognavn, ikke full path
    copy_status = Column(String(20), default="not_started")  # not_started, in_progress, completed, failed
    copy_started_at = Column(DateTime, nullable=True)
    copy_completed_at = Column(DateTime, nullable=True)
    storage_size_mb = Column(Integer, default=0)
    
    # Historisk informasjon (kun for referanse)
    original_source_path = Column(Text, nullable=True)
    
    def generate_storage_directory_name(self, session_description: str = None) -> str:
        """Generate storage directory name with date prefix and UUID suffix"""
        import_date = (self.started_at or datetime.utcnow()).strftime("%Y%m%d")
        uuid_suffix = self.storage_uuid[:8] if self.storage_uuid else "unknown"
        
        if session_description:
            # Clean session description for filename safety
            safe_description = re.sub(r'[^\w\-_]', '_', session_description)[:50]
            return f"{import_date}_import_{safe_description}_{uuid_suffix}"
        else:
            return f"{import_date}_import_session_{uuid_suffix}"
    
    @property
    def has_permanent_storage(self) -> bool:
        """Check if this session has permanent storage configured"""
        return bool(self.storage_uuid and self.storage_directory_name)
    
    @property
    def is_storage_accessible(self) -> bool:
        """Sjekk om storage katalog finnes (må søke i storage_root)"""
        if not self.storage_directory_name:
            return False
        # Implementert i service layer med find_storage_directory()
        return True  # Placeholder - implementeres i StorageService
```

### Image Model Utvidelser

```python
class Image(Base, TimestampMixin):
    # Eksisterende felter...
    
    # Nye storage-felt
    storage_relative_path = Column(Text, nullable=True)  # Relativ sti innad i storage
    original_import_path = Column(Text, nullable=True)   # Opprinnelig sti (kun historisk)
    
    @property
    def storage_file_path(self) -> Optional[Path]:
        """Få full sti til lagret fil"""
        if self.import_session and self.storage_relative_path:
            storage_dir = self.import_session.storage_directory
            if storage_dir:
                return storage_dir / "files" / self.storage_relative_path
        return None
    
    @property
    def is_file_accessible(self) -> bool:
        """Sjekk om lagret fil er tilgjengelig"""
        file_path = self.storage_file_path
        return file_path and file_path.exists()
```

## 🔄 Import Workflow

### Fase 1: Scanning og Database (Eksisterende)

1. **Directory Scanning**: Scan kildekatalog for bildefiler
2. **EXIF Processing**: Ekstrakter metadata fra bildefiler  
3. **Photo Creation**: Opprett Photo og Image records i database
4. **Duplicate Detection**: Identifiser og håndter duplikater

### Fase 2: Storage Copy (Ny funksjonalitet)

5. **Storage Preparation**: 
   ```python
   storage_uuid = str(uuid.uuid4())
   storage_dir = storage_root / "import-sessions" / storage_uuid
   storage_dir.mkdir(parents=True, exist_ok=True)
   ```

6. **File Copying**:
   ```python
   for image in import_session.images:
       source_path = Path(image.original_import_path)
       relative_path = source_path.relative_to(import_session.original_source_path)
       target_path = storage_dir / "files" / relative_path
       
       # Opprett katalog og kopier fil
       target_path.parent.mkdir(parents=True, exist_ok=True)
       shutil.copy2(source_path, target_path)
       
       # Oppdater Image record
       image.storage_relative_path = str(relative_path)
   ```

7. **Metadata Generation**:
   ```python
   metadata = {
       "import_session_id": str(import_session.id),
       "created_at": import_session.created_at.isoformat(),
       "source_path": str(import_session.original_source_path),
       "total_files": len(import_session.images),
       # ... resten av metadata
   }
   
   with open(storage_dir / "metadata.json", "w") as f:
       json.dump(metadata, f, indent=2)
   ```

8. **Database Update**:
   ```python
   import_session.storage_uuid = storage_uuid
   import_session.copy_status = "completed"
   import_session.copy_completed_at = datetime.utcnow()
   ```

## 🖥️ Frontend Utvidelser

### Import Dialog Utvidelser

```typescript
interface ImportSessionConfig {
  // Eksisterende
  source_directory: string;
  author_id?: number;
  
  // Nye felter
  storage_root: string;          // Sti til storage medium
  storage_accessible: boolean;   // Om storage er tilgjengelig
  copy_files: boolean;          // Om filer skal kopieres (default: true)
}
```

### UI Komponenter

1. **Storage Path Input**:
   ```svelte
   <div class="storage-config">
     <label>Storage Medium Path:</label>
     <input 
       type="text" 
       bind:value={storageRoot}
       class:error={!storageAccessible}
       placeholder="/media/external-drive"
     />
     {#if !storageAccessible}
       <div class="error">⚠️ Storage path not accessible</div>
     {/if}
   </div>
   ```

2. **Import Progress Extended**:
   ```svelte
   <div class="import-progress">
     <div class="phase">
       <span class="phase-name">Database Import</span>
       <progress value={dbProgress} max="100"></progress>
     </div>
     
     <div class="phase">
       <span class="phase-name">File Copying</span>
       <progress value={copyProgress} max="100"></progress>
       <span class="file-info">{currentFile} ({copiedFiles}/{totalFiles})</span>
     </div>
   </div>
   ```

3. **Post-Import Source Warning**:
   ```svelte
   {#if importCompleted}
     <div class="success-message">
       ✅ Import completed successfully!
       <p>Files have been copied to storage. The source directory is no longer needed.</p>
       <button on:click={showStorageInfo}>View Storage Location</button>
     </div>
   {/if}
   ```

## 🔧 API Endepunkter

### Storage Management

```python
@router.get("/import-sessions/{session_id}/storage-status")
async def get_storage_status(session_id: int):
    """Sjekk storage tilgjengelighet for import session"""
    return {
        "storage_accessible": session.is_storage_accessible,
        "storage_path": str(session.storage_directory) if session.storage_directory else None,
        "files_accessible": sum(1 for img in session.images if img.is_file_accessible),
        "total_files": len(session.images)
    }

@router.post("/import-sessions/{session_id}/update-storage-path")
async def update_storage_path(session_id: int, new_path: str):
    """Oppdater storage sti (f.eks. når ekstern disk kobles til annen sti)"""
    session.storage_path = new_path
    return {"success": True, "accessible": session.is_storage_accessible}

@router.get("/storage/scan-locations")
async def scan_storage_locations():
    """Scan tilgjengelige disker for import session kataloger"""
    locations = []
    for mount_point in get_mount_points():
        sessions_dir = Path(mount_point) / "import-sessions"
        if sessions_dir.exists():
            session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
            locations.append({
                "path": str(mount_point),
                "session_count": len(session_dirs),
                "sessions": [d.name for d in session_dirs]
            })
    return locations
```

### File Access

```python
@router.get("/images/{image_id}/file")
async def get_image_file(image_id: int):
    """Hent faktisk bildefil fra storage"""
    image = get_image_or_404(image_id)
    
    if not image.is_file_accessible:
        raise HTTPException(404, "Image file not accessible. Check storage connection.")
    
    file_path = image.storage_file_path
    return FileResponse(file_path)
```

## 🧪 Testing Scenarios

### Happy Path

1. **Full Import**: Source → Database → Storage → Source disconnect
2. **Storage Migration**: Move storage to new disk, update path, verify access
3. **Partial Failure Recovery**: Handle copy failures, rollback, retry

### Error Cases

1. **Storage Full**: Handle disk space errors during copy
2. **Permission Issues**: Handle write permission errors
3. **Network Disconnect**: Handle storage disconnection during copy
4. **Corrupted Files**: Verify file integrity after copy

### Recovery Scenarios

1. **Resume Failed Copy**: Continue copying from last successful file
2. **Storage Path Update**: Update paths when storage is moved
3. **Missing Storage**: Graceful degradation when files not accessible

## 🔒 Sikkerhet og Integritet

### File Verification

```python
def verify_file_copy(source: Path, target: Path) -> bool:
    """Verifiser at fil ble kopiert korrekt"""
    if not target.exists():
        return False
    
    # Sammenlign filstørrelse
    if source.stat().st_size != target.stat().st_size:
        return False
    
    # Sammenlign checksums for kritiske filer
    if source.suffix.lower() in ['.raw', '.dng']:
        return calculate_sha256(source) == calculate_sha256(target)
    
    return True
```

### Rollback Strategy

```python
def rollback_failed_import(import_session: ImportSession):
    """Rull tilbake mislykket import"""
    if import_session.storage_directory and import_session.storage_directory.exists():
        shutil.rmtree(import_session.storage_directory)
    
    # Fjern database records
    for image in import_session.images:
        db.delete(image)
    for photo in import_session.photos:
        db.delete(photo)
    
    import_session.copy_status = "failed"
    db.commit()
```

## 🚀 Implementeringsfaser

### Fase 1: Database Schema
- [ ] Utvid ImportSession model med storage felter
- [ ] Utvid Image model med storage paths
- [ ] Lag database migrering
- [ ] Test nye felter og relationships

### Fase 2: Backend Storage Logic
- [ ] Implementer storage directory creation
- [ ] Implementer file copying med progress
- [ ] Implementer metadata generation
- [ ] Legg til API endepunkter for storage management

### Fase 3: Frontend Integration
- [ ] Utvid import dialog med storage path
- [ ] Legg til storage accessibility checking
- [ ] Implementer extended progress tracking
- [ ] Legg til post-import storage info

### Fase 4: Error Handling & Recovery
- [ ] Implementer rollback på feil
- [ ] Legg til resume functionality
- [ ] Implementer storage path update
- [ ] Test alle error scenarios

### Fase 5: Optimization & Polish
- [ ] Implementer parallel file copying
- [ ] Legg til file integrity verification
- [ ] Optimiser storage scanning
- [ ] Legg til storage analytics

## 📊 Metrics & Monitoring

### Import Metrics
- Copy speed (MB/s)
- Success/failure rates
- Storage utilization
- Average import size

### Storage Health
- Disk space monitoring
- File accessibility checks
- Integrity verification results
- Performance metrics

## 🔄 Migration Strategy

### Eksisterende Data
- Marker eksisterende ImportSessions som "legacy"
- Tilby optional retroactive copying
- Gradvis migration ved re-import

### Backwards Compatibility
- Behold support for ikke-kopierte imports
- Graceful degradation når storage ikke tilgjengelig
- Clear UI indicators for legacy vs. storage-backed imports

---

*Dette systemet sikrer permanent arkivering av importerte bilder og gjør ImaLink helt uavhengig av originalkilder.*