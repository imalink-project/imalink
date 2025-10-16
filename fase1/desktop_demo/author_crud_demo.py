#!/usr/bin/env python3
"""
ImaLink Desktop Demo - Author CRUD
===================================

En enkel Flet desktop app som demonstrerer CRUD-operasjoner på Author-tabellen.
Dette er en prototype for å teste desktop client-konseptet.

Kjør: python author_crud_demo.py
"""

import sys
from pathlib import Path

# Legg til parent directory og src directory for å få tilgang til backend-koden
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / "src"))

import flet as ft
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from models.author import Author


class AuthorCrudApp:
    """Flet app for Author CRUD operasjoner"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "ImaLink Author Manager"
        self.page.window_width = 800
        self.page.window_height = 600
        self.page.padding = 20
        
        # Database session
        self.db: Session = SessionLocal()
        
        # UI Components
        self.author_list = ft.ListView(expand=True, spacing=10, padding=10)
        self.name_field = ft.TextField(label="Name", width=300)
        self.email_field = ft.TextField(label="Email (optional)", width=300)
        self.bio_field = ft.TextField(
            label="Bio (optional)", 
            width=300, 
            multiline=True, 
            min_lines=3,
            max_lines=5
        )
        
        # Selected author for edit/delete
        self.selected_author_id = None
        
        # Status message
        self.status_text = ft.Text(value="", color=ft.Colors.GREEN)
        
        # Build UI
        self.build_ui()
        
        # Load initial data
        self.load_authors()
    
    def build_ui(self):
        """Bygg UI komponenter"""
        
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text("📸 ImaLink Author Manager", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Desktop Demo - CRUD Operations", size=14, color=ft.Colors.GREY_700),
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        # Form section
        form_section = ft.Container(
            content=ft.Column([
                ft.Text("Add/Edit Author", size=18, weight=ft.FontWeight.BOLD),
                self.name_field,
                self.email_field,
                self.bio_field,
                ft.Row([
                    ft.ElevatedButton(
                        "Add Author",
                        icon=ft.Icons.ADD,
                        on_click=self.add_author
                    ),
                    ft.ElevatedButton(
                        "Update Selected",
                        icon=ft.Icons.EDIT,
                        on_click=self.update_author,
                        disabled=True
                    ),
                    ft.OutlinedButton(
                        "Clear Form",
                        on_click=self.clear_form
                    ),
                ], spacing=10),
                self.status_text,
            ], spacing=10),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
        )
        
        # List section
        list_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Authors", size=18, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Refresh list",
                        on_click=lambda _: self.load_authors()
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=self.author_list,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=10,
                    expand=True,
                )
            ], expand=True),
            expand=True,
        )
        
        # Main layout
        self.page.add(
            header,
            ft.Row([
                ft.Container(content=form_section, width=350),
                ft.Container(content=list_section, expand=True),
            ], expand=True, spacing=20)
        )
    
    def load_authors(self):
        """Last inn alle forfattere fra databasen"""
        try:
            authors = self.db.query(Author).order_by(Author.name).all()
            
            self.author_list.controls.clear()
            
            if not authors:
                self.author_list.controls.append(
                    ft.Text("No authors found. Add one above!", color=ft.Colors.GREY_500)
                )
            else:
                for author in authors:
                    self.author_list.controls.append(
                        self.create_author_card(author)
                    )
            
            self.page.update()
            
        except Exception as e:
            self.show_status(f"Error loading authors: {str(e)}", is_error=True)
    
    def create_author_card(self, author: Author) -> ft.Container:
        """Lag et kort for en forfatter"""
        
        # Build info text
        info_parts = [f"👤 {author.name}"]
        if author.email:
            info_parts.append(f"📧 {author.email}")
        if author.bio:
            bio_preview = author.bio[:50] + "..." if len(author.bio) > 50 else author.bio
            info_parts.append(f"📝 {bio_preview}")
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(author.name, size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(author.email or "No email", size=12, color=ft.Colors.GREY_600),
                        ft.Text(
                            f"Created: {author.created_at.strftime('%Y-%m-%d %H:%M')}" if author.created_at else "",
                            size=10,
                            color=ft.Colors.GREY_500
                        ),
                    ], expand=True),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            tooltip="Edit",
                            on_click=lambda _, a=author: self.edit_author(a)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            tooltip="Delete",
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda _, a=author: self.delete_author(a)
                        ),
                    ]),
                ]),
                ft.Text(author.bio or "", size=12, color=ft.Colors.GREY_700) if author.bio else None,
            ], spacing=5),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50,
        )
    
    def add_author(self, e):
        """Legg til ny forfatter"""
        name = self.name_field.value.strip()
        
        if not name:
            self.show_status("Name is required!", is_error=True)
            return
        
        try:
            # Sjekk om navnet allerede eksisterer
            existing = self.db.query(Author).filter(Author.name == name).first()
            if existing:
                self.show_status(f"Author '{name}' already exists!", is_error=True)
                return
            
            # Opprett ny forfatter
            author = Author(
                name=name,
                email=self.email_field.value.strip() or None,
                bio=self.bio_field.value.strip() or None
            )
            
            self.db.add(author)
            self.db.commit()
            
            self.show_status(f"✅ Author '{name}' added successfully!")
            self.clear_form(None)
            self.load_authors()
            
        except Exception as ex:
            self.db.rollback()
            self.show_status(f"Error adding author: {str(ex)}", is_error=True)
    
    def edit_author(self, author: Author):
        """Fyll skjemaet med forfatter for redigering"""
        self.selected_author_id = author.id
        self.name_field.value = author.name
        self.email_field.value = author.email or ""
        self.bio_field.value = author.bio or ""
        
        # Enable update button
        for control in self.page.controls:
            self.enable_update_button(control)
        
        self.show_status(f"Editing: {author.name}")
        self.page.update()
    
    def enable_update_button(self, control):
        """Recursive function to enable update button"""
        if isinstance(control, ft.ElevatedButton) and control.text == "Update Selected":
            control.disabled = False
        elif hasattr(control, 'controls'):
            for child in control.controls:
                self.enable_update_button(child)
        elif hasattr(control, 'content'):
            self.enable_update_button(control.content)
    
    def update_author(self, e):
        """Oppdater valgt forfatter"""
        if not self.selected_author_id:
            self.show_status("No author selected!", is_error=True)
            return
        
        name = self.name_field.value.strip()
        if not name:
            self.show_status("Name is required!", is_error=True)
            return
        
        try:
            author = self.db.query(Author).filter(Author.id == self.selected_author_id).first()
            
            if not author:
                self.show_status("Author not found!", is_error=True)
                return
            
            # Sjekk om det nye navnet allerede eksisterer (unntatt current author)
            existing = self.db.query(Author).filter(
                Author.name == name,
                Author.id != self.selected_author_id
            ).first()
            
            if existing:
                self.show_status(f"Another author with name '{name}' already exists!", is_error=True)
                return
            
            # Oppdater
            author.name = name
            author.email = self.email_field.value.strip() or None
            author.bio = self.bio_field.value.strip() or None
            
            self.db.commit()
            
            self.show_status(f"✅ Author '{name}' updated successfully!")
            self.clear_form(None)
            self.load_authors()
            
        except Exception as ex:
            self.db.rollback()
            self.show_status(f"Error updating author: {str(ex)}", is_error=True)
    
    def delete_author(self, author: Author):
        """Slett forfatter (med bekreftelse)"""
        def confirm_delete(e):
            try:
                # Refresh author from DB to ensure it still exists
                db_author = self.db.query(Author).filter(Author.id == author.id).first()
                if db_author:
                    self.db.delete(db_author)
                    self.db.commit()
                    self.show_status(f"✅ Author '{author.name}' deleted successfully!")
                    self.load_authors()
                
                dialog.open = False
                self.page.update()
                
            except Exception as ex:
                self.db.rollback()
                self.show_status(f"Error deleting author: {str(ex)}", is_error=True)
                dialog.open = False
                self.page.update()
        
        def cancel_delete(e):
            dialog.open = False
            self.page.update()
        
        # Confirmation dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete '{author.name}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(
                    color=ft.Colors.RED
                )),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def clear_form(self, e):
        """Tøm skjemaet"""
        self.name_field.value = ""
        self.email_field.value = ""
        self.bio_field.value = ""
        self.selected_author_id = None
        
        # Disable update button
        for control in self.page.controls:
            self.disable_update_button(control)
        
        self.status_text.value = ""
        self.page.update()
    
    def disable_update_button(self, control):
        """Recursive function to disable update button"""
        if isinstance(control, ft.ElevatedButton) and control.text == "Update Selected":
            control.disabled = True
        elif hasattr(control, 'controls'):
            for child in control.controls:
                self.disable_update_button(child)
        elif hasattr(control, 'content'):
            self.disable_update_button(control.content)
    
    def show_status(self, message: str, is_error: bool = False):
        """Vis status melding"""
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED if is_error else ft.Colors.GREEN
        self.page.update()
    
    def cleanup(self):
        """Cleanup database connection"""
        self.db.close()


def main(page: ft.Page):
    """Main entry point"""
    app = AuthorCrudApp(page)
    
    # Cleanup on close
    def on_window_event(e):
        if e.data == "close":
            app.cleanup()
    
    page.on_window_event = on_window_event


if __name__ == "__main__":
    print("🚀 Starting ImaLink Author Manager...")
    print("📁 Using database from backend configuration")
    print("🌐 Opening in web browser on http://localhost:8550")
    
    # Use web mode for WSL compatibility
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
