# General API Guidelines

## 🏗️ **Prinsipper for en God API**

### **1. REST-prinsipper (Representational State Transfer)**

#### **Ressurs-orientert Design:**
```
GET    /api/images           # Hent liste av bilder
GET    /api/images/{id}      # Hent spesifikt bilde
POST   /api/images           # Opprett nytt bilde
PUT    /api/images/{id}      # Oppdater hele bildet
PATCH  /api/images/{id}      # Oppdater deler av bildet
DELETE /api/images/{id}      # Slett bilde
```

#### **HTTP Status Codes:**
- `200 OK` - Vellykket forespørsel
- `201 Created` - Ressurs opprettet
- `400 Bad Request` - Ugyldig forespørsel
- `401 Unauthorized` - Mangler autentisering
- `403 Forbidden` - Ingen tilgang
- `404 Not Found` - Ressurs ikke funnet
- `422 Unprocessable Entity` - Valideringsfeil
- `500 Internal Server Error` - Serverfeil

---

### **2. Konsistent Data Format (JSON)**

#### **Standard Response Struktur:**
```json
{
  "data": [...],           // Hoveddata
  "meta": {                // Metadata
    "total": 150,
    "page": 1,
    "per_page": 20,
    "pages": 8
  },
  "links": {               // HATEOAS links
    "self": "/api/images?page=1",
    "next": "/api/images?page=2",
    "prev": null,
    "first": "/api/images?page=1",
    "last": "/api/images?page=8"
  }
}
```

#### **Error Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "name",
        "message": "Name is required"
      }
    ]
  }
}
```

---

### **3. Versioning Strategy**

```
/api/v1/images     # Version i URL
/api/v2/images     # Ny versjon med breaking changes

# Eller via headers:
Accept: application/vnd.api+json;version=1
```

---

### **4. Pydantic Models for Validation**

#### **Input Models (Request):**
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ImageCreateRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    author_id: Optional[int] = None
    tags: Optional[List[str]] = []

class ImageUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)
```

#### **Output Models (Response):**
```python
class ImageResponse(BaseModel):
    id: int
    filename: str
    title: Optional[str]
    description: Optional[str]
    width: int
    height: int
    file_size: int
    created_at: datetime
    taken_at: Optional[datetime]
    author: Optional[AuthorSummary]  # Nested model
    tags: List[str]
    
    class Config:
        from_attributes = True  # For SQLAlchemy compatibility

class AuthorSummary(BaseModel):
    id: int
    name: str
```

---

### **5. Lagdelt Arkitektur**

```
Controllers (API Layer)
    ↓
Services (Business Logic)
    ↓
Repositories (Data Access)
    ↓
Database Models
```

#### **Eksempel - Service Layer:**
```python
# services/image_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from repositories.image_repository import ImageRepository
from models.schemas import ImageCreateRequest, ImageResponse

class ImageService:
    def __init__(self, db: Session):
        self.image_repo = ImageRepository(db)
    
    async def get_images(
        self, 
        skip: int = 0, 
        limit: int = 100,
        author_id: Optional[int] = None
    ) -> List[ImageResponse]:
        images = await self.image_repo.get_images(
            skip=skip, 
            limit=limit, 
            author_id=author_id
        )
        return [ImageResponse.from_orm(img) for img in images]
    
    async def create_image(self, image_data: ImageCreateRequest) -> ImageResponse:
        # Business logic her
        if await self.image_repo.exists_by_hash(image_data.hash):
            raise DuplicateImageError("Image already exists")
        
        image = await self.image_repo.create(image_data)
        return ImageResponse.from_orm(image)
```

#### **Controller:**
```python
# api/images.py
from fastapi import APIRouter, Depends, HTTPException, Query
from services.image_service import ImageService

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[ImageResponse])
async def get_images(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    author_id: Optional[int] = Query(None),
    service: ImageService = Depends(get_image_service)
):
    try:
        images = await service.get_images(skip, limit, author_id)
        total = await service.count_images(author_id=author_id)
        
        return PaginatedResponse(
            data=images,
            meta=PaginationMeta(
                total=total,
                page=skip // limit + 1,
                per_page=limit,
                pages=(total + limit - 1) // limit
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### **6. Generic Response Wrappers**

```python
from typing import TypeVar, Generic, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta
    links: Optional[PaginationLinks] = None

class SingleResponse(BaseModel, Generic[T]):
    data: T
    meta: Optional[Dict] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[List[ValidationError]] = None
```

---

### **7. Dependency Injection**

```python
# dependencies.py
from sqlalchemy.orm import Session
from database.connection import get_db
from services.image_service import ImageService

def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    return ImageService(db)

def get_author_service(db: Session = Depends(get_db)) -> AuthorService:
    return AuthorService(db)
```

---

### **8. Error Handling**

```python
# exceptions.py
class APIException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

class NotFoundError(APIException):
    def __init__(self, resource: str, id: Any):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND",
            status_code=404
        )

# Global exception handler
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )
```

---

### **9. Authentication & Authorization**

```python
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await get_user_by_id(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Bruk i endpoints:
@router.get("/private")
async def private_endpoint(current_user: User = Depends(get_current_user)):
    return {"user": current_user.name}
```

---

### **10. Dokumentasjon (OpenAPI/Swagger)**

```python
app = FastAPI(
    title="ImaLink API",
    description="Professional image management API",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc"       # ReDoc
)

@router.post(
    "/images/",
    response_model=ImageResponse,
    status_code=201,
    summary="Create new image",
    description="Upload and create a new image with metadata",
    responses={
        201: {"description": "Image created successfully"},
        400: {"description": "Invalid request data"},
        422: {"description": "Validation error"}
    }
)
```

---

## 🎯 **Sammenligning med Nåværende API**

### **Hva som gjøres bra:**
- ✅ Bruker FastAPI og Pydantic
- ✅ REST-lignende struktur
- ✅ JSON responses

### **Forbedringspunkter:**
- ❌ Blander HTML-serving med API
- ❌ Inkonsistent response format
- ❌ Mangler service layer
- ❌ Begrenset error handling
- ❌ Ingen versioning strategi

### **Anbefalt Refaktorering:**

1. **Skill API fra frontend-serving**
2. **Implementer service layer**
3. **Standardiser response format**
4. **Legg til proper error handling**
5. **Implementer dependency injection**

---

## 📚 **Ressurser**

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [REST API Design Guidelines](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)

---

**En ren API skal være platform-agnostic og kunne brukes av web, mobile, eller andre systemer!** 🚀