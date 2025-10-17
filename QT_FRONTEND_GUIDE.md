# Qt Frontend Development Guide

Guide for developing Qt-based frontend for ImaLink.

## Architecture Overview

```
┌─────────────────┐         HTTP/REST        ┌──────────────────┐
│   Qt Frontend   │ ◄─────────────────────► │  FastAPI Backend │
│   (Windows)     │    JSON over HTTP        │     (WSL)        │
└─────────────────┘                          └──────────────────┘
        │                                              │
        │                                              │
    Qt Models                                    SQLite Database
    Qt Views                                     SQLAlchemy ORM
    QNetworkAccessManager                        Pydantic Schemas
```

## Technology Stack Recommendation

### Qt Version
- **Qt 6.x** (recommended) or Qt 5.15+
- **PyQt6** or **PySide6** for Python
- **Qt for Python** (official Python bindings)

### Key Qt Modules
- `QtWidgets` - Main UI components
- `QtNetwork` - HTTP client (QNetworkAccessManager)
- `QtCore` - Core functionality (QTimer, signals/slots)
- `QtGui` - Image handling (QPixmap, QImage)
- `QtConcurrent` - Background tasks

### Additional Python Packages
```
PySide6>=6.6.0
requests>=2.31.0  # Simpler than QtNetwork for REST
Pillow>=10.0.0    # Image processing
python-dateutil>=2.8.2  # Date parsing
```

## Project Structure

```
imalink-qt-frontend/
├── main.py                 # Application entry point
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/               # Backend communication
│   │   ├── __init__.py
│   │   ├── client.py      # Main API client
│   │   └── models.py      # Data models (dataclasses)
│   │
│   ├── ui/                # UI components
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── gallery_view.py
│   │   ├── import_dialog.py
│   │   ├── photo_detail.py
│   │   └── widgets/
│   │       ├── thumbnail.py
│   │       └── photo_card.py
│   │
│   ├── models/            # Qt models (MVC)
│   │   ├── __init__.py
│   │   ├── photo_model.py
│   │   └── image_model.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py
│       └── cache.py
│
└── resources/
    ├── icons/
    └── styles/
        └── main.qss       # Qt StyleSheet
```

## API Client Implementation

### Basic Client (src/api/client.py)

```python
import requests
from typing import List, Optional
from dataclasses import dataclass
import base64
from io import BytesIO
from PIL import Image

@dataclass
class Photo:
    """Photo data model matching API response"""
    id: int
    hothash: str
    title: Optional[str] = None
    description: Optional[str] = None
    author_id: Optional[int] = None
    rating: Optional[int] = None
    location: Optional[str] = None
    tags: List[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class ImaLinkClient:
    """HTTP client for ImaLink API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def get_photos(self, skip: int = 0, limit: int = 100) -> List[Photo]:
        """Get paginated list of photos"""
        response = self.session.get(
            f"{self.base_url}/photos/",
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()
        return [Photo(**item) for item in data["items"]]
    
    def get_photo(self, hothash: str) -> Photo:
        """Get single photo by hothash"""
        response = self.session.get(f"{self.base_url}/photos/{hothash}")
        response.raise_for_status()
        return Photo(**response.json())
    
    def get_photo_thumbnail(self, hothash: str) -> bytes:
        """Get photo thumbnail as JPEG bytes"""
        response = self.session.get(
            f"{self.base_url}/photos/{hothash}/hotpreview"
        )
        response.raise_for_status()
        return response.content
    
    def search_photos(self, title: str = None, tags: List[str] = None,
                     rating_min: int = None, rating_max: int = None) -> List[Photo]:
        """Search photos with filters"""
        payload = {}
        if title:
            payload["title"] = title
        if tags:
            payload["tags"] = tags
        if rating_min:
            payload["rating_min"] = rating_min
        if rating_max:
            payload["rating_max"] = rating_max
        
        response = self.session.post(
            f"{self.base_url}/photos/search",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return [Photo(**item) for item in data["items"]]
    
    def import_image(self, file_path: str, session_id: int = None) -> dict:
        """Import a single image file"""
        from pathlib import Path
        
        # Generate hotpreview (150x150 JPEG)
        img = Image.open(file_path)
        
        # Handle EXIF rotation
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except:
            pass
        
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        # Convert to JPEG bytes
        buffer = BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=85)
        hotpreview_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Get file info
        path = Path(file_path)
        payload = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "file_path": str(path.absolute()),
            "hotpreview": hotpreview_b64
        }
        
        if session_id:
            payload["import_session_id"] = session_id
        
        response = self.session.post(
            f"{self.base_url}/image-files/",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def find_similar_images(self, image_id: int, threshold: int = 5, limit: int = 10) -> List[dict]:
        """Find images similar to given image using perceptual hash
        
        Args:
            image_id: ID of the reference image
            threshold: Hamming distance threshold (0-16, lower = more similar)
            limit: Maximum number of results to return
            
        Returns:
            List of similar images sorted by similarity (most similar first)
        """
        response = self.session.get(
            f"{self.base_url}/image-files/similar/{image_id}",
            params={"threshold": threshold, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def upload_image_with_similarity_check(self, file_path: str, 
                                         check_duplicates: bool = True) -> dict:
        """Upload image and optionally check for similar existing images"""
        # First upload the image
        result = self.import_image(file_path)
        
        if check_duplicates:
            # Check for similar images after upload
            image_id = result["id"]
            similar = self.find_similar_images(image_id, threshold=3, limit=5)
            result["similar_images"] = similar
        
        return result
```

## Qt Main Window Example

### Main Window (src/ui/main_window.py)

```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QPushButton, QStatusBar, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

from .gallery_view import GalleryView
from .photo_detail import PhotoDetailPanel
from ..api.client import ImaLinkClient

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ImaLink Photo Manager")
        self.resize(1400, 900)
        
        # API client
        self.api = ImaLinkClient(base_url="http://172.x.x.x:8000/api/v1")
        
        self.setup_ui()
        self.setup_toolbar()
        self.setup_statusbar()
        
    def setup_ui(self):
        """Setup main UI layout"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        
        # Splitter: Gallery | Detail Panel
        splitter = QSplitter(Qt.Horizontal)
        
        # Gallery view
        self.gallery = GalleryView(self.api)
        self.gallery.photo_selected.connect(self.on_photo_selected)
        splitter.addWidget(self.gallery)
        
        # Detail panel
        self.detail_panel = PhotoDetailPanel(self.api)
        splitter.addWidget(self.detail_panel)
        
        splitter.setSizes([900, 500])
        
        layout.addWidget(splitter)
    
    def setup_toolbar(self):
        """Setup toolbar with actions"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Import action
        import_action = QAction("Import Images", self)
        import_action.triggered.connect(self.on_import_clicked)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.gallery.refresh)
        toolbar.addAction(refresh_action)
    
    def setup_statusbar(self):
        """Setup status bar"""
        self.statusBar().showMessage("Ready")
    
    def on_photo_selected(self, hothash: str):
        """Handle photo selection"""
        self.detail_panel.load_photo(hothash)
        self.statusBar().showMessage(f"Selected: {hothash[:16]}...")
    
    def on_import_clicked(self):
        """Show import dialog"""
        from .import_dialog import ImportDialog
        dialog = ImportDialog(self.api, self)
        if dialog.exec():
            self.gallery.refresh()
            self.statusBar().showMessage("Import completed")
```

## Qt Gallery View Example

### Gallery View (src/ui/gallery_view.py)

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGridLayout,
    QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap

class PhotoLoader(QThread):
    """Background thread for loading photos"""
    photos_loaded = Signal(list)
    
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
    
    def run(self):
        """Load photos in background"""
        try:
            photos = self.api.get_photos(limit=100)
            self.photos_loaded.emit(photos)
        except Exception as e:
            print(f"Error loading photos: {e}")

class ThumbnailWidget(QWidget):
    """Single photo thumbnail widget"""
    clicked = Signal(str)  # Emits hothash
    
    def __init__(self, photo, api_client):
        super().__init__()
        self.photo = photo
        self.api = api_client
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # Title
        title = photo.title or "Untitled"
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Load thumbnail
        self.load_thumbnail()
    
    def load_thumbnail(self):
        """Load thumbnail from API"""
        try:
            img_data = self.api.get_photo_thumbnail(self.photo.hothash)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            self.image_label.setPixmap(pixmap)
        except Exception as e:
            self.image_label.setText("Error")
            print(f"Error loading thumbnail: {e}")
    
    def mousePressEvent(self, event):
        """Handle click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo.hothash)

class GalleryView(QWidget):
    """Photo gallery grid view"""
    photo_selected = Signal(str)  # Emits hothash
    
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.photos = []
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)
    
    def refresh(self):
        """Reload photos from API"""
        self.loader = PhotoLoader(self.api)
        self.loader.photos_loaded.connect(self.display_photos)
        self.loader.start()
    
    def display_photos(self, photos):
        """Display photos in grid"""
        self.photos = photos
        
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add photos in grid (5 columns)
        columns = 5
        for idx, photo in enumerate(photos):
            row = idx // columns
            col = idx % columns
            
            thumbnail = ThumbnailWidget(photo, self.api)
            thumbnail.clicked.connect(self.photo_selected)
            self.grid_layout.addWidget(thumbnail, row, col)


## Image Similarity Search

### Duplicate Finder Widget
```python
class DuplicateFinderWidget(QWidget):
    """Widget for finding and managing duplicate images"""
    
    duplicates_found = Signal(list)
    
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Threshold slider
        controls_layout.addWidget(QLabel("Similarity Threshold:"))
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 16)
        self.threshold_slider.setValue(3)
        self.threshold_label = QLabel("3")
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(str(v))
        )
        controls_layout.addWidget(self.threshold_slider)
        controls_layout.addWidget(self.threshold_label)
        
        # Find button
        self.find_btn = QPushButton("Find Duplicates")
        self.find_btn.clicked.connect(self.find_all_duplicates)
        controls_layout.addWidget(self.find_btn)
        
        layout.addLayout(controls_layout)
        
        # Results area
        self.results_scroll = QScrollArea()
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_scroll.setWidget(self.results_widget)
        self.results_scroll.setWidgetResizable(True)
        layout.addWidget(self.results_scroll)
        
        # Status
        self.status_label = QLabel("Click 'Find Duplicates' to start")
        layout.addWidget(self.status_label)
    
    def find_all_duplicates(self):
        """Find all duplicate groups in the database"""
        self.find_btn.setEnabled(False)
        self.status_label.setText("Searching for duplicates...")
        
        # Start background task
        self.worker = DuplicateFinderWorker(
            self.api, 
            threshold=self.threshold_slider.value()
        )
        self.worker.duplicates_found.connect(self.display_duplicates)
        self.worker.finished.connect(lambda: self.find_btn.setEnabled(True))
        self.worker.start()
    
    def display_duplicates(self, duplicate_groups):
        """Display found duplicate groups"""
        # Clear existing results
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not duplicate_groups:
            self.status_label.setText("No duplicates found")
            return
        
        self.status_label.setText(f"Found {len(duplicate_groups)} duplicate groups")
        
        # Display each group
        for group_idx, group in enumerate(duplicate_groups):
            group_widget = DuplicateGroupWidget(group, self.api)
            self.results_layout.addWidget(group_widget)

class DuplicateFinderWorker(QThread):
    """Background worker for finding duplicates"""
    duplicates_found = Signal(list)
    
    def __init__(self, api_client, threshold=3):
        super().__init__()
        self.api = api_client
        self.threshold = threshold
    
    def run(self):
        try:
            # Get all images
            all_images = self.api.get_image_files(limit=10000)
            duplicate_groups = []
            processed_ids = set()
            
            for image in all_images:
                if image["id"] in processed_ids:
                    continue
                
                # Find similar images
                similar = self.api.find_similar_images(
                    image["id"], 
                    threshold=self.threshold,
                    limit=50
                )
                
                if similar:  # Found duplicates
                    group = [image] + similar
                    duplicate_groups.append(group)
                    
                    # Mark all as processed
                    for img in group:
                        processed_ids.add(img["id"])
            
            self.duplicates_found.emit(duplicate_groups)
            
        except Exception as e:
            print(f"Error finding duplicates: {e}")
            self.duplicates_found.emit([])

class DuplicateGroupWidget(QWidget):
    """Widget showing a group of duplicate images"""
    
    def __init__(self, image_group, api_client):
        super().__init__()
        self.images = image_group
        self.api = api_client
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Group header
        header = QLabel(f"Duplicate Group ({len(self.images)} images)")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        # Image thumbnails in horizontal layout
        thumbs_layout = QHBoxLayout()
        
        for image in self.images:
            thumb_widget = QWidget()
            thumb_layout = QVBoxLayout(thumb_widget)
            
            # Thumbnail (placeholder - implement with actual API call)
            thumb_label = QLabel("📷")
            thumb_label.setFixedSize(100, 100)
            thumb_label.setAlignment(Qt.AlignCenter)
            thumb_label.setStyleSheet("border: 1px solid #ccc;")
            thumb_layout.addWidget(thumb_label)
            
            # Image info
            info_text = f"{image['filename']}\n{image['file_size']} bytes"
            if image.get('perceptual_hash'):
                info_text += f"\npHash: {image['perceptual_hash'][:8]}..."
            
            info_label = QLabel(info_text)
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setWordWrap(True)
            thumb_layout.addWidget(info_label)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(
                lambda checked, img=image: self.delete_image(img)
            )
            thumb_layout.addWidget(delete_btn)
            
            thumbs_layout.addWidget(thumb_widget)
        
        layout.addLayout(thumbs_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
    
    def delete_image(self, image):
        """Delete an image from the duplicate group"""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Delete {image['filename']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete via photo API (cascade delete)
                self.api.delete_photo(image['photo_hothash'])
                
                # Remove from group and refresh UI
                self.images.remove(image)
                self.setup_ui()
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {e}")


### Find Similar Images Widget
```python
class SimilarImagesFinder(QWidget):
    """Widget for finding images similar to a selected image"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.reference_image_id = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Reference image selection
        ref_layout = QHBoxLayout()
        ref_layout.addWidget(QLabel("Reference Image ID:"))
        self.image_id_input = QLineEdit()
        self.image_id_input.setPlaceholderText("Enter image ID")
        ref_layout.addWidget(self.image_id_input)
        
        self.select_btn = QPushButton("Find Similar")
        self.select_btn.clicked.connect(self.find_similar)
        ref_layout.addWidget(self.select_btn)
        
        layout.addLayout(ref_layout)
        
        # Threshold control
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Similarity Threshold:"))
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 16)
        self.threshold_slider.setValue(5)
        self.threshold_label = QLabel("5")
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(str(v))
        )
        self.threshold_slider.valueChanged.connect(self.update_results)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        layout.addLayout(threshold_layout)
        
        # Results grid
        self.results_scroll = QScrollArea()
        self.results_widget = QWidget()
        self.results_grid = QGridLayout(self.results_widget)
        self.results_scroll.setWidget(self.results_widget)
        self.results_scroll.setWidgetResizable(True)
        layout.addWidget(self.results_scroll)
        
        # Status
        self.status_label = QLabel("Enter image ID and click 'Find Similar'")
        layout.addWidget(self.status_label)
    
    def set_reference_image(self, image_id: int):
        """Set reference image from external source (e.g., gallery click)"""
        self.reference_image_id = image_id
        self.image_id_input.setText(str(image_id))
        self.find_similar()
    
    def find_similar(self):
        """Find images similar to the reference image"""
        try:
            image_id = int(self.image_id_input.text())
        except ValueError:
            self.status_label.setText("Please enter a valid image ID")
            return
        
        self.reference_image_id = image_id
        self.update_results()
    
    def update_results(self):
        """Update results based on current threshold"""
        if not self.reference_image_id:
            return
        
        try:
            threshold = self.threshold_slider.value()
            similar_images = self.api.find_similar_images(
                self.reference_image_id,
                threshold=threshold,
                limit=20
            )
            
            self.display_results(similar_images)
            
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
    
    def display_results(self, images):
        """Display similar images in grid"""
        # Clear existing results
        while self.results_grid.count():
            item = self.results_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not images:
            self.status_label.setText("No similar images found")
            return
        
        self.status_label.setText(f"Found {len(images)} similar images")
        
        # Display in grid (4 columns)
        columns = 4
        for idx, image in enumerate(images):
            row = idx // columns
            col = idx % columns
            
            # Create thumbnail widget
            thumb_widget = self.create_thumbnail_widget(image)
            self.results_grid.addWidget(thumb_widget, row, col)
    
    def create_thumbnail_widget(self, image):
        """Create a thumbnail widget for an image"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        
        # Thumbnail placeholder
        thumb_label = QLabel("📷")
        thumb_label.setFixedSize(120, 120)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setStyleSheet("""
            border: 1px solid #ccc;
            background-color: #f5f5f5;
        """)
        layout.addWidget(thumb_label)
        
        # Image info
        info_text = f"ID: {image['id']}\n{image['filename']}"
        if image.get('perceptual_hash'):
            info_text += f"\npHash: {image['perceptual_hash'][:8]}..."
        
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(info_label)
        
        # Make clickable
        widget.mousePressEvent = lambda event: self.on_image_clicked(image)
        widget.setCursor(Qt.PointingHandCursor)
        
        return widget
    
    def on_image_clicked(self, image):
        """Handle image click - could open detail view"""
        print(f"Clicked image: {image['filename']}")
        # Implement: open image detail, set as new reference, etc.


### Integration with Main Gallery
```python
class EnhancedGalleryView(GalleryView):
    """Enhanced gallery with similarity search integration"""
    
    def __init__(self, api_client):
        super().__init__(api_client)
        self.similarity_finder = SimilarImagesFinder(api_client)
        
        # Add similarity finder as a dock widget or tab
        self.add_similarity_panel()
    
    def add_similarity_panel(self):
        """Add similarity search panel to the gallery"""
        # Create splitter for main gallery and similarity panel
        splitter = QSplitter(Qt.Horizontal)
        
        # Move existing gallery to left side
        gallery_widget = QWidget()
        gallery_layout = QVBoxLayout(gallery_widget)
        gallery_layout.addWidget(self)  # Move existing content
        splitter.addWidget(gallery_widget)
        
        # Add similarity finder to right side
        similarity_dock = QWidget()
        similarity_layout = QVBoxLayout(similarity_dock)
        similarity_layout.addWidget(QLabel("Find Similar Images"))
        similarity_layout.addWidget(self.similarity_finder)
        splitter.addWidget(similarity_dock)
        
        # Set initial sizes (70% gallery, 30% similarity)
        splitter.setSizes([700, 300])
    
    def on_thumbnail_right_click(self, image_id):
        """Handle right-click on thumbnail - show context menu"""
        menu = QMenu(self)
        
        find_similar_action = menu.addAction("Find Similar Images")
        find_similar_action.triggered.connect(
            lambda: self.similarity_finder.set_reference_image(image_id)
        )
        
        menu.exec_(QCursor.pos())
```
```

## Configuration Management

### Config File (config.json)

```json
{
  "api": {
    "base_url": "http://172.20.144.1:8000/api/v1",
    "timeout": 30
  },
  "ui": {
    "thumbnail_size": 150,
    "grid_columns": 5,
    "cache_size_mb": 100
  },
  "import": {
    "default_author_id": 1,
    "auto_archive": true
  }
}
```

### Config Loader (src/utils/config.py)

```python
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class AppConfig:
    api_base_url: str = "http://localhost:8000/api/v1"
    api_timeout: int = 30
    thumbnail_size: int = 150
    grid_columns: int = 5
    
    @classmethod
    def load(cls, config_file: str = "config.json"):
        """Load config from JSON file"""
        path = Path(config_file)
        if not path.exists():
            return cls()
        
        with open(path) as f:
            data = json.load(f)
        
        return cls(
            api_base_url=data["api"]["base_url"],
            api_timeout=data["api"]["timeout"],
            thumbnail_size=data["ui"]["thumbnail_size"],
            grid_columns=data["ui"]["grid_columns"]
        )
```

## Finding WSL IP Address

### Automatic WSL IP Discovery (Windows)

```python
import subprocess

def get_wsl_ip() -> str:
    """Get WSL IP address from Windows"""
    try:
        # Run wsl command to get IP
        result = subprocess.run(
            ["wsl", "hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Returns something like "172.20.144.1 "
            ip = result.stdout.strip().split()[0]
            return ip
    except Exception as e:
        print(f"Error getting WSL IP: {e}")
    
    return "localhost"

# Use in config
api_url = f"http://{get_wsl_ip()}:8000/api/v1"
```

## Deployment Checklist

### Windows Setup

1. **Install Python 3.10+**
2. **Install Qt**:
   ```
   pip install PySide6 requests Pillow
   ```

3. **Clone repository** or copy frontend folder

4. **Create config.json**:
   ```json
   {
     "api": {
       "base_url": "http://AUTO:8000/api/v1"
     }
   }
   ```
   (AUTO will be replaced with WSL IP)

5. **Run application**:
   ```
   python main.py
   ```

### WSL Backend Setup

1. **Start backend with external access**:
   ```bash
   cd /home/kjell/git_prosjekt/imalink/fase1
   uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Find IP address**:
   ```bash
   hostname -I
   ```

3. **Test from Windows**:
   ```powershell
   curl http://172.x.x.x:8000/api/v1/debug/status
   ```

## New: Image Similarity Features

### Backend Support (Available Now)
- ✅ **Perceptual Hash**: Auto-generated 16-bit pHash for all imported images
- ✅ **Similarity Search API**: `GET /image-files/similar/{image_id}`
- ✅ **Threshold Control**: Hamming distance 0-16 (0=identical, 16=different)
- ✅ **Duplicate Detection**: Find near-identical images automatically

### API Usage Examples
```python
# Find similar images
similar = api_client.find_similar_images(
    image_id=123,
    threshold=5,    # Allow some differences
    limit=10        # Max 10 results
)

# Upload with duplicate check
result = api_client.upload_image_with_similarity_check(
    "photo.jpg", 
    check_duplicates=True
)
if result.get("similar_images"):
    print("Warning: Similar images found!")
```

### Qt Implementation
- ✅ **DuplicateFinderWidget**: Find and manage duplicate groups
- ✅ **SimilarImagesFinder**: Interactive similarity search
- ✅ **Enhanced Gallery**: Right-click "Find Similar" integration
- ✅ **Background Processing**: Non-blocking similarity search

## Next Steps

1. Create new repository: `imalink-qt-frontend`
2. Implement basic API client with similarity support
3. Create main window with gallery view
4. Add import functionality with duplicate detection
5. Add photo detail view with "find similar" button
6. Add duplicate finder tab/panel
7. Add search/filter with similarity threshold
8. Add settings dialog
9. Package as Windows executable (PyInstaller)

---

## Resources

- **Qt Documentation**: https://doc.qt.io/qtforpython-6/
- **API Reference**: See `API_REFERENCE.md` in main repo
- **FastAPI Docs**: http://localhost:8000/docs (when backend running)
