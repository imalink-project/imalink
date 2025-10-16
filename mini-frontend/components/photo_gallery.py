"""
Photo Gallery Component
Displays photos in a grid with hotpreview thumbnails
"""
import flet as ft
from services.api_client import APIClient
import base64
import io


class PhotoGallery(ft.Column):
    """Photo gallery view with grid of thumbnails"""
    
    def __init__(self, api_client: APIClient, on_photo_click=None):
        super().__init__()
        self.api_client = api_client
        self.on_photo_click = on_photo_click
        self.photos = []
        self.spacing = 10
        self.scroll = ft.ScrollMode.AUTO
        
        # Header
        self.header = ft.Row([
            ft.Text("Photo Gallery", size=24, weight=ft.FontWeight.BOLD),
            ft.IconButton(
                icon="refresh",
                tooltip="Refresh",
                on_click=lambda _: self.load_photos()
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Photo grid
        self.photo_grid = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=180,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        # Status text
        self.status_text = ft.Text("Loading photos...", italic=True)
        
        self.controls = [
            self.header,
            self.status_text,
            self.photo_grid
        ]
    
    def load_photos(self):
        """Load photos from API"""
        try:
            self.status_text.value = "Loading photos..."
            self.update()
            
            response = self.api_client.get_photos(offset=0, limit=100)
            self.photos = response.get("data", [])
            
            # Clear grid
            self.photo_grid.controls.clear()
            
            if not self.photos:
                self.status_text.value = "No photos found. Import some images!"
                self.update()
                return
            
            # Add photo cards
            for photo in self.photos:
                card = self._create_photo_card(photo)
                self.photo_grid.controls.append(card)
            
            self.status_text.value = f"Showing {len(self.photos)} photos"
            self.update()
            
        except Exception as e:
            self.status_text.value = f"Error loading photos: {str(e)}"
            self.update()
    
    def _create_photo_card(self, photo: dict) -> ft.Container:
        """Create a photo card with thumbnail"""
        hothash = photo.get("hothash", "")
        title = photo.get("title", "Untitled")
        
        # Try to get hotpreview
        try:
            hotpreview_bytes = self.api_client.get_photo_hotpreview(hothash)
            image_base64 = base64.b64encode(hotpreview_bytes).decode('utf-8')
            
            image = ft.Image(
                src_base64=image_base64,
                width=150,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=8
            )
        except:
            # Fallback if no hotpreview
            image = ft.Container(
                content=ft.Icon("image", size=60),
                width=150,
                height=150,
                bgcolor="grey300",
                border_radius=8,
                alignment=ft.alignment.center
            )
        
        # Photo info overlay
        info_text = ft.Text(
            title[:20] + "..." if len(title) > 20 else title,
            size=12,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER
        )
        
        file_count = len(photo.get("image_files", []))
        file_count_badge = ft.Container(
            content=ft.Text(f"{file_count}", size=10, color="white"),
            bgcolor="blue700",
            padding=4,
            border_radius=10,
            width=24,
            height=24,
            alignment=ft.alignment.center
        )
        
        # Card with click handler
        card = ft.Container(
            content=ft.Stack([
                image,
                ft.Container(
                    content=ft.Column([
                        info_text,
                        file_count_badge
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor="black,0.7",
                    padding=8,
                    border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
                    alignment=ft.alignment.bottom_center,
                    width=150
                )
            ]),
            width=150,
            height=180,
            on_click=lambda _, p=photo: self._handle_photo_click(p),
            ink=True,
            border_radius=8,
            tooltip=f"{title}\n{file_count} file(s)\nHash: {hothash[:16]}..."
        )
        
        return card
    
    def _handle_photo_click(self, photo: dict):
        """Handle photo card click"""
        if self.on_photo_click:
            self.on_photo_click(photo)
