"""
API endpoints for Author management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.models import Author

class AuthorCreate(BaseModel):
    name: str
    email: Optional[str] = None
    bio: Optional[str] = None

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_authors(db: Session = Depends(get_db)):
    """
    Get all authors
    """
    authors = db.query(Author).order_by(Author.name).all()
    
    return [
        {
            "id": author.id,
            "name": author.name,
            "email": author.email,
            "bio": author.bio,
            "created_at": author.created_at.isoformat() if author.created_at else None,
            "image_count": len(author.images) if author.images else 0
        }
        for author in authors
    ]


@router.post("/", response_model=dict)
async def create_author(
    author_data: AuthorCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new author
    """
    name = author_data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Author name cannot be empty")
    
    # Check if author already exists
    existing = db.query(Author).filter(Author.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Author '{name}' already exists")
    
    # Create new author
    author = Author(
        name=name,
        email=author_data.email.strip() if author_data.email else None,
        bio=author_data.bio.strip() if author_data.bio else None
    )
    db.add(author)
    db.commit()
    db.refresh(author)
    
    return {
        "id": author.id,
        "name": author.name,
        "email": author.email,
        "bio": author.bio,
        "created_at": author.created_at.isoformat(),
        "message": f"Author '{name}' created successfully"
    }


@router.get("/{author_id}")
async def get_author(author_id: int, db: Session = Depends(get_db)):
    """
    Get specific author details
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return {
        "id": author.id,
        "name": author.name,
        "email": author.email,
        "bio": author.bio,
        "created_at": author.created_at.isoformat() if author.created_at else None,
        "image_count": len(author.images) if author.images else 0,
        "images": [
            {
                "id": img.id,
                "filename": img.original_filename,
                "taken_at": img.taken_at.isoformat() if img.taken_at else None
            }
            for img in author.images[:10]  # Show first 10 images
        ] if author.images else []
    }


class AuthorUpdate(BaseModel):
    name: str
    email: Optional[str] = None
    bio: Optional[str] = None

@router.put("/{author_id}")
async def update_author(
    author_id: int,
    author_data: AuthorUpdate,
    db: Session = Depends(get_db)
):
    """
    Update author details
    """
    name = author_data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Author name cannot be empty")
    
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Check if new name already exists (excluding current author)
    existing = db.query(Author).filter(Author.name == name, Author.id != author_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Author '{name}' already exists")
    
    # Update fields
    author.name = name
    author.email = author_data.email.strip() if author_data.email else None
    author.bio = author_data.bio.strip() if author_data.bio else None
    
    db.commit()
    db.refresh(author)
    
    return {
        "id": author.id,
        "name": author.name,
        "email": author.email,
        "bio": author.bio,
        "message": f"Author '{name}' updated successfully"
    }


@router.delete("/{author_id}")
async def delete_author(author_id: int, db: Session = Depends(get_db)):
    """
    Delete author (only if no images are associated)
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Check if author has images
    image_count = len(author.images) if author.images else 0
    if image_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete author '{author.name}' - {image_count} images are still associated"
        )
    
    name = author.name
    db.delete(author)
    db.commit()
    
    return {"message": f"Author '{name}' deleted successfully"}