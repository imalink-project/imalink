# ImaLink Qt Frontend Development Guide
## Modern Qt Integration with Hybrid Storage Architecture

**Version**: 2.0  
**Date**: October 18, 2025  
**Target**: Qt 6.x with C++ and Python bindings

---

## 🎯 **Overview**

This guide covers developing Qt frontend applications that integrate with ImaLink's hybrid storage architecture. The frontend enables users to manage photos while leveraging ImaLink's revolutionary combination of database-powered organization and user-controlled file structures.

---

## 🏗️ **Architecture Integration**

### **Qt Frontend ↔ ImaLink Backend**

```
┌─────────────────────────────────────┐
│           Qt Frontend               │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ FileStorage │  │ ImportSession│   │
│  │ Management  │  │ Processing  │   │
│  │             │  │             │   │
│  │ File System │  │ HTTP Client │   │
│  │ Browser     │  │ API Layer   │   │
│  └─────────────┘  └─────────────┘   │
└─────────────┬───────────┬───────────┘
              │           │
              │      HTTP/REST API
              │    (Metadata Only)
              │           │
┌─────────────▼───────────▼───────────┐
│         ImaLink Backend             │
│  ┌──────────────┐ ┌──────────────┐  │
│  │ FileStorage  │ │ ImportSession│  │
│  │ Metadata     │ │ Metadata     │  │
│  │ Storage      │ │ Storage      │  │
│  └──────────────┘ └──────────────┘  │
└─────────────────────────────────────┘
```

### **Key Integration Points**

1. **FileStorage Management**: Qt handles creation, scanning, and monitoring of storage directories
2. **File System Operations**: Qt's `QFileDialog`, `QDir`, `QFileInfo` for complete file management
3. **ImportSession Processing**: Frontend handles file scanning, copying, and organization
4. **HTTP Communication**: `QNetworkAccessManager` for sending metadata to backend
5. **JSON Index Generation**: Frontend creates and maintains JSON indexes locally
6. **Backend Integration**: Send only metadata and references to backend database

---

## 📚 **Qt Components Overview**

### **Core Qt Classes for ImaLink Integration**

#### **1. File System Management**
```cpp
// Qt Classes for File Operations
QFileDialog          // Storage path selection
QDir                 // Directory operations and scanning
QFileInfo            // File metadata extraction
QFileSystemWatcher   // Monitor for external file changes
QStorageInfo         // Disk space and accessibility checking
```

#### **2. Network Communication**
```cpp
// Qt Classes for Backend Integration  
QNetworkAccessManager // HTTP client for API calls
QNetworkRequest       // HTTP request configuration
QNetworkReply         // API response handling
QJsonDocument         // JSON parsing and generation
QJsonObject/Array     // JSON data structures
```

#### **3. UI Components**
```cpp
// Qt Widgets for ImaLink UI
QTreeView            // FileStorage and ImportSession hierarchy
QListWidget          // Photo thumbnail display
QProgressBar         // Import and scanning progress
QFileSystemModel     // File browser integration
QTabWidget           // Multi-storage management
```

---

## 🔌 **Backend API Integration**

### **HTTP Client Service Class**

```cpp
// ImaLinkApiClient.h
#pragma once
#include <QObject>
#include <QNetworkAccessManager>
#include <QJsonObject>
#include <QJsonDocument>

class ImaLinkApiClient : public QObject
{
    Q_OBJECT

public:
    explicit ImaLinkApiClient(const QString& baseUrl = "http://localhost:8000/api/v1", 
                             QObject *parent = nullptr);
    
    // FileStorage Metadata (Frontend creates directories, backend stores metadata)
    void registerFileStorage(const QString& storageUuid, const QString& basePath, 
                            const QString& displayName, const QString& description = QString());
    void getFileStorageMetadata();
    void updateFileStorageMetadata(const QString& storageUuid, const QJsonObject& metadata);
    void deleteFileStorageRecord(const QString& storageUuid);
    
    // ImportSession Metadata (Frontend processes files, backend stores session info)
    void registerImportSession(const QString& sessionUuid, const QString& title, 
                              const QString& description, const QString& storageUuid, 
                              int fileCount, qint64 totalSize, int defaultAuthorId = -1);
    void getImportSessionMetadata();
    void updateImportSessionStatus(const QString& sessionUuid, const QString& status);
    
    // Photo Metadata (Frontend indexes files, backend provides photo info)
    void uploadPhotoMetadata(const QString& hothash, const QJsonObject& metadata);
    void getPhotosBySession(const QString& sessionUuid);
    void getPhotosByStorage(const QString& storageUuid);
    void searchPhotos(const QJsonObject& searchCriteria);

signals:
    // FileStorage Metadata Signals
    void fileStorageRegistered(const QJsonObject& storageMetadata);
    void fileStorageMetadataReceived(const QJsonArray& storages);
    void fileStorageUpdated(const QString& storageUuid, const QJsonObject& metadata);
    
    // ImportSession Metadata Signals
    void importSessionRegistered(const QJsonObject& sessionMetadata);
    void importSessionMetadataReceived(const QJsonArray& sessions);
    
    // Photo Metadata Signals
    void photoMetadataUploaded(const QString& hothash, const QJsonObject& result);
    void photosReceived(const QJsonArray& photos);
    void photoSearchResults(const QJsonArray& results);
    
    // Error Signals
    void apiError(const QString& operation, const QString& error);

private slots:
    void onNetworkReply();

private:
    QNetworkAccessManager* m_networkManager;
    QString m_baseUrl;
    
    void sendRequest(const QString& method, const QString& endpoint, 
                    const QJsonObject& data = QJsonObject());
};
```

### **Implementation Example**

```cpp
// ImaLinkApiClient.cpp
#include "ImaLinkApiClient.h"
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonDocument>

ImaLinkApiClient::ImaLinkApiClient(const QString& baseUrl, QObject *parent)
    : QObject(parent)
    , m_networkManager(new QNetworkAccessManager(this))
    , m_baseUrl(baseUrl)
{
    connect(m_networkManager, &QNetworkAccessManager::finished,
            this, &ImaLinkApiClient::onNetworkReply);
}

void ImaLinkApiClient::registerFileStorage(const QString& storageUuid,
                                          const QString& basePath, 
                                          const QString& displayName,
                                          const QString& description)
{
    QJsonObject data;
    data["storage_uuid"] = storageUuid;
    data["base_path"] = basePath;
    data["display_name"] = displayName;
    if (!description.isEmpty()) {
        data["description"] = description;
    }
    
    sendRequest("POST", "/file-storage/register", data);
}

void ImaLinkApiClient::sendRequest(const QString& method, const QString& endpoint,
                                  const QJsonObject& data)
{
    QUrl url(m_baseUrl + endpoint);
    QNetworkRequest request(url);
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    
    QJsonDocument doc(data);
    QByteArray jsonData = doc.toJson();
    
    QNetworkReply* reply = nullptr;
    if (method == "POST") {
        reply = m_networkManager->post(request, jsonData);
    } else if (method == "GET") {
        reply = m_networkManager->get(request);
    } else if (method == "PUT") {
        reply = m_networkManager->put(request, jsonData);
    }
    
    // Store operation context in reply for handling
    reply->setProperty("operation", endpoint);
}

void ImaLinkApiClient::onNetworkReply()
{
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    if (!reply) return;
    
    QString operation = reply->property("operation").toString();
    
    if (reply->error() != QNetworkReply::NoError) {
        emit apiError(operation, reply->errorString());
        reply->deleteLater();
        return;
    }
    
    QJsonDocument doc = QJsonDocument::fromJson(reply->readAll());
    QJsonObject response = doc.object();
    
    // Handle different API responses
    if (operation == "/file-storage/register") {
        emit fileStorageRegistered(response["data"].toObject());
    } else if (operation == "/file-storage/metadata") {
        emit fileStorageMetadataReceived(response["data"].toObject()["storages"].toArray());
    } else if (operation.startsWith("/import-sessions/register")) {
        emit importSessionRegistered(response["data"].toObject());
    }
    // ... handle other operations
    
    reply->deleteLater();
}
```

---

## 🖼️ **Main Window Implementation**

### **Primary Application Window**

```cpp
// MainWindow.h
#pragma once
#include <QMainWindow>
#include <QTabWidget>
#include <QTreeView>
#include <QListWidget>
#include <QProgressBar>
#include <QLabel>
#include "ImaLinkApiClient.h"
#include "StorageManagerWidget.h"
#include "ImportSessionWidget.h"
#include "PhotoBrowserWidget.h"

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    // Storage Management
    void onStorageCreated(const QJsonObject& storage);
    void onStorageAccessibilityChanged(const QString& uuid, bool accessible);
    
    // Import Sessions
    void onImportSessionCreated(const QJsonObject& session);
    void onImportProgressUpdated(int sessionId, int progress);
    
    // File Operations
    void onFileSystemChanged(const QString& path);
    void refreshStorageStatus();

private:
    void setupUI();
    void setupConnections();
    void loadInitialData();
    
    // UI Components
    QTabWidget* m_tabWidget;
    StorageManagerWidget* m_storageManager;
    ImportSessionWidget* m_importManager;  
    PhotoBrowserWidget* m_photoBrowser;
    QProgressBar* m_statusProgress;
    QLabel* m_statusLabel;
    
    // Backend Integration
    ImaLinkApiClient* m_apiClient;
    QTimer* m_refreshTimer;
};
```

### **Storage Manager Widget**

```cpp
// StorageManagerWidget.h  
#pragma once
#include <QWidget>
#include <QTreeView>
#include <QPushButton>
#include <QProgressBar>
#include <QLabel>
#include <QFileSystemModel>
#include "ImaLinkApiClient.h"

class StorageManagerWidget : public QWidget
{
    Q_OBJECT

public:
    explicit StorageManagerWidget(ImaLinkApiClient* apiClient, QWidget *parent = nullptr);

public slots:
    void refreshStorageMetadata();
    void createNewStorage();
    void scanStorageForChanges();
    void generateLocalIndexes();
    void syncWithBackend();

private slots:
    void onStorageSelectionChanged();
    void onStorageDirectoryCreated(const QString& uuid, const QString& path);
    void onLocalScanCompleted(const QString& uuid, const QJsonObject& changes);
    void onIndexGenerationComplete(const QString& uuid);

signals:
    void storageSelected(const QString& storageUuid);
    void storageCreated(const QString& storageUuid, const QString& path);
    void scanProgressUpdated(int progress);
    void indexGenerationProgress(int progress);
    void syncCompleted(const QString& storageUuid);

private:
    void setupUI();
    void setupStorageTree();
    void updateStorageStatus(const QJsonObject& storage);
    
    ImaLinkApiClient* m_apiClient;
    
    // UI Components
    QTreeView* m_storageTree;
    QPushButton* m_createButton;
    QPushButton* m_scanButton;  
    QPushButton* m_generateIndexButton;
    QPushButton* m_syncButton;
    QProgressBar* m_scanProgress;
    QProgressBar* m_indexProgress;
    QLabel* m_statusLabel;
    
    // Data Models and State
    QStandardItemModel* m_storageModel;
    QString m_selectedStorageUuid;
    QFileSystemWatcher* m_storageWatcher;
};

// StorageManagerWidget.cpp
StorageManagerWidget::StorageManagerWidget(ImaLinkApiClient* apiClient, QWidget *parent)
    : QWidget(parent)
    , m_apiClient(apiClient)
    , m_storageWatcher(new QFileSystemWatcher(this))
{
    setupUI();
    
    // Connect API signals for metadata operations
    connect(m_apiClient, &ImaLinkApiClient::fileStorageMetadataReceived,
            this, &StorageManagerWidget::onStorageMetadataReceived);
    connect(m_apiClient, &ImaLinkApiClient::fileStorageRegistered,
            this, &StorageManagerWidget::onStorageRegistered);
    
    // Connect file system watcher for local changes
    connect(m_storageWatcher, &QFileSystemWatcher::directoryChanged,
            this, &StorageManagerWidget::onDirectoryChanged);
    
    // Load initial metadata
    refreshStorageMetadata();
}

void StorageManagerWidget::createNewStorage()
{
    // Open dialog to select base path
    QString basePath = QFileDialog::getExistingDirectory(
        this, 
        tr("Select Storage Base Directory"),
        QDir::homePath(),
        QFileDialog::ShowDirsOnly | QFileDialog::DontResolveSymlinks
    );
    
    if (!basePath.isEmpty()) {
        // Get display name from user
        bool ok;
        QString displayName = QInputDialog::getText(
            this,
            tr("Storage Name"),
            tr("Enter display name for this storage:"),
            QLineEdit::Normal,
            QDir(basePath).dirName(),
            &ok
        );
        
        if (ok && !displayName.isEmpty()) {
            // Generate UUID for storage
            QString storageUuid = QUuid::createUuid().toString(QUuid::WithoutBraces);
            
            // Create physical directory structure
            createStorageDirectory(basePath, storageUuid);
            
            // Register with backend (metadata only)
            m_apiClient->registerFileStorage(storageUuid, basePath, displayName);
        }
    }
}

void StorageManagerWidget::scanStorageForChanges()
{
    if (m_selectedStorageUuid.isEmpty()) {
        QMessageBox::information(this, tr("No Selection"), 
                                tr("Please select a storage to scan."));
        return;
    }
    
    m_scanProgress->setVisible(true);
    m_scanProgress->setValue(0);
    m_statusLabel->setText(tr("Scanning storage for changes..."));
    
    // Perform local file system scan (frontend responsibility)
    performLocalStorageScan(m_selectedStorageUuid);
}

void StorageManagerWidget::performLocalStorageScan(const QString& storageUuid)
{
    // Get storage path from model
    QString storagePath = getStoragePath(storageUuid);
    if (storagePath.isEmpty()) return;
    
    // Scan directory structure
    QDir storageDir(storagePath);
    scanDirectoryRecursively(storageDir);
    
    // Generate/update JSON indexes
    generateLocalIndexes();
    
    // Sync changes with backend
    syncWithBackend();
}
```

---

## � **Frontend-Backend Responsibility Matrix**

### **Frontend Responsibilities (Qt Application)**

| **Operation** | **Frontend Action** | **Backend Interaction** |
|---------------|---------------------|-------------------------|
| **Storage Creation** | Create directory structure with UUID naming | Register metadata only |
| **File Import** | Copy files, organize structure, generate hashes | Upload file metadata records |
| **Index Generation** | Create JSON indexes locally | No backend involvement |
| **File Scanning** | Scan directories, detect changes | Sync metadata updates |
| **Photo Processing** | Extract EXIF, generate hotpreviews | Store photo metadata |
| **Directory Reorganization** | Move/rename files freely | Update file paths in metadata |

### **API Endpoints (Metadata Operations Only)**

```http
# FileStorage Metadata Management
POST   /api/v1/file-storage/register          # Register new storage metadata
GET    /api/v1/file-storage/metadata          # Get all storage metadata
PUT    /api/v1/file-storage/{uuid}/metadata   # Update storage metadata
DELETE /api/v1/file-storage/{uuid}            # Remove storage record

# ImportSession Metadata Management  
POST   /api/v1/import-sessions/register        # Register session metadata
GET    /api/v1/import-sessions/metadata        # Get session metadata
PUT    /api/v1/import-sessions/{uuid}/status   # Update session status

# Photo Metadata Management
POST   /api/v1/photos/metadata                 # Upload photo metadata batch
GET    /api/v1/photos/by-session/{uuid}       # Get photos by session
GET    /api/v1/photos/by-storage/{uuid}       # Get photos by storage
POST   /api/v1/photos/search                  # Search photos by criteria
```

### **Local File Operations (No Backend Interaction)**

```cpp
// Directory Structure Creation
void createStorageStructure(const QString& basePath, const QString& uuid) {
    QDir baseDir(basePath);
    QString storageName = QString("imalink_%1").arg(uuid);
    
    // Create main directories
    baseDir.mkdir(storageName);
    QDir storageDir(baseDir.filePath(storageName));
    storageDir.mkdir("imports");
    storageDir.mkdir("photos"); 
    storageDir.mkdir(".imalink");
    storageDir.mkdir(".imalink/hotpreviews");
    
    // Create index files
    QJsonObject masterIndex;
    masterIndex["storage_uuid"] = uuid;
    masterIndex["created_at"] = QDateTime::currentDateTime().toString(Qt::ISODate);
    masterIndex["import_sessions"] = QJsonArray();
    
    QFile indexFile(storageDir.filePath("index.json"));
    indexFile.open(QIODevice::WriteOnly);
    indexFile.write(QJsonDocument(masterIndex).toJson());
}

// File Import Processing
void ImportSessionWidget::processImportBatch() {
    QString sessionUuid = QUuid::createUuid().toString(QUuid::WithoutBraces);
    m_currentSessionUuid = sessionUuid;
    
    // Create session directory
    QString sessionDir = getSessionDirectory(sessionUuid);
    QDir().mkpath(sessionDir);
    
    // Copy files with progress tracking
    for (const QString& sourceFile : m_imageFiles) {
        QString targetFile = generateTargetPath(sourceFile, sessionDir);
        copyFileWithProgress(sourceFile, targetFile);
        
        // Generate hothash and extract metadata
        QString hothash = generateHothash(targetFile);
        QJsonObject metadata = extractFileMetadata(targetFile);
        
        emit fileCopyCompleted(sourceFile, targetFile);
    }
    
    // Generate session index locally
    generateSessionIndex();
    
    // Register with backend (metadata only)
    registerWithBackend();
}
```

---

## �📁 **File System Integration**

### **Directory Browser with Storage Awareness**

```cpp
// FileSystemBrowser.h
#pragma once
#include <QWidget>
#include <QTreeView>
#include <QFileSystemModel>
#include <QFileInfo>
#include <QDir>

class FileSystemBrowser : public QWidget
{
    Q_OBJECT

public:
    explicit FileSystemBrowser(QWidget *parent = nullptr);
    
    void setStorageRoot(const QString& path);
    void highlightImportSession(int sessionId);

public slots:
    void refreshView();
    void navigateToPath(const QString& path);

signals:
    void fileSelected(const QString& filePath);
    void directoryChanged(const QString& newPath);
    void importSessionDetected(const QString& sessionPath);

private slots:
    void onItemDoubleClicked(const QModelIndex& index);
    void onSelectionChanged(const QItemSelection& selected);

private:
    void setupUI();
    void detectImaLinkStructure(const QString& path);
    bool isImaLinkStorage(const QString& path);
    
    QTreeView* m_fileTree;
    QFileSystemModel* m_fileModel;
    QString m_currentStorageRoot;
    QStringList m_sessionDirectories;
};

// Implementation highlights
bool FileSystemBrowser::isImaLinkStorage(const QString& path)
{
    QDir dir(path);
    
    // Check for ImaLink storage structure
    if (dir.dirName().startsWith("imalink_")) {
        // Check for required subdirectories
        return dir.exists("imports") && 
               dir.exists("photos") && 
               dir.exists(".imalink") &&
               QFile::exists(dir.filePath("index.json"));
    }
    
    return false;
}

void FileSystemBrowser::detectImaLinkStructure(const QString& path)
{
    QDir dir(path);
    
    if (isImaLinkStorage(path)) {
        // Found ImaLink storage, scan for session indexes
        QDir importsDir(dir.filePath("imports"));
        QStringList sessionFiles = importsDir.entryList(
            QStringList() << "session_*.json", 
            QDir::Files
        );
        
        m_sessionDirectories.clear();
        for (const QString& sessionFile : sessionFiles) {
            // Extract session ID and add to tracking
            QString sessionId = sessionFile.mid(8, sessionFile.length() - 13); // Remove "session_" and ".json"
            m_sessionDirectories.append(sessionId);
        }
        
        emit importSessionDetected(path);
    }
}
```

---

## 🔄 **Import Workflow Implementation**

### **Import Session Manager**

```cpp
// ImportSessionWidget.h
#pragma once
#include <QWidget>
#include <QWizard>
#include <QLabel>
#include <QLineEdit>
#include <QTextEdit>
#include <QComboBox>
#include <QProgressBar>
#include <QListWidget>

class ImportSessionWidget : public QWidget
{
    Q_OBJECT

public:
    explicit ImportSessionWidget(ImaLinkApiClient* apiClient, QWidget *parent = nullptr);

public slots:
    void startNewImport();
    void selectSourceDirectory();
    void processImportBatch();
    void copyFilesToStorage();
    void generateSessionIndex();
    void registerWithBackend();

signals:
    void importCompleted(const QString& sessionUuid);
    void importProgressUpdated(int progress);
    void fileCopyCompleted(const QString& sourceFile, const QString& targetFile);
    void sessionIndexGenerated(const QString& sessionUuid);

private:
    void setupUI();
    void validateImportSettings();
    void scanSourceDirectory();
    
    ImaLinkApiClient* m_apiClient;
    
    // UI Components
    QLineEdit* m_titleEdit;
    QTextEdit* m_descriptionEdit;
    QComboBox* m_storageCombo;
    QComboBox* m_authorCombo;
    QLabel* m_sourcePath;
    QListWidget* m_fileList;
    QProgressBar* m_importProgress;
    QPushButton* m_startButton;
    
    // Import State
    QString m_selectedSourcePath;
    QStringList m_imageFiles;
    QString m_selectedStorageUuid;
    QString m_currentSessionUuid;
    int m_selectedAuthorId;
    
    // File Processing
    QThread* m_importThread;
    QTimer* m_progressTimer;
};

// Import Wizard Implementation
class ImportWizard : public QWizard
{
    Q_OBJECT

public:
    explicit ImportWizard(ImaLinkApiClient* apiClient, QWidget *parent = nullptr);

private:
    enum PageId {
        SourceSelectionPage,
        StorageSelectionPage,
        MetadataPage,
        ProcessingPage,
        CompletionPage
    };
    
    ImaLinkApiClient* m_apiClient;
};

// Source Selection Page
class SourceSelectionPage : public QWizardPage
{
    Q_OBJECT

public:
    explicit SourceSelectionPage(QWidget *parent = nullptr);
    
    bool validatePage() override;
    QString selectedPath() const { return m_pathEdit->text(); }

private slots:
    void browseForDirectory();
    void scanDirectory();

private:
    QLineEdit* m_pathEdit;
    QPushButton* m_browseButton;
    QLabel* m_fileCountLabel;
    QListWidget* m_previewList;
    
    QStringList m_foundFiles;
};

void SourceSelectionPage::browseForDirectory()
{
    QString path = QFileDialog::getExistingDirectory(
        this,
        tr("Select Source Directory"),
        m_pathEdit->text().isEmpty() ? QDir::homePath() : m_pathEdit->text(),
        QFileDialog::ShowDirsOnly
    );
    
    if (!path.isEmpty()) {
        m_pathEdit->setText(path);
        scanDirectory();
    }
}

void SourceSelectionPage::scanDirectory()
{
    QString path = m_pathEdit->text();
    if (path.isEmpty()) return;
    
    QDir dir(path);
    QStringList imageExtensions = {"*.jpg", "*.jpeg", "*.cr2", "*.nef", "*.arw", "*.dng", "*.png", "*.tiff"};
    
    m_foundFiles = dir.entryList(imageExtensions, QDir::Files);
    
    m_fileCountLabel->setText(tr("Found %1 image files").arg(m_foundFiles.count()));
    
    // Show preview of first 10 files
    m_previewList->clear();
    for (int i = 0; i < qMin(10, m_foundFiles.count()); ++i) {
        QListWidgetItem* item = new QListWidgetItem(m_foundFiles.at(i));
        m_previewList->addItem(item);
    }
    
    if (m_foundFiles.count() > 10) {
        QListWidgetItem* moreItem = new QListWidgetItem(tr("... and %1 more files").arg(m_foundFiles.count() - 10));
        moreItem->setFlags(Qt::NoItemFlags);
        m_previewList->addItem(moreItem);
    }
}
```

---

## 🖼️ **Photo Browser Integration**

### **Thumbnail View with Hotpreview Support**

```cpp
// PhotoBrowserWidget.h
#pragma once
#include <QWidget>
#include <QListWidget>
#include <QLabel>
#include <QScrollArea>
#include <QNetworkAccessManager>
#include <QPixmap>

class PhotoBrowserWidget : public QWidget
{
    Q_OBJECT

public:
    explicit PhotoBrowserWidget(ImaLinkApiClient* apiClient, QWidget *parent = nullptr);
    
    void setImportSession(int sessionId);
    void setStorageLocation(const QString& storageUuid);

public slots:
    void refreshPhotos();
    void showPhotoDetails(const QString& hothash);

signals:
    void photoSelected(const QString& hothash);
    void photoDoubleClicked(const QString& filePath);

private slots:
    void onThumbnailClicked(QListWidgetItem* item);
    void onThumbnailLoaded();

private:
    void setupUI();
    void loadThumbnails();
    void loadHotpreview(const QString& hothash, QListWidgetItem* item);
    
    ImaLinkApiClient* m_apiClient;
    QNetworkAccessManager* m_thumbnailLoader;
    
    // UI Components
    QListWidget* m_photoGrid;
    QLabel* m_photoDetails;
    QScrollArea* m_detailsArea;
    
    // Current State
    int m_currentSessionId;
    QString m_currentStorageUuid;
    QJsonArray m_currentPhotos;
};

// Thumbnail Loading Implementation
void PhotoBrowserWidget::loadHotpreview(const QString& hothash, QListWidgetItem* item)
{
    // Construct hotpreview URL based on storage structure
    // Format: {storage_root}/.imalink/hotpreviews/{hash[0:2]}/{hash[2:4]}/{hash}.jpg
    QString previewPath = QString("/.imalink/hotpreviews/%1/%2/%3.jpg")
        .arg(hothash.left(2))
        .arg(hothash.mid(2, 2))  
        .arg(hothash);
    
    // For local files, load directly
    QPixmap thumbnail;
    if (thumbnail.load(m_currentStorageRoot + previewPath)) {
        item->setIcon(QIcon(thumbnail.scaled(200, 200, Qt::KeepAspectRatio, Qt::SmoothTransformation)));
    } else {
        // Fallback to generic image icon
        item->setIcon(style()->standardIcon(QStyle::SP_FileIcon));
    }
}
```

---

## ⚙️ **Configuration and Settings**

### **Application Settings Management**

```cpp
// SettingsManager.h
#pragma once
#include <QObject>
#include <QSettings>
#include <QString>

class SettingsManager : public QObject
{
    Q_OBJECT

public:
    static SettingsManager* instance();
    
    // API Configuration
    QString apiBaseUrl() const;
    void setApiBaseUrl(const QString& url);
    
    QString apiToken() const;
    void setApiToken(const QString& token);
    
    // Storage Preferences
    QString defaultStoragePath() const;
    void setDefaultStoragePath(const QString& path);
    
    QStringList recentStorages() const;
    void addRecentStorage(const QString& storageUuid, const QString& displayName);
    
    // UI Preferences
    int thumbnailSize() const;
    void setThumbnailSize(int size);
    
    bool autoScanOnStartup() const;
    void setAutoScanOnStartup(bool enabled);
    
    // Import Preferences
    QString lastImportDirectory() const;
    void setLastImportDirectory(const QString& path);
    
    int defaultAuthorId() const;
    void setDefaultAuthorId(int authorId);

signals:
    void settingsChanged();

private:
    explicit SettingsManager(QObject *parent = nullptr);
    QSettings* m_settings;
    
    static SettingsManager* s_instance;
};

// Settings Dialog
class SettingsDialog : public QDialog
{
    Q_OBJECT

public:
    explicit SettingsDialog(QWidget *parent = nullptr);

private slots:
    void onApiUrlChanged();
    void onStoragePathBrowse();
    void saveSettings();
    void resetToDefaults();

private:
    void setupUI();
    void loadCurrentSettings();
    
    // UI Components
    QLineEdit* m_apiUrlEdit;
    QLineEdit* m_apiTokenEdit;
    QLineEdit* m_storagePathEdit;
    QSpinBox* m_thumbnailSizeSpin;
    QCheckBox* m_autoScanCheck;
};
```

---

## 🔍 **Monitoring and Status**

### **Storage Health Monitor**

```cpp
// StorageHealthMonitor.h
#pragma once
#include <QObject>
#include <QTimer>
#include <QJsonObject>
#include <QJsonArray>

class StorageHealthMonitor : public QObject
{
    Q_OBJECT

public:
    explicit StorageHealthMonitor(ImaLinkApiClient* apiClient, QObject *parent = nullptr);
    
    void startMonitoring(int intervalMs = 30000); // Default 30 seconds
    void stopMonitoring();
    
    void checkStorageHealth(const QString& storageUuid);
    void checkAllStorages();

signals:
    void storageHealthChanged(const QString& storageUuid, bool healthy);
    void storageAccessibilityChanged(const QString& storageUuid, bool accessible);  
    void lowDiskSpace(const QString& storageUuid, qint64 freeBytes);
    void indexIntegrityIssue(const QString& storageUuid, const QStringList& issues);

private slots:
    void performHealthCheck();
    void onHealthCheckResult(const QString& storageUuid, const QJsonObject& status);

private:
    ImaLinkApiClient* m_apiClient;
    QTimer* m_healthCheckTimer;
    QStringList m_monitoredStorages;
    
    void analyzeStorageStatus(const QJsonObject& status);
    void checkDiskSpace(const QString& storageUuid);
    void verifyIndexIntegrity(const QString& storageUuid);
};

// Status Bar Widget  
class StatusBarWidget : public QWidget
{
    Q_OBJECT

public:
    explicit StatusBarWidget(QWidget *parent = nullptr);
    
    void setStorageStatus(const QString& storageUuid, const QString& status);
    void setConnectionStatus(bool connected);
    void showProgressIndicator(const QString& operation, int progress = -1);
    void hideProgressIndicator();

private:
    void setupUI();
    
    QLabel* m_connectionLabel;
    QLabel* m_storageLabel;
    QProgressBar* m_progressBar;
    QLabel* m_operationLabel;
};
```

---

## 🧪 **Testing and Debugging**

### **Mock API Client for Development**

```cpp
// MockApiClient.h (for development/testing)
#pragma once
#include "ImaLinkApiClient.h"
#include <QTimer>

class MockApiClient : public ImaLinkApiClient
{
    Q_OBJECT

public:
    explicit MockApiClient(QObject *parent = nullptr);
    
    // Override API methods with mock responses
    void createFileStorage(const QString& basePath, const QString& displayName, 
                          const QString& description = QString()) override;
    void getFileStorages() override;
    void generateAllIndexes(const QString& storageUuid) override;

private slots:
    void emitMockResponse();

private:
    void scheduleMockResponse(const QString& operation, const QJsonObject& data);
    
    QTimer* m_mockTimer;
    QString m_pendingOperation;
    QJsonObject m_pendingData;
    
    // Mock data generators
    QJsonObject generateMockStorage(const QString& basePath, const QString& displayName);
    QJsonArray generateMockStorageList();
    QJsonObject generateMockSession(int id, const QString& title);
};

// Debug Console for API Testing
class ApiDebugConsole : public QWidget
{
    Q_OBJECT

public:
    explicit ApiDebugConsole(ImaLinkApiClient* apiClient, QWidget *parent = nullptr);

private slots:
    void sendCustomRequest();
    void onApiResponse(const QString& operation, const QJsonObject& response);
    void onApiError(const QString& operation, const QString& error);

private:
    void setupUI();
    void addLogEntry(const QString& type, const QString& message);
    
    ImaLinkApiClient* m_apiClient;
    
    QLineEdit* m_endpointEdit;
    QComboBox* m_methodCombo;
    QTextEdit* m_requestBody;
    QPushButton* m_sendButton;
    QTextEdit* m_responseLog;
};
```

---

## 📚 **Deployment and Distribution**

### **CMake Configuration**

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.20)
project(ImaLinkQt)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Widgets Network)

# Enable automatic MOC, UIC, and RCC
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON) 
set(CMAKE_AUTORCC ON)

# Source files
set(SOURCES
    src/main.cpp
    src/MainWindow.cpp
    src/ImaLinkApiClient.cpp
    src/StorageManagerWidget.cpp
    src/ImportSessionWidget.cpp
    src/PhotoBrowserWidget.cpp
    src/FileSystemBrowser.cpp
    src/SettingsManager.cpp
    src/StorageHealthMonitor.cpp
    src/StatusBarWidget.cpp
)

set(HEADERS
    src/MainWindow.h
    src/ImaLinkApiClient.h
    src/StorageManagerWidget.h
    src/ImportSessionWidget.h
    src/PhotoBrowserWidget.h
    src/FileSystemBrowser.h
    src/SettingsManager.h
    src/StorageHealthMonitor.h
    src/StatusBarWidget.h
)

# Create executable
add_executable(ImaLinkQt ${SOURCES} ${HEADERS})

# Link Qt libraries
target_link_libraries(ImaLinkQt Qt6::Core Qt6::Widgets Qt6::Network)

# Platform-specific configurations
if(WIN32)
    set_property(TARGET ImaLinkQt PROPERTY WIN32_EXECUTABLE TRUE)
endif()

# Install configuration
install(TARGETS ImaLinkQt
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
```

### **Application Packaging**

```bash
#!/bin/bash
# build_release.sh - Build and package ImaLink Qt application

set -e

BUILD_DIR="build_release"
INSTALL_DIR="ImaLinkQt_Install"

# Clean previous builds
rm -rf "$BUILD_DIR" "$INSTALL_DIR"

# Create build directory
mkdir "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_INSTALL_PREFIX="../$INSTALL_DIR"

# Build
make -j$(nproc)

# Install
make install

cd ..

# Create application bundle (macOS) or installer (Windows/Linux)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS App Bundle
    macdeployqt "$INSTALL_DIR/ImaLinkQt.app" -dmg
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows Installer
    windeployqt "$INSTALL_DIR/bin/ImaLinkQt.exe"
else
    # Linux AppImage
    linuxdeploy --appdir "$INSTALL_DIR" \
               --executable "$INSTALL_DIR/bin/ImaLinkQt" \
               --desktop-file resources/ImaLinkQt.desktop \
               --icon-file resources/imalink.png \
               --output appimage
fi

echo "Build completed successfully!"
```

---

## 🔧 **Configuration Examples**

### **Application Configuration File**

```ini
# imalink-qt.conf
[API]
base_url=http://localhost:8000/api/v1
timeout=30000
retry_attempts=3

[Storage]
default_base_path=/home/user/Photos
auto_scan_interval=300000
max_concurrent_operations=5

[UI]
thumbnail_size=200  
grid_columns=5
theme=system
language=auto

[Import]
default_author_id=1
auto_generate_titles=true
preserve_directory_structure=true
supported_formats=jpg,jpeg,cr2,nef,arw,dng,png,tiff

[Monitoring]
health_check_interval=30000
low_disk_warning_mb=1024
enable_notifications=true
```

### **Logging Configuration**

```cpp
// Logger.h
#pragma once
#include <QObject>
#include <QFile>
#include <QTextStream>
#include <QDateTime>

class Logger : public QObject
{
    Q_OBJECT

public:
    enum LogLevel {
        Debug,
        Info,
        Warning,
        Error,
        Critical
    };

    static Logger* instance();
    
    void log(LogLevel level, const QString& category, const QString& message);
    void setLogLevel(LogLevel minLevel);
    void setLogFile(const QString& filePath);

public slots:
    void debug(const QString& message) { log(Debug, "APP", message); }
    void info(const QString& message) { log(Info, "APP", message); }
    void warning(const QString& message) { log(Warning, "APP", message); }
    void error(const QString& message) { log(Error, "APP", message); }
    void critical(const QString& message) { log(Critical, "APP", message); }

private:
    explicit Logger(QObject *parent = nullptr);
    
    static Logger* s_instance;
    LogLevel m_minLevel;
    QFile* m_logFile;
    QTextStream* m_logStream;
};

// Usage throughout application:
// Logger::instance()->info("Application started");
// Logger::instance()->error("Failed to connect to API: " + error);
```

---

## 🚀 **Getting Started**

### **Quick Setup Checklist**

1. **Prerequisites**
   - [ ] Qt 6.x installed
   - [ ] CMake 3.20+
   - [ ] ImaLink backend running on `localhost:8000`
   - [ ] C++17 compatible compiler

2. **Project Setup**
   - [ ] Clone/create Qt project structure
   - [ ] Configure CMakeLists.txt with dependencies
   - [ ] Set up API client configuration
   - [ ] Configure logging and settings

3. **Basic Integration**
   - [ ] Implement ImaLinkApiClient class
   - [ ] Create main window with storage manager
   - [ ] Set up file system browser
   - [ ] Test API connectivity

4. **Advanced Features**
   - [ ] Implement import workflow wizard
   - [ ] Add photo browser with hotpreview support
   - [ ] Set up storage health monitoring
   - [ ] Create settings and configuration management

### **Development Workflow**

1. **Start Backend**: Ensure ImaLink backend is running
2. **Mock Development**: Use MockApiClient during UI development
3. **Integration Testing**: Test with real backend API
4. **User Testing**: Validate workflows with actual photo imports
5. **Performance Optimization**: Profile and optimize for large collections

---

## 📞 **Support and Resources**

### **Key Documentation Links**
- [Storage Architecture](../STORAGE_ARCHITECTURE.md) - Backend system design
- [Storage API Reference](../STORAGE_API.md) - Complete API documentation
- [Storage Workflows](../STORAGE_WORKFLOW.md) - Backend workflow examples

### **Qt Resources**
- [Qt6 Documentation](https://doc.qt.io/qt-6/)
- [QNetworkAccessManager](https://doc.qt.io/qt-6/qnetworkaccessmanager.html)
- [QFileSystemModel](https://doc.qt.io/qt-6/qfilesystemmodel.html)
- [QJsonDocument](https://doc.qt.io/qt-6/qjsondocument.html)

### **Best Practices**
- Always handle API errors gracefully with user feedback
- Implement progress indicators for long operations
- Use Qt's model/view architecture for data display
- Leverage Qt's threading for non-blocking operations
- Follow Qt coding conventions and naming patterns

---

*This guide enables developers to create powerful Qt applications that fully leverage ImaLink's hybrid storage architecture, providing users with intuitive photo management while maintaining the flexibility of the underlying system.*