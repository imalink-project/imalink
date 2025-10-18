# ImaLink Documentation Index
## Storage Architecture & Implementation Guide

**Last Updated**: October 18, 2025  
**Version**: 2.0

---

## 📖 **Documentation Overview**

This documentation set covers ImaLink's revolutionary **Hybrid Storage Architecture** - a system that combines database-powered organization with complete user control over file structure.

---

## 📁 **Core Documentation**

### **[Storage Architecture](STORAGE_ARCHITECTURE.md)**
Complete overview of the hybrid storage system design and philosophy.

**Key Topics:**
- Per-ImportSession JSON indexing
- Hothash-based file identification  
- User-controlled file organization
- Database recovery mechanisms
- Technical implementation details

**Read this first** to understand the core concepts and benefits.

---

### **[API Reference](api/API_REFERENCE.md)**  
Complete API documentation for all endpoints including FileStorage management.

**Key Topics:**
- FileStorage management endpoints
- Index generation and maintenance APIs
- Scanning and synchronization operations
- Error handling and status codes
- Request/response formats

**Essential for developers** integrating with the storage system.

---

### **[Storage Workflows](STORAGE_WORKFLOW.md)**
Practical examples and step-by-step workflows for common scenarios.

**Key Topics:**
- First-time setup procedures
- Regular photo import workflows
- File reorganization handling
- Multi-storage management
- Disaster recovery procedures
- Monitoring and maintenance

**Perfect for administrators** and power users managing ImaLink installations.

---

### **Legacy Documentation**
- **[General API Guidelines](general_api_guidelines.md)** - REST API standards and conventions
- **[Service Layer Guide](service_layer_guide.md)** - Architecture patterns and service implementation
- **[Legacy API Reference](api/API_REFERENCE.md)** - Previous endpoint documentation

---

## 🎯 **Quick Start Guide**

### **New Users: Getting Started**
1. Read [Storage Architecture](STORAGE_ARCHITECTURE.md) - Overview and concepts
2. Follow [Workflow 1](STORAGE_WORKFLOW.md#workflow-1-first-time-setup) - First-time setup
3. Try [Workflow 2](STORAGE_WORKFLOW.md#workflow-2-regular-photo-import) - Import your first photos

### **Developers: API Integration**
1. Review [API Reference](api/API_REFERENCE.md) - Complete endpoint documentation
2. Check [FileStorage Testing Examples](api/API_REFERENCE.md#filestorage-testing-examples) - cURL and Python examples  
3. Implement using [Schema Reference](api/API_REFERENCE.md#schema-reference) - TypeScript models

### **Administrators: System Management**
1. Set up [Health Monitoring](STORAGE_WORKFLOW.md#workflow-7-health-monitoring) - Daily checks
2. Plan [Storage Migration](STORAGE_WORKFLOW.md#workflow-5-storage-migration) procedures
3. Prepare [Disaster Recovery](STORAGE_WORKFLOW.md#workflow-6-disaster-recovery) plans

---

## 🔑 **Key Concepts Summary**

### **FileStorage**
- Physical storage location with UUID-based naming
- Directory structure: \`imalink_YYYYMMDD_HHMMSS_uuid8\`
- Contains master index and per-session indexes
- Supports any storage medium (local, external, NAS, cloud)

### **ImportSession** 
- User's reference metadata for a batch of imported photos
- Natural grouping: "Italy Vacation", "Wedding Photos", etc.
- Each session gets its own JSON index file
- Linked to FileStorage via foreign key relationship

### **JSON Indexes**
- **Master Index**: \`index.json\` - Overview of all sessions in storage
- **Session Indexes**: \`imports/session_X.json\` - Complete file metadata per session
- Enable offline browsing and database reconstruction
- Self-contained with all necessary recovery information

### **Hothash Identification**
- Universal file identifier computed from image content
- Location-independent - files can be moved freely
- Duplicate-resistant and version-safe
- Enables cross-system compatibility

---

*This documentation represents the complete guide to ImaLink's innovative storage architecture - enabling unprecedented flexibility while maintaining the power of structured data management.*
