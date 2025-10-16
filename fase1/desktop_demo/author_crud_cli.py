#!/usr/bin/env python3
"""
ImaLink Desktop Demo - Author CRUD (CLI Version)
================================================

En enkel CLI-versjon for testing på WSL/headless systemer.
Demonstrerer samme CRUD-operasjoner uten GUI.

Kjør: python author_crud_cli.py
"""

import sys
from pathlib import Path

# Legg til src directory for backend imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / "src"))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from models.author import Author


class AuthorCLI:
    """CLI interface for Author CRUD"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def list_authors(self):
        """List all authors"""
        authors = self.db.query(Author).order_by(Author.name).all()
        
        if not authors:
            print("\n📋 No authors found.")
            return
        
        print(f"\n📋 Found {len(authors)} author(s):\n")
        print("-" * 80)
        for i, author in enumerate(authors, 1):
            print(f"{i}. {author.name}")
            if author.email:
                print(f"   📧 {author.email}")
            if author.bio:
                bio = author.bio[:60] + "..." if len(author.bio) > 60 else author.bio
                print(f"   📝 {bio}")
            if author.created_at:
                print(f"   📅 Created: {author.created_at.strftime('%Y-%m-%d %H:%M')}")
            print("-" * 80)
    
    def add_author(self):
        """Add new author"""
        print("\n➕ Add New Author")
        print("-" * 40)
        
        name = input("Name (required): ").strip()
        if not name:
            print("❌ Name is required!")
            return
        
        # Check if exists
        existing = self.db.query(Author).filter(Author.name == name).first()
        if existing:
            print(f"❌ Author '{name}' already exists!")
            return
        
        email = input("Email (optional): ").strip() or None
        bio = input("Bio (optional): ").strip() or None
        
        try:
            author = Author(name=name, email=email, bio=bio)
            self.db.add(author)
            self.db.commit()
            
            print(f"\n✅ Author '{name}' added successfully!")
            print(f"   ID: {author.id}")
            
        except Exception as e:
            self.db.rollback()
            print(f"\n❌ Error adding author: {e}")
    
    def update_author(self):
        """Update existing author"""
        self.list_authors()
        
        try:
            author_id = int(input("\nEnter author ID to update: ").strip())
        except ValueError:
            print("❌ Invalid ID!")
            return
        
        author = self.db.query(Author).filter(Author.id == author_id).first()
        if not author:
            print("❌ Author not found!")
            return
        
        print(f"\n✏️  Updating: {author.name}")
        print(f"Current email: {author.email or '(none)'}")
        print(f"Current bio: {author.bio or '(none)'}")
        print("\nPress Enter to keep current value, or type new value:")
        print("-" * 40)
        
        name = input(f"Name [{author.name}]: ").strip()
        if name:
            # Check if new name already exists (excluding current author)
            existing = self.db.query(Author).filter(
                Author.name == name,
                Author.id != author_id
            ).first()
            if existing:
                print(f"❌ Another author with name '{name}' already exists!")
                return
            author.name = name
        
        email = input(f"Email [{author.email or ''}]: ").strip()
        if email:
            author.email = email or None
        
        bio = input(f"Bio [{author.bio or ''}]: ").strip()
        if bio:
            author.bio = bio or None
        
        try:
            self.db.commit()
            print(f"\n✅ Author updated successfully!")
            
        except Exception as e:
            self.db.rollback()
            print(f"\n❌ Error updating author: {e}")
    
    def delete_author(self):
        """Delete author"""
        self.list_authors()
        
        try:
            author_id = int(input("\nEnter author ID to delete: ").strip())
        except ValueError:
            print("❌ Invalid ID!")
            return
        
        author = self.db.query(Author).filter(Author.id == author_id).first()
        if not author:
            print("❌ Author not found!")
            return
        
        confirm = input(f"\n⚠️  Delete '{author.name}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Cancelled.")
            return
        
        try:
            self.db.delete(author)
            self.db.commit()
            print(f"\n✅ Author '{author.name}' deleted successfully!")
            
        except Exception as e:
            self.db.rollback()
            print(f"\n❌ Error deleting author: {e}")
    
    def run(self):
        """Main menu loop"""
        print("\n" + "=" * 80)
        print("📸 ImaLink Author Manager (CLI)")
        print("=" * 80)
        
        while True:
            print("\n" + "─" * 40)
            print("Menu:")
            print("  1. List all authors")
            print("  2. Add new author")
            print("  3. Update author")
            print("  4. Delete author")
            print("  0. Exit")
            print("─" * 40)
            
            choice = input("\nYour choice: ").strip()
            
            if choice == '1':
                self.list_authors()
            elif choice == '2':
                self.add_author()
            elif choice == '3':
                self.update_author()
            elif choice == '4':
                self.delete_author()
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice!")
    
    def cleanup(self):
        """Cleanup resources"""
        self.db.close()


def main():
    """Entry point"""
    cli = AuthorCLI()
    
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        cli.cleanup()


if __name__ == "__main__":
    main()
