# ImaLink Storage Architecture
## Hybrid File Management System

**Version**: 2.0  
**Date**: October 18, 2025  
**Author**: ImaLink Development Team

---

## 🎯 **Core Philosophy**

ImaLink implements a revolutionary **Hybrid Storage Architecture** that combines the best of two worlds:

- **Database-powered organization**: Fast search, metadata management, and relational linking
- **User-controlled file structure**: Complete freedom to organize files using familiar file explorer tools

### **The Innovation: Per-ImportSession JSON Indexes**

Unlike traditional photo management systems, ImaLink allows users to reorganize their files at any time while maintaining complete database connectivity through **hothash-based identification** and **per-session JSON indexes**.

---

## 🏗️ **Architecture Overview**

```
FileStorage Directory Structure:
├── index.json                    # Master overview of all import sessions
├── imports/                      # Per-session JSON indexes
│   ├── session_42.json          # "Italy Summer 2024"
│   ├── session_43.json          # "Wedding Photos" 
│   └── session_44.json          # "Norway Trip"
├── photos/                      # USER-CONTROLLED organization
│   ├── 2024/italy/             # User can reorganize freely
│   │   ├── rome/IMG001.jpg     # From session_42
│   │   └── venice/IMG045.jpg   # From session_42
│   ├── 2024/wedding/           # From session_43
│   └── 2024/norway/            # From session_44
└── .imalink/                   # System files (hidden)
    ├── hotpreviews/            # Organized by hothash
    │   ├── a1/b2/a1b2c3d4.jpg # 200x200 previews
    │   └── e5/f6/e5f6g7h8.jpg
    └── metadata/               # Additional system data
```

---

## 🔑 **Key Components**

### **1. FileStorage Model**
```python
class FileStorage(Base):
    """Physical storage location with UUID-based naming"""
    storage_uuid: str           # Unique identifier
    directory_name: str         # "imalink_20241018_143052_a1b2c3d4"
    base_path: str             # "/external/photos"
    full_path: str             # "{base_path}/{directory_name}"
    is_accessible: bool        # Storage availability status
    total_files: int           # File count statistics
    total_size_bytes: int      # Size statistics
```

**Key Properties:**
- `master_index_path` → `"{full_path}/index.json"`
- `imports_index_dir` → `"{full_path}/imports"`
- `get_session_index_path(session_id)` → Path to session JSON

### **2. ImportSession Model** 
```python
class ImportSession(Base):
    """User's reference metadata for a batch of imported photos"""
    id: int                    # Primary key
    title: str                 # "Italy Summer 2024"
    description: str           # User's notes
    imported_at: datetime      # When import happened
    file_storage_id: int       # FK to FileStorage
    default_author_id: int     # Default photographer
    
    # Relationships
    file_storage: FileStorage
    image_files: List[ImageFile]
```

**Index Generation:**
- `index_filename` → `"session_{id}.json"`
- `index_path` → Full path to session index
- `generate_index_data()` → Complete JSON with all files and metadata

---

## 📋 **JSON Index Formats**

### **Master Index (index.json)**
```json
{
  "storage_info": {
    "uuid": "abc123-def456-ghi789",
    "directory_name": "imalink_20241018_143052_a1b2c3d4", 
    "base_path": "/external/photos",
    "display_name": "External Drive Photos",
    "created_at": "2024-10-18T14:30:52Z",
    "last_scan": "2024-10-18T16:45:00Z",
    "is_accessible": true,
    "total_files": 324,
    "total_size_mb": 1250.5
  },
  "import_sessions": [
    {
      "id": 42,
      "title": "Italy Summer 2024",
      "imported_at": "2024-07-15T10:00:00Z", 
      "file_count": 127,
      "index_file": "imports/session_42.json"
    },
    {
      "id": 43,
      "title": "Wedding Photos",
      "imported_at": "2024-08-20T14:30:00Z",
      "file_count": 89,
      "index_file": "imports/session_43.json"
    }
  ],
  "imalink_version": "2.0"
}
```

### **Session Index (session_42.json)**
```json
{
  "import_session": {
    "id": 42,
    "title": "Italy Summer 2024",
    "description": "Family vacation to Rome, Venice, Florence",
    "imported_at": "2024-07-15T10:00:00Z",
    "default_author_id": 1,
    "file_storage_id": 5,
    "storage_directory": "imalink_20241018_143052_a1b2c3d4"
  },
  "files": {
    "a1b2c3d4e5f6g7h8": {
      "filename": "IMG_001.jpg",
      "file_size": 2048576,
      "taken_at": "2024-07-10T14:30:00Z",
      "created_at": "2024-07-15T10:15:00Z",
      "original_filename": "IMG_001.jpg",
      "file_format": "JPEG",
      "width": 4000,
      "height": 3000,
      "has_hotpreview": true
    },
    "e5f6g7h8i9j0k1l2": {
      "filename": "IMG_002.CR2", 
      "file_size": 25600000,
      "taken_at": "2024-07-10T15:45:00Z",
      "created_at": "2024-07-15T10:16:00Z", 
      "original_filename": "IMG_002.CR2",
      "file_format": "RAW",
      "width": 6000,
      "height": 4000,
      "has_hotpreview": true
    }
  },
  "statistics": {
    "total_files": 127,
    "index_generated": "2024-10-18T16:45:00Z",
    "imalink_version": "2.0"
  }
}
```

---

## 🔄 **Core Workflows**

### **Import Process**
1. **User initiates import**: Select source directory and target FileStorage
2. **File scanning**: Backend scans source for image files
3. **Metadata extraction**: Generate hothash, extract EXIF, create hotpreview
4. **Database registration**: Create ImportSession and ImageFile records
5. **File copying**: Copy files to FileStorage directory
6. **Index generation**: Create session_X.json with complete metadata
7. **Master index update**: Update index.json with new session

### **User Reorganization**
1. **User reorganizes files**: Move files freely in photos/ directory using file explorer
2. **Re-scan trigger**: User runs scan via CLI/API or automatic detection
3. **Hothash identification**: System calculates hothash for each file found
4. **Database matching**: Match files to existing records via hothash
5. **Index update**: Update session indexes with new file paths
6. **Conflict resolution**: Handle any missing or duplicate files

### **Database Recovery**
1. **Scan FileStorage**: Discover all session indexes in imports/ directory
2. **Read master index**: Get overview of expected sessions and files  
3. **Process session indexes**: Reconstruct ImportSession and ImageFile records
4. **Hothash linking**: Connect files to Photo records via hothash matching
5. **Validation**: Verify file existence and data integrity
6. **Report**: Generate summary of restored vs missing data

---

## 🛠️ **Technical Implementation**

### **Core Services**

#### **StorageIndexService**
```python
class StorageIndexService:
    """Generate and maintain JSON indexes"""
    
    def generate_session_index(session: ImportSession) -> dict
    def write_session_index(session: ImportSession) -> str
    def generate_master_index(storage: FileStorage) -> dict  
    def write_master_index(storage: FileStorage) -> str
    def generate_all_indexes(storage_uuid: str) -> dict
    def scan_storage_for_changes(storage_uuid: str) -> dict
    def read_session_index(session: ImportSession) -> dict
    def read_master_index(storage: FileStorage) -> dict
```

#### **FileStorageService** 
```python
class FileStorageService:
    """Manage FileStorage lifecycle and operations"""
    
    def create_storage(base_path: str, display_name: str) -> FileStorage
    def get_storage_statistics(storage_uuid: str) -> dict
    def check_accessibility(storage_uuid: str) -> bool
    def deactivate_storage(storage_uuid: str) -> bool
    def reactivate_storage(storage_uuid: str) -> bool
```

### **API Endpoints**

#### **Storage Management**
- `POST /api/v1/file-storage/create` - Create new FileStorage
- `GET /api/v1/file-storage/{uuid}` - Get FileStorage details
- `GET /api/v1/file-storage/{uuid}/statistics` - Get storage stats
- `POST /api/v1/file-storage/{uuid}/accessibility` - Check/update accessibility

#### **Index Management**  
- `POST /api/v1/storage-index/generate/{uuid}` - Generate all indexes
- `POST /api/v1/storage-index/session/{session_id}` - Generate session index
- `GET /api/v1/storage-index/status/{uuid}` - Get index status
- `POST /api/v1/storage-index/scan/{uuid}` - Scan for changes
- `GET /api/v1/storage-index/master/{uuid}` - Read master index
- `GET /api/v1/storage-index/session/{session_id}` - Read session index

---

## 💡 **Key Benefits**

### **For Users**
- ✅ **Familiar workflow**: Continue using file explorer and existing tools
- ✅ **No vendor lock-in**: Files remain in standard formats and locations
- ✅ **Flexible organization**: Reorganize anytime without losing database connections
- ✅ **Portable storage**: Move FileStorage directories between systems
- ✅ **Offline access**: Browse files even when database is unavailable

### **For Administrators**
- ✅ **Robust backup**: JSON indexes enable complete database reconstruction  
- ✅ **System migration**: Easy to move between different ImaLink instances
- ✅ **Storage flexibility**: Support any storage medium (local, NAS, cloud)
- ✅ **Selective sync**: Process only changed files during re-indexing
- ✅ **Conflict resolution**: Clear workflows for handling data inconsistencies

### **For Developers**
- ✅ **Clear separation**: Database layer independent of file organization
- ✅ **Extensible format**: JSON indexes can accommodate future metadata
- ✅ **Hothash consistency**: Universal file identification across systems
- ✅ **API-driven**: All operations accessible via REST endpoints
- ✅ **Testable architecture**: Mock FileStorage for unit testing

---

## 🔒 **Data Integrity & Safety**

### **Hothash as Universal Key**
Every image file is identified by its **hothash** (computed from image content), making it:
- **Location-independent**: File can be moved without losing database connection
- **Duplicate-resistant**: Same image detected regardless of filename
- **Version-safe**: Different edits get different hothashes
- **Cross-system compatible**: Same hothash across different ImaLink instances

### **Multi-layered Backup**
1. **Primary database**: Full relational data with fast queries
2. **Session indexes**: Complete per-import metadata in JSON
3. **Master index**: Storage overview and session directory
4. **File checksums**: Integrity verification for all files
5. **Hotpreviews**: Visual identification even if originals are lost

### **Graceful Degradation**
- **Missing files**: Show metadata with clear "file not found" indicator
- **Corrupt indexes**: Regenerate from database or file scanning
- **Inaccessible storage**: Clear status reporting and recovery options
- **Partial imports**: Handle incomplete or interrupted operations

---

## 🚀 **Future Enhancements**

### **Phase 1: Core Stability** ✅
- [x] Basic FileStorage and ImportSession models
- [x] JSON index generation and reading
- [x] Master index management
- [x] Core API endpoints

### **Phase 2: Advanced Features** 🔄
- [ ] Incremental scanning (only changed files)
- [ ] Multi-storage support (multiple FileStorage per session)
- [ ] Conflict resolution UI
- [ ] Batch operations for large reorganizations

### **Phase 3: Enterprise Features** 📅
- [ ] Network storage optimization
- [ ] Distributed scanning across multiple machines
- [ ] Advanced integrity checking and repair
- [ ] Custom metadata fields in indexes
- [ ] Storage usage analytics and reporting

---

## 📚 **Related Documentation**

- [API Reference](api/API_REFERENCE.md) - Complete API documentation including FileStorage
- [Storage Workflows](STORAGE_WORKFLOW.md) - Practical examples and use cases
- [Migration Guide](STORAGE_MIGRATION.md) - Upgrading from legacy storage systems
- [Troubleshooting](STORAGE_TROUBLESHOOTING.md) - Common issues and solutions

---

*This architecture represents a fundamental shift from traditional "database owns files" to "files and database coexist harmoniously" - enabling unprecedented flexibility while maintaining the power of structured data management.*