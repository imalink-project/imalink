# Service Layer Implementation Guide

## 🏗️ **Hva er Service Layer?**

Service Layer er et lag mellom API (Controllers) og Database (Repositories) som inneholder **business logic**.

```
Current:     API Controller → Database Model
Improved:    API Controller → Service → Repository → Database Model
```

---

## 🎯 **Problemet med nåværende struktur**

### **Eksempel fra eksisterende kode:**

```python
# I api/images.py - PROBLEMATISK
@router.get("/")
async def get_images(db: Session = Depends(get_db)):
    images = (
        db.query(Image)  # ❌ Direkte database query i controller
        .order_by(Image.taken_at.desc(), Image.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # ❌ Business logic i controller
    for img in images:
        raw_companion = ImageProcessor.find_raw_companion(img.file_path)
        
        # ❌ Manual data mapping i controller
        result.append({
            "id": img.id,
            "filename": img.original_filename,
            # ... masse mapping kode
        })
```

### **Problemene:**
- 🔴 **Business logic i controller** - RAW companion logic
- 🔴 **Direkte database queries** - db.query(Image) i API
- 🔴 **Manual data mapping** - konverterer til dict i controller
- 🔴 **Blandet ansvar** - API gjør database + business logic

---

## 💡 **Service Layer løsningen**

### **1. Repository Layer (Data Access)**

```python
# repositories/image_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Image

class ImageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_images(
        self, 
        offset: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None
    ) -> List[Image]:
        query = self.db.query(Image)
        
        if author_id:
            query = query.filter(Image.author_id == author_id)
            
        return (query
                .order_by(Image.taken_at.desc(), Image.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all())
    
    def get_by_id(self, image_id: int) -> Optional[Image]:
        return self.db.query(Image).filter(Image.id == image_id).first()
    
    def count_images(self, author_id: Optional[int] = None) -> int:
        query = self.db.query(Image)
        if author_id:
            query = query.filter(Image.author_id == author_id)
        return query.count()
    
    def create(self, image_data: dict) -> Image:
        image = Image(**image_data)
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image
    
    def update(self, image_id: int, update_data: dict) -> Optional[Image]:
        image = self.get_by_id(image_id)
        if image:
            for key, value in update_data.items():
                setattr(image, key, value)
            self.db.commit()
            self.db.refresh(image)
        return image
    
    def delete(self, image_id: int) -> bool:
        image = self.get_by_id(image_id)
        if image:
            self.db.delete(image)
            self.db.commit()
            return True
        return False
```

### **2. Response Schemas (Data Transfer Objects)**

```python
# schemas/image_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ImageResponse(BaseModel):
    id: int
    hash: str
    filename: str
    taken_at: Optional[datetime]
    created_at: datetime
    width: int
    height: int
    file_size: int
    format: str
    has_gps: bool
    has_raw_companion: bool = False
    user_rotation: int = 0
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    
    class Config:
        from_attributes = True

class ImageCreateRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    author_id: Optional[int] = None
    tags: List[str] = []

class ImageUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = None

class PaginationMeta(BaseModel):
    total: int
    offset: int
    limit: int
    page: int
    pages: int
    
class ImageListResponse(BaseModel):
    data: List[ImageResponse]
    meta: PaginationMeta

# Generic response wrappers
from typing import TypeVar, Generic
T = TypeVar('T')

class SingleResponse(BaseModel, Generic[T]):
    data: T
    meta: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: dict
```

### **3. Service Layer (Business Logic)**

```python
# services/image_service.py
from typing import Optional, List
from sqlalchemy.orm import Session
from schemas.image_schemas import ImageResponse, ImageListResponse, ImageCreateRequest
from repositories.image_repository import ImageRepository
from services.image_processor import ImageProcessor
from exceptions import NotFoundError, DuplicateImageError

class ImageService:
    def __init__(self, db: Session):
        self.image_repo = ImageRepository(db)
        self.image_processor = ImageProcessor()
    
    async def get_images(
        self, 
        offset: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None
    ) -> ImageListResponse:
        # Hent data via repository
        images = self.image_repo.get_images(offset, limit, author_id)
        total = self.image_repo.count_images(author_id)
        
        # Business logic: RAW companion detection
        image_responses = []
        for img in images:
            raw_companion = self.image_processor.find_raw_companion(img.file_path)
            
            # Transform til response model
            image_response = ImageResponse(
                id=img.id,
                hash=img.image_hash,
                filename=img.original_filename,
                taken_at=img.taken_at,
                created_at=img.created_at,
                width=img.width,
                height=img.height,
                file_size=img.file_size,
                format=img.file_format,
                has_gps=bool(img.gps_latitude and img.gps_longitude),
                has_raw_companion=raw_companion is not None,
                user_rotation=img.user_rotation or 0,
                title=img.title,
                description=img.description,
                tags=img.tags or []
            )
            image_responses.append(image_response)
        
        # Beregn paginering metadata
        page = (offset // limit) + 1
        pages = (total + limit - 1) // limit
        
        return ImageListResponse(
            data=image_responses,
            meta=PaginationMeta(
                total=total,
                offset=offset,
                limit=limit,
                page=page,
                pages=pages
            )
        )
    
    async def get_image_by_id(self, image_id: int) -> ImageResponse:
        image = self.image_repo.get_by_id(image_id)
        if not image:
            raise NotFoundError("Image", image_id)
        
        # Business logic: RAW companion detection
        raw_companion = self.image_processor.find_raw_companion(image.file_path)
        
        return ImageResponse(
            **image.__dict__,
            has_raw_companion=bool(raw_companion)
        )
    
    async def create_image(self, image_data: ImageCreateRequest) -> ImageResponse:
        # Business logic: Duplicate check
        if self.image_repo.exists_by_hash(image_data.hash):
            raise DuplicateImageError("Image with this hash already exists")
        
        # Business logic: Thumbnail generation
        thumbnail = await self.image_processor.generate_thumbnail(image_data.file_path)
        
        image_dict = image_data.dict()
        image_dict['thumbnail'] = thumbnail
        
        image = self.image_repo.create(image_dict)
        return ImageResponse.from_orm(image)
    
    async def update_image(self, image_id: int, update_data: ImageUpdateRequest) -> ImageResponse:
        image = self.image_repo.get_by_id(image_id)
        if not image:
            raise NotFoundError("Image", image_id)
        
        # Business logic: Handle tag updates
        if update_data.tags is not None:
            # Normalize tags (lowercase, trim spaces)
            update_data.tags = [tag.lower().strip() for tag in update_data.tags]
        
        updated_image = self.image_repo.update(image_id, update_data.dict(exclude_unset=True))
        return ImageResponse.from_orm(updated_image)
    
    async def delete_image(self, image_id: int) -> bool:
        image = self.image_repo.get_by_id(image_id)
        if not image:
            raise NotFoundError("Image", image_id)
        
        # Business logic: Cleanup files
        await self.image_processor.cleanup_files(image.file_path)
        
        return self.image_repo.delete(image_id)
```

### **4. Exception Handling**

```python
# exceptions.py
class APIException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

class NotFoundError(APIException):
    def __init__(self, resource: str, id: any):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND",
            status_code=404
        )

class DuplicateImageError(APIException):
    def __init__(self, message: str = "Image already exists"):
        super().__init__(
            message=message,
            code="DUPLICATE_IMAGE",
            status_code=409
        )
```

### **5. Dependency Injection**

```python
# dependencies.py
from sqlalchemy.orm import Session
from database.connection import get_db
from services.image_service import ImageService
from services.author_service import AuthorService
from services.import_service import ImportService
from fastapi import Depends

def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    return ImageService(db)

def get_author_service(db: Session = Depends(get_db)) -> AuthorService:
    return AuthorService(db)

def get_import_service(db: Session = Depends(get_db)) -> ImportService:
    return AuthorService(db)
```

### **6. Oppdaterte Controllers (Bare koordinering)**

```python
# api/images.py - FORBEDRET
from fastapi import APIRouter, Depends, HTTPException, Query
from services.image_service import ImageService
from schemas.image_schemas import ImageListResponse, ImageResponse, ImageCreateRequest
from dependencies import get_image_service
from exceptions import APIException
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=ImageListResponse)
async def get_images(
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of images to return"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    image_service: ImageService = Depends(get_image_service)
):
    """Get list of images with pagination and optional filtering"""
    try:
        return await image_service.get_images(offset, limit, author_id)
    except Exception as e:
        logger.error(f"Error getting images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    image_service: ImageService = Depends(get_image_service)
):
    """Get specific image by ID"""
    try:
        return await image_service.get_image_by_id(image_id)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=ImageResponse, status_code=201)
async def create_image(
    image_data: ImageCreateRequest,
    image_service: ImageService = Depends(get_image_service)
):
    """Create new image"""
    try:
        return await image_service.create_image(image_data)
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error creating image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🎯 **Fordeler med Service Layer**

### **1. Separation of Concerns:**
- **Controller**: HTTP handling, validation, error responses
- **Service**: Business logic, orchestration  
- **Repository**: Data access, queries
- **Schemas**: Data transformation, validation

### **2. Testbarhet:**
```python
# Lett å teste business logic isolert
def test_image_service():
    mock_repo = Mock(ImageRepository)
    mock_repo.get_images.return_value = [mock_image]
    
    service = ImageService(mock_repo)
    
    # Test business logic uten database
    result = service.get_images(0, 10)
    assert len(result.data) == 1
    assert result.meta.total == 1
```

### **3. Gjenbrukbarhet:**
```python
# Service kan brukes av flere controllers
@router.get("/images/")
async def api_get_images(service: ImageService = Depends()):
    return await service.get_images()

@router.get("/admin/images/")  # Admin endpoint
async def admin_get_images(service: ImageService = Depends()):
    # Same service, different controller
    return await service.get_images_with_admin_data()
```

### **4. Konsistent Data Format:**
- Alle responses følger samme struktur
- Automatisk paginering metadata
- Konsistent error handling
- Type safety med Pydantic

---

## 📊 **Implementeringsplan**

### **Fase 1: Oppsett (5 min)**
1. Opprett `services/` og `repositories/` mapper
2. Opprett `schemas/` for response models  
3. Opprett `exceptions.py` for custom exceptions
4. Lag `dependencies.py` for dependency injection

### **Fase 2: Images API (15 min)**
1. `ImageRepository` - data access
2. `ImageService` - business logic
3. `ImageResponse` schemas  
4. Oppdater `images.py` controller

### **Fase 3: Andre APIs (10 min hver)**
- Authors, Import - samme pattern som Images API

### **Fase 4: Testing (10 min)**
- Unit tests for services
- Integration tests for repositories

---

## 🔄 **Migrasjonstrategi**

### **Inkrementell tilnærming:**
1. Behold eksisterende API funksjoner
2. Implementer ny service/repository struktur parallelt
3. Migrer endpoints én av gangen
4. Test grundig etter hver migrering
5. Fjern gammel kode når alt fungerer

### **Bakoverkompatibilitet:**
- Samme URL struktur
- Samme response format (forbedret)
- Ingen breaking changes for frontend

---

## 🎯 **Neste Steg**

**Spørsmål:**
1. **Hvor omfattende?** Skal vi starte med bare Images API, eller gjøre alle?
2. **Hvor detaljert?** Full paginering + metadata, eller enklere først?  
3. **Database queries?** Beholde eksisterende queries eller optimalisere?

**Service Layer gir deg mye renere, mer testbar og vedlikeholdbar kode!** 🚀