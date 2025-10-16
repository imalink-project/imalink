"""
Import View Component
Upload images and create image files via API
"""
import flet as ft
from services.api_client import APIClient
from utils.image_utils import generate_hotpreview, get_image_info
from pathlib import Path


class ImportView(ft.Column):
    """Import view for uploading images"""
    
    def __init__(self, api_client: APIClient, on_import_complete=None):
        super().__init__()
        self.api_client = api_client
        self.on_import_complete = on_import_complete
        self.selected_files = []
        self.spacing = 20
        self.scroll = ft.ScrollMode.AUTO
        
        # File picker
        self.file_picker = ft.FilePicker(on_result=self._handle_file_selection)
        
        # Header
        self.header = ft.Text("Import Images", size=24, weight=ft.FontWeight.BOLD)
        
        # Select button
        self.select_btn = ft.ElevatedButton(
            "Select Images",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self.file_picker.pick_files(
                allow_multiple=True,
                allowed_extensions=["jpg", "jpeg", "png", "heic", "dng", "cr2", "nef"]
            )
        )
        
        # Selected files list
        self.file_list = ft.ListView(expand=1, spacing=10, padding=20)
        
        # Import button
        self.import_btn = ft.ElevatedButton(
            "Import Selected Files",
            icon=ft.Icons.CLOUD_UPLOAD,
            on_click=lambda _: self._import_files(),
            disabled=True
        )
        
        # Status
        self.status_text = ft.Text("", italic=True)
        self.progress_bar = ft.ProgressBar(visible=False)
        
        self.controls = [
            self.header,
            self.select_btn,
            ft.Divider(),
            ft.Text("Selected Files:", weight=ft.FontWeight.BOLD),
            self.file_list,
            self.import_btn,
            self.progress_bar,
            self.status_text
        ]
    
    def _handle_file_selection(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if not e.files:
            return
        
        self.selected_files = e.files
        self.file_list.controls.clear()
        
        for file in self.selected_files:
            file_path = file.path
            file_info = get_image_info(file_path)
            
            card = ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.IMAGE, size=40),
                        ft.Column([
                            ft.Text(file_info["filename"], weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"{file_info.get('width', '?')}x{file_info.get('height', '?')} • "
                                f"{file_info['file_size'] / 1024:.1f} KB",
                                size=12
                            )
                        ], spacing=2, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _, f=file: self._remove_file(f)
                        )
                    ], spacing=10),
                    padding=10
                )
            )
            self.file_list.controls.append(card)
        
        self.import_btn.disabled = len(self.selected_files) == 0
        self.status_text.value = f"{len(self.selected_files)} file(s) selected"
        self.update()
    
    def _remove_file(self, file):
        """Remove file from selection"""
        self.selected_files = [f for f in self.selected_files if f != file]
        self._handle_file_selection(ft.FilePickerResultEvent(files=self.selected_files))
    
    def _import_files(self):
        """Import selected files to API"""
        if not self.selected_files:
            return
        
        self.import_btn.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = 0
        self.update()
        
        success_count = 0
        error_count = 0
        total = len(self.selected_files)
        
        for idx, file in enumerate(self.selected_files):
            try:
                file_path = file.path
                self.status_text.value = f"Processing {idx + 1}/{total}: {Path(file_path).name}"
                self.progress_bar.value = (idx + 1) / total
                self.update()
                
                # Generate hotpreview
                hotpreview_base64 = generate_hotpreview(file_path)
                if not hotpreview_base64:
                    raise Exception("Failed to generate hotpreview")
                
                # Prepare image data
                file_info = get_image_info(file_path)
                image_data = {
                    "filename": file_info["filename"],
                    "file_size": file_info["file_size"],
                    "file_path": file_path,
                    "hotpreview": hotpreview_base64,
                    "exif_data": {}  # TODO: Extract real EXIF
                }
                
                # Upload to API
                result = self.api_client.create_image_file(image_data)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error importing {file.path}: {e}")
        
        # Done
        self.progress_bar.visible = False
        self.status_text.value = f"Import complete: {success_count} succeeded, {error_count} failed"
        self.import_btn.disabled = False
        
        # Clear selection
        self.selected_files = []
        self.file_list.controls.clear()
        self.update()
        
        # Notify parent
        if self.on_import_complete and success_count > 0:
            self.on_import_complete()
