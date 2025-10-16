"""
ImaLink Mini-Frontend
Simple desktop application built with Flet
"""
import flet as ft
from services.api_client import APIClient
from components.photo_gallery import PhotoGallery
from components.import_view import ImportView


def main(page: ft.Page):
    """Main application entry point"""
    
    # Page configuration
    page.title = "ImaLink Mini-Frontend"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.width = 1200
    page.window.height = 800
    
    # API client
    api_client = APIClient(base_url="http://localhost:8000/api/v1")
    
    # Status bar at top
    status_bar = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.PHOTO_LIBRARY, size=30),
            ft.Text("ImaLink", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),  # Spacer
            ft.Text("API: http://localhost:8000/api/v1", size=12, italic=True)
        ]),
        padding=10,
        bgcolor=ft.Colors.BLUE_50,
        border_radius=8
    )
    
    # Navigation rail
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.PHOTO_LIBRARY_OUTLINED,
                selected_icon=ft.Icons.PHOTO_LIBRARY,
                label="Gallery"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.UPLOAD_FILE_OUTLINED,
                selected_icon=ft.Icons.UPLOAD_FILE,
                label="Import"
            ),
        ],
        on_change=lambda e: switch_view(e.control.selected_index)
    )
    
    # Create views
    def on_photo_click(photo):
        """Handle photo click - show details dialog"""
        hothash = photo.get("hothash", "")
        title = photo.get("title", "Untitled")
        image_files = photo.get("image_files", [])
        
        # Create dialog
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Column([
                ft.Text(f"Hash: {hothash}", size=12),
                ft.Text(f"Rating: {photo.get('rating', 'N/A')}", size=12),
                ft.Divider(),
                ft.Text("Image Files:", weight=ft.FontWeight.BOLD),
                *[ft.Text(f"• {img.get('filename', 'Unknown')}", size=12) for img in image_files]
            ], tight=True, scroll=ft.ScrollMode.AUTO, height=300),
            actions=[
                ft.TextButton("Close", on_click=lambda _: close_dialog(dialog))
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
    
    def close_dialog(dialog):
        dialog.open = False
        page.update()
    
    def on_import_complete():
        """Refresh gallery after import"""
        gallery_view.load_photos()
        nav_rail.selected_index = 0
        switch_view(0)
    
    gallery_view = PhotoGallery(api_client, on_photo_click=on_photo_click)
    import_view = ImportView(api_client, on_import_complete=on_import_complete)
    
    # Add file picker overlay
    page.overlay.append(import_view.file_picker)
    
    # Content container
    content = ft.Container(
        content=gallery_view,
        expand=True,
        padding=20
    )
    
    def switch_view(index):
        """Switch between views"""
        if index == 0:
            content.content = gallery_view
            gallery_view.load_photos()
        elif index == 1:
            content.content = import_view
        page.update()
    
    # Layout
    page.add(
        status_bar,
        ft.Row([
            nav_rail,
            ft.VerticalDivider(width=1),
            content
        ], expand=True)
    )
    
    # Initial load
    gallery_view.load_photos()


if __name__ == "__main__":
    ft.app(target=main)
