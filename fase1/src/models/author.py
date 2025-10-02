"""
Author/photographer model
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .image import Image
    from .import_model import Import


class Author(Base, TimestampMixin):
    """
    Author/photographer model - who took the photo
    """
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    bio = Column(Text, nullable=True)
    
    # Relationships
    images = relationship("Image", back_populates="author")
    imports = relationship("Import", back_populates="default_author")
    
    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}')>"