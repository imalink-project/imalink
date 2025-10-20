# ImaLink Storage Workflows
## Practical Examples and Use Cases

**Version**: 2.0  
**Date**: October 18, 2025

---

## 🎯 **Overview**

This guide provides practical workflows for ImaLink's hybrid storage architecture. Each scenario includes step-by-step instructions, API calls, and expected outcomes.

---

## 🚀 **Getting Started Workflows**

### **Workflow 1: First-Time Setup**

**Scenario**: New ImaLink installation, setting up first FileStorage for photo collection.

#### **Step 1: Create FileStorage**
```bash
# Create storage on external drive
curl -X POST http://localhost:8000/api/v1/file-storage/create \
  -H "Content-Type: application/json" \
  -d '{
    "base_path": "/external/photos",
    "display_name": "Main Photo Archive",
    "description": "Primary storage for all family photos"
  }'
```

**Result**: FileStorage created with UUID and directory name like `imalink_20241018_143052_a1b2c3d4`

#### **Step 2: Verify Storage**
```bash
# Check accessibility
curl -X POST http://localhost:8000/api/v1/file-storage/{uuid}/accessibility
```

**Result**: Confirms storage is writable and has adequate space

#### **Step 3: First Import**
```bash
# Create ImportSession
curl -X POST http://localhost:8000/api/v1/import-sessions/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Italy Vacation 2024",
    "description": "Family trip to Rome and Venice",
    "default_author_id": 1,
    "file_storage_id": 5
  }'
```

**Result**: ImportSession linked to FileStorage, ready for file import

#### **Step 4: Generate Initial Index**
```bash
# Create session index after files are imported
curl -X POST http://localhost:8000/api/v1/storage-index/session/42
```

**Result**: JSON index created at `{storage}/imports/session_42.json`

---

### **Workflow 2: Regular Photo Import**

**Scenario**: Importing photos from a memory card after a photo session.

#### **Step 1: Import Files**
- Copy files from memory card to temporary location
- Use ImaLink import process to scan and register files
- Files are copied to FileStorage and database records created

#### **Step 2: Automatic Index Generation**
```python
# Python example for automated indexing
import requests

def import_and_index_photos(source_dir, storage_uuid, session_title):
    # 1. Create ImportSession
    session_data = {
        "title": session_title,
        "file_storage_id": get_storage_id(storage_uuid)
    }
    session = requests.post("/api/v1/import-sessions/create", 
                           json=session_data).json()
    
    # 2. Process files (separate import API)
    # ... file processing happens here ...
    
    # 3. Generate session index
    session_id = session["data"]["id"]
    index_result = requests.post(f"/api/v1/storage-index/session/{session_id}")
    
    # 4. Update master index
    master_result = requests.post(f"/api/v1/storage-index/generate/{storage_uuid}")
    
    return {
        "session_id": session_id,
        "files_imported": session["data"]["images_count"],
        "index_generated": index_result.json()["success"]
    }
```

#### **Step 3: Verify Import**
```bash
# Check import status
curl -X GET http://localhost:8000/api/v1/import-sessions/42

# Verify index exists
curl -X GET http://localhost:8000/api/v1/storage-index/status/{storage_uuid}
```

**Expected File Structure:**
```
/external/photos/imalink_20241018_143052_a1b2c3d4/
├── index.json                    # Updated with new session
├── imports/
│   └── session_42.json          # New session index
├── photos/
│   └── 2024/italy/              # Imported files
│       ├── IMG_001.jpg
│       ├── IMG_002.CR2
│       └── ...
└── .imalink/
    └── hotpreviews/             # Generated previews
        ├── a1/b2/a1b2c3d4.jpg
        └── ...
```

---

## 🔄 **File Management Workflows**

### **Workflow 3: User File Reorganization**

**Scenario**: User wants to reorganize photos using file explorer after import.

#### **Before Reorganization**
```
photos/
├── 2024/italy/
│   ├── IMG_001.jpg
│   ├── IMG_002.CR2
│   └── IMG_003.jpg
└── 2024/wedding/
    ├── DSC_001.jpg
    └── DSC_002.jpg
```

#### **Step 1: User Reorganizes Files**
User moves files in file explorer to preferred structure:

```
photos/
├── Vacations/
│   └── Italy_2024/
│       ├── Rome/
│       │   ├── IMG_001.jpg
│       │   └── IMG_003.jpg
│       └── Venice/
│           └── IMG_002.CR2
└── Events/
    └── Wedding_August/
        ├── DSC_001.jpg
        └── DSC_002.jpg
```

#### **Step 2: Scan for Changes**
```bash
# Detect file movements
curl -X POST http://localhost:8000/api/v1/storage-index/scan/{storage_uuid}
```

**Response Example:**
```json
{
  "success": true,
  "data": {
    "changes_detected": true,
    "moved_files": [
      {
        "hothash": "a1b2c3d4e5f6g7h8",
        "old_path": "photos/2024/italy/IMG_001.jpg",
        "new_path": "photos/Vacations/Italy_2024/Rome/IMG_001.jpg",
        "session_id": 42
      }
    ],
    "missing_files": [],
    "new_files": []
  }
}
```

#### **Step 3: Update Indexes**
```bash
# Regenerate affected session indexes
curl -X POST http://localhost:8000/api/v1/storage-index/session/42
curl -X POST http://localhost:8000/api/v1/storage-index/session/43

# Update master index
curl -X POST http://localhost:8000/api/v1/storage-index/generate/{storage_uuid}
```

**Result**: Database and indexes updated with new file paths, maintaining all metadata connections.

---

### **Workflow 4: Multi-Storage Management**

**Scenario**: Managing photos across multiple storage devices (main drive, external backup, NAS).

#### **Step 1: Create Multiple FileStorages**
```bash
# Main storage (fast SSD)
curl -X POST http://localhost:8000/api/v1/file-storage/create \
  -d '{"base_path": "/home/photos", "display_name": "Main SSD"}'

# Backup storage (external drive)  
curl -X POST http://localhost:8000/api/v1/file-storage/create \
  -d '{"base_path": "/backup/photos", "display_name": "Backup Drive"}'

# Archive storage (NAS)
curl -X POST http://localhost:8000/api/v1/file-storage/create \
  -d '{"base_path": "/nas/archive", "display_name": "NAS Archive"}'
```

#### **Step 2: Distribute Import Sessions**
```python
# Python workflow for intelligent storage distribution
def distribute_imports():
    storages = get_all_storages()
    
    for storage in storages:
        # Check space and accessibility
        stats = requests.get(f"/api/v1/file-storage/{storage['uuid']}/statistics")
        accessibility = requests.post(f"/api/v1/file-storage/{storage['uuid']}/accessibility")
        
        if accessibility.json()["data"]["is_accessible"]:
            free_space = accessibility.json()["data"]["free_space_gb"]
            print(f"{storage['display_name']}: {free_space:.1f} GB free")
    
    # Create session on storage with most space
    best_storage = max(storages, key=lambda s: get_free_space(s))
    
    session = requests.post("/api/v1/import-sessions/create", json={
        "title": "Latest Import",
        "file_storage_id": best_storage["id"]
    })
    
    return session.json()
```

#### **Step 3: Monitor Storage Health**
```bash
# Check all storages
curl -X GET http://localhost:8000/api/v1/file-storage/

# Get detailed statistics
for uuid in storage_uuids; do
  curl -X GET http://localhost:8000/api/v1/file-storage/$uuid/statistics
done
```

---

## 🔧 **Maintenance Workflows**

### **Workflow 5: Storage Migration**

**Scenario**: Moving FileStorage from one drive to another (e.g., upgrading to larger drive).

#### **Step 1: Prepare New Storage**
```bash
# Create new storage location
curl -X POST http://localhost:8000/api/v1/file-storage/create \
  -d '{
    "base_path": "/new/larger/drive", 
    "display_name": "New 4TB Drive",
    "description": "Upgraded storage with more capacity"
  }'
```

#### **Step 2: Copy Files**
```bash
# Copy entire FileStorage directory
rsync -av /old/drive/imalink_20241018_143052_a1b2c3d4/ \
         /new/larger/drive/imalink_20241018_143052_a1b2c3d4/
```

#### **Step 3: Update Database**
```python
# Update FileStorage record to point to new location
import requests

old_uuid = "abc123-def456-ghi789"
new_base_path = "/new/larger/drive"

# This would require admin API to update base_path
# Alternatively, recreate FileStorage and migrate ImportSessions
```

#### **Step 4: Verify Migration**
```bash
# Check accessibility of new location
curl -X POST http://localhost:8000/api/v1/file-storage/{new_uuid}/accessibility

# Verify indexes are intact
curl -X GET http://localhost:8000/api/v1/storage-index/status/{new_uuid}

# Test sample file access
curl -X GET http://localhost:8000/api/v1/storage-index/session/42
```

#### **Step 5: Deactivate Old Storage**
```bash
# Mark old storage as inactive
curl -X POST http://localhost:8000/api/v1/file-storage/{old_uuid}/deactivate
```

---

### **Workflow 6: Disaster Recovery**

**Scenario**: Database lost, but FileStorage directories with indexes are intact.

#### **Step 1: Scan Available Storages**
```bash
# Scan file system for ImaLink storage directories
find /external /backup /nas -name "imalink_*" -type d 2>/dev/null
```

Expected output:
```
/external/photos/imalink_20241018_143052_a1b2c3d4
/backup/photos/imalink_20241015_092134_e5f6g7h8
/nas/archive/imalink_20241010_174523_i9j0k1l2
```

#### **Step 2: Read Master Indexes**
```bash
# Check what data is available
for dir in $(find /external /backup /nas -name "imalink_*" -type d); do
  if [ -f "$dir/index.json" ]; then
    echo "=== $dir ==="
    jq '.storage_info.display_name, .import_sessions[].title' "$dir/index.json"
  fi
done
```

#### **Step 3: Recreate FileStorage Records**
```python
# Python script to recreate database from indexes
import json
import requests
from pathlib import Path

def recover_from_indexes():
    storage_dirs = find_storage_directories()
    recovered = []
    
    for storage_dir in storage_dirs:
        master_index_path = storage_dir / "index.json"
        
        if master_index_path.exists():
            with open(master_index_path) as f:
                master_data = json.load(f)
            
            # Recreate FileStorage
            storage_info = master_data["storage_info"]
            new_storage = requests.post("/api/v1/file-storage/create", json={
                "base_path": str(storage_dir.parent),
                "display_name": storage_info["display_name"],
                "description": f"Recovered from {storage_dir}"
            }).json()
            
            # Recreate ImportSessions
            for session_info in master_data["import_sessions"]:
                session_index_path = storage_dir / session_info["index_file"]
                
                if session_index_path.exists():
                    with open(session_index_path) as f:
                        session_data = json.load(f)
                    
                    # Recreate ImportSession
                    session_meta = session_data["import_session"]
                    new_session = requests.post("/api/v1/import-sessions/create", json={
                        "title": session_meta["title"],
                        "description": session_meta.get("description"),
                        "file_storage_id": new_storage["data"]["id"]
                    }).json()
                    
                    # Recreate ImageFiles from index data
                    for hothash, file_data in session_data["files"].items():
                        # This would require additional APIs to recreate ImageFiles
                        pass
            
            recovered.append({
                "storage_dir": str(storage_dir),
                "sessions_recovered": len(master_data["import_sessions"])
            })
    
    return recovered
```

#### **Step 4: Verify Recovery**
```bash
# Check that all FileStorages are accessible
curl -X GET http://localhost:8000/api/v1/file-storage/

# Verify ImportSessions are connected
curl -X GET http://localhost:8000/api/v1/import-sessions/

# Test index consistency
for uuid in recovered_uuids; do
  curl -X POST http://localhost:8000/api/v1/storage-index/scan/$uuid
done
```

---

## 📊 **Monitoring Workflows**

### **Workflow 7: Health Monitoring**

**Scenario**: Regular monitoring of storage health and usage.

#### **Daily Health Check Script**
```python
#!/usr/bin/env python3
"""ImaLink Storage Health Monitor"""

import requests
import json
from datetime import datetime

def daily_health_check():
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "storages": [],
        "issues": [],
        "summary": {}
    }
    
    # Get all storages
    storages_response = requests.get("/api/v1/file-storage/")
    storages = storages_response.json()["data"]["storages"]
    
    total_files = 0
    total_size = 0
    accessible_count = 0
    
    for storage in storages:
        uuid = storage["storage_uuid"]
        
        # Check accessibility
        access_check = requests.post(f"/api/v1/file-storage/{uuid}/accessibility")
        access_data = access_check.json()["data"]
        
        # Get statistics
        stats_response = requests.get(f"/api/v1/file-storage/{uuid}/statistics")
        stats_data = stats_response.json()["data"]
        
        # Check index status
        index_status = requests.get(f"/api/v1/storage-index/status/{uuid}")
        index_data = index_status.json()["data"]
        
        storage_report = {
            "uuid": uuid,
            "name": storage["display_name"],
            "accessible": access_data["is_accessible"],
            "free_space_gb": access_data.get("free_space_gb", 0),
            "total_files": stats_data["statistics"]["total_files"],
            "size_mb": stats_data["statistics"]["total_size_mb"],
            "import_sessions": len(stats_data["import_sessions"]),
            "indexes_healthy": index_data["master_index_exists"]
        }
        
        report["storages"].append(storage_report)
        
        # Accumulate totals
        if storage_report["accessible"]:
            accessible_count += 1
            total_files += storage_report["total_files"]
            total_size += storage_report["size_mb"]
        
        # Check for issues
        if not storage_report["accessible"]:
            report["issues"].append(f"Storage '{storage['display_name']}' is not accessible")
        
        if storage_report["free_space_gb"] < 1.0:
            report["issues"].append(f"Storage '{storage['display_name']}' is low on space")
        
        if not storage_report["indexes_healthy"]:
            report["issues"].append(f"Storage '{storage['display_name']}' has missing indexes")
    
    # Summary
    report["summary"] = {
        "total_storages": len(storages),
        "accessible_storages": accessible_count,
        "total_files": total_files,
        "total_size_gb": round(total_size / 1024, 2),
        "issues_count": len(report["issues"])
    }
    
    return report

# Run and save report
if __name__ == "__main__":
    report = daily_health_check()
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"storage_health_{timestamp}.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"Storage Health Report - {report['timestamp']}")
    print(f"Storages: {report['summary']['accessible_storages']}/{report['summary']['total_storages']} accessible")
    print(f"Files: {report['summary']['total_files']:,} ({report['summary']['total_size_gb']} GB)")
    print(f"Issues: {report['summary']['issues_count']}")
    
    if report['issues']:
        print("\nIssues found:")
        for issue in report['issues']:
            print(f"  - {issue}")
```

#### **Weekly Index Regeneration**
```bash
#!/bin/bash
# Weekly maintenance script

echo "=== Weekly ImaLink Storage Maintenance ==="
echo "Starting: $(date)"

# Get all storage UUIDs
storage_uuids=$(curl -s http://localhost:8000/api/v1/file-storage/ | jq -r '.data.storages[].storage_uuid')

for uuid in $storage_uuids; do
    echo "Processing storage: $uuid"
    
    # Regenerate all indexes
    curl -X POST http://localhost:8000/api/v1/storage-index/generate/$uuid
    
    # Scan for changes
    curl -X POST http://localhost:8000/api/v1/storage-index/scan/$uuid
    
    echo "Completed storage: $uuid"
done

echo "Maintenance completed: $(date)"
```

---

## 🎛️ **Advanced Workflows**

### **Workflow 8: Bulk Operations**

**Scenario**: Managing large numbers of files and sessions efficiently.

#### **Batch Index Generation**
```python
import asyncio
import aiohttp

async def batch_generate_indexes(session_ids):
    """Generate indexes for multiple sessions concurrently"""
    
    async def generate_single_index(session, session_id):
        url = f"http://localhost:8000/api/v1/storage-index/session/{session_id}"
        async with session.post(url) as response:
            return await response.json()
    
    async with aiohttp.ClientSession() as session:
        tasks = [generate_single_index(session, sid) for sid in session_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

# Usage
session_ids = [42, 43, 44, 45, 46]  # Batch of sessions to process
results = asyncio.run(batch_generate_indexes(session_ids))
```

#### **Bulk File Validation**
```python
def validate_storage_integrity(storage_uuid):
    """Validate all files in a storage against their indexes"""
    
    # Get master index
    master_response = requests.get(f"/api/v1/storage-index/master/{storage_uuid}")
    master_data = master_response.json()["data"]
    
    validation_results = {
        "storage_uuid": storage_uuid,
        "total_sessions": len(master_data["import_sessions"]),
        "validated_files": 0,
        "missing_files": [],
        "extra_files": [],
        "corrupted_files": []
    }
    
    for session_info in master_data["import_sessions"]:
        session_id = session_info["id"]
        
        # Get session index
        session_response = requests.get(f"/api/v1/storage-index/session/{session_id}")
        if not session_response.ok:
            continue
            
        session_data = session_response.json()["data"]
        
        # Validate each file
        for hothash, file_info in session_data["files"].items():
            file_path = f"{master_data['storage_info']['full_path']}/photos/{file_info['filename']}"
            
            if not os.path.exists(file_path):
                validation_results["missing_files"].append({
                    "hothash": hothash,
                    "expected_path": file_path,
                    "session_id": session_id
                })
            else:
                # Could add checksum validation here
                validation_results["validated_files"] += 1
    
    return validation_results
```

---

## 📋 **Troubleshooting Workflows**

### **Common Issues and Solutions**

#### **Issue: Storage Inaccessible**
```bash
# Diagnose accessibility
curl -X POST http://localhost:8000/api/v1/file-storage/{uuid}/accessibility

# Check mount points
df -h | grep -E "(external|backup|nas)"

# Test write permissions
touch /external/photos/test_write && rm /external/photos/test_write
```

#### **Issue: Missing Index Files**
```bash
# Regenerate missing indexes
curl -X POST http://localhost:8000/api/v1/storage-index/generate/{uuid}

# Check index status
curl -X GET http://localhost:8000/api/v1/storage-index/status/{uuid}
```

#### **Issue: Files Moved by User**
```bash
# Scan for changes
curl -X POST http://localhost:8000/api/v1/storage-index/scan/{uuid}

# Review detected changes
curl -X GET http://localhost:8000/api/v1/storage-index/master/{uuid}

# Update affected session indexes
curl -X POST http://localhost:8000/api/v1/storage-index/session/{session_id}
```

---

## 📚 **Best Practices**

### **1. Regular Maintenance**
- **Daily**: Run accessibility checks
- **Weekly**: Regenerate all indexes
- **Monthly**: Full storage validation
- **Quarterly**: Review storage distribution and capacity

### **2. User Education**  
- Train users on the hybrid model benefits
- Provide clear guidelines for file organization
- Document the scanning and recovery process
- Set expectations about index regeneration time

### **3. Monitoring and Alerts**
- Monitor storage capacity and accessibility
- Alert on missing or corrupted indexes
- Track import session growth rates
- Monitor API response times for storage operations

### **4. Backup Strategy**
- Include JSON indexes in backup procedures
- Test recovery procedures regularly
- Keep multiple copies of master indexes
- Document storage locations and access credentials

---

*These workflows demonstrate the full power and flexibility of ImaLink's hybrid storage architecture, enabling seamless integration of database-driven management with user-controlled file organization.*