# Simplified Multi-User Implementation: Clean Start Strategy

## 🎯 Forenklet Tilnærming: Multi-User Fra Starten

Siden du ikke har lagt inn bildene dine ennå, kan vi implementere multi-user systemet uten kompleks migrering. Dette er mye enklere og tryggere.

## 🚀 Strategi: Fresh Multi-User Database

### Fordeler Med Clean Start
- ✅ **Ingen migrering** av eksisterende data
- ✅ **Enklere implementasjon** uten backward compatibility
- ✅ **Renere kode** uten legacy støtte
- ✅ **Raskere utvikling** uten komplekse rollback prosedyrer
- ✅ **Bedre testing** med kontrollerte testdata

### Implementeringsfaser

## Fase 1: Core Multi-User Foundation

### Database Schema: Built for Multi-User
```python
# Alle modeller har user_id fra starten
class User(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    photos = relationship("Photo", back_populates="owner")
    import_sessions = relationship("ImportSession", back_populates="owner")
    file_storages = relationship("FileStorage", back_populates="owner")

class Photo(Base, TimestampMixin):
    hothash = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)  # Required from start
    
    # ... resten som før
    owner = relationship("User", back_populates="photos")

class ImportSession(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)  # Required from start
    
    # ... resten som før
    owner = relationship("User", back_populates="import_sessions")

class ImageFile(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)  # Required from start
    
    # ... resten som før
    owner = relationship("User", back_populates="image_files")

class FileStorage(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)  # Required from start
    
    # ... resten som før
    owner = relationship("User", back_populates="file_storages")
```

### Database Creation Script
```python
# scripts/create_multiuser_database.py
def create_fresh_multiuser_database():
    """
    Opprett helt ny database med multi-user schema fra starten
    """
    # Sikkerhetsspørsmål
    if os.path.exists("imalink.db"):
        response = input("⚠️  Database exists. Create backup and recreate? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return False
        
        # Backup existing database
        backup_name = f"imalink.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy("imalink.db", backup_name)
        print(f"✅ Backup created: {backup_name}")
        
        # Remove old database
        os.remove("imalink.db")
    
    # Create fresh database with multi-user schema
    engine = create_engine('sqlite:///imalink.db')
    Base.metadata.create_all(engine)
    
    print("✅ Fresh multi-user database created")
    return True

if __name__ == "__main__":
    print("🚀 Creating fresh multi-user database...")
    success = create_fresh_multiuser_database()
    
    if success:
        print("🎉 Ready for multi-user development!")
        print("📝 Next steps:")
        print("   1. Start backend: uv run uvicorn src.main:app --reload")
        print("   2. Register first user via API")
        print("   3. Begin testing with clean data")
```

## Fase 2: Authentication & User Management

### JWT Authentication Setup
```python
# core/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-here"  # Move to environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user
```

### User Management API
```python
# api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """Register new user"""
    # Check if username/email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | 
        (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        display_name=user_data.display_name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

@router.post("/login", response_model=TokenResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout_user():
    """Logout user (client should discard token)"""
    return {"message": "Successfully logged out"}
```

## Fase 3: User-Scoped Services

### Photo Service Med User Context
```python
# services/photo_service.py
class PhotoService:
    def __init__(self, db: Session):
        self.db = db
        self.photo_repo = PhotoRepository(db)
    
    def get_photos_for_user(
        self, 
        user_id: int, 
        offset: int = 0, 
        limit: int = 100
    ) -> PaginatedResponse[PhotoResponse]:
        """Get photos for specific user only"""
        return self.photo_repo.get_photos_for_user(user_id, offset, limit)
    
    def create_photo(
        self, 
        user_id: int, 
        photo_data: PhotoCreateRequest
    ) -> PhotoResponse:
        """Create photo owned by user"""
        photo_data.user_id = user_id  # Ensure user ownership
        return self.photo_repo.create(photo_data)
    
    def get_photo_by_hash(
        self, 
        user_id: int, 
        photo_hash: str
    ) -> PhotoResponse:
        """Get photo by hash - only if user owns it"""
        photo = self.photo_repo.get_by_hash_and_user(photo_hash, user_id)
        if not photo:
            raise NotFoundError("Photo not found or access denied")
        
        return self._convert_to_response(photo)
    
    def update_photo(
        self, 
        user_id: int, 
        photo_hash: str, 
        update_data: PhotoUpdateRequest
    ) -> PhotoResponse:
        """Update photo - only if user owns it"""
        photo = self.photo_repo.get_by_hash_and_user(photo_hash, user_id)
        if not photo:
            raise NotFoundError("Photo not found or access denied")
        
        return self.photo_repo.update(photo_hash, update_data)
    
    def delete_photo(
        self, 
        user_id: int, 
        photo_hash: str
    ) -> bool:
        """Delete photo - only if user owns it"""
        photo = self.photo_repo.get_by_hash_and_user(photo_hash, user_id)
        if not photo:
            raise NotFoundError("Photo not found or access denied")
        
        return self.photo_repo.delete(photo_hash)
```

### Protected API Endpoints
```python
# api/v1/photos.py
@router.get("/", response_model=PaginatedResponse[PhotoResponse])
async def get_photos(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),  # Required authentication
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get user's photos"""
    return photo_service.get_photos_for_user(current_user.id, offset, limit)

@router.post("/", response_model=PhotoResponse, status_code=201)
async def create_photo(
    photo_data: PhotoCreateRequest,
    current_user: User = Depends(get_current_user),  # Required authentication
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Create new photo for current user"""
    return photo_service.create_photo(current_user.id, photo_data)

@router.get("/{photo_hash}", response_model=PhotoResponse)
async def get_photo(
    photo_hash: str,
    current_user: User = Depends(get_current_user),  # Required authentication
    photo_service: PhotoService = Depends(get_photo_service)
):
    """Get specific photo (only if owned by user)"""
    return photo_service.get_photo_by_hash(current_user.id, photo_hash)
```

## Fase 4: Dependencies & Configuration

### Requirements Update
```toml
# pyproject.toml - add authentication dependencies
dependencies = [
    # ... existing dependencies
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.20",
]
```

### Environment Configuration
```python
# core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///imalink.db"
    
    # Authentication
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Multi-user settings
    multi_user_enabled: bool = True
    require_authentication: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Fase 5: Testing Strategy

### Test Data Setup
```python
# tests/fixtures/user_fixtures.py
@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        display_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user"""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}

# tests/test_multiuser_photos.py
def test_user_can_only_see_own_photos(client, auth_headers, test_user):
    """Test that users only see their own photos"""
    # Create photo for test user
    response = client.post("/api/v1/photos", 
                          json={"title": "My Photo"}, 
                          headers=auth_headers)
    assert response.status_code == 201
    
    # User should see their own photo
    response = client.get("/api/v1/photos", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    
def test_user_cannot_access_other_users_photos(client, db_session):
    """Test user isolation"""
    # Create two users
    user1 = create_test_user("user1", "user1@test.com")
    user2 = create_test_user("user2", "user2@test.com")
    
    # User1 creates photo
    headers1 = get_auth_headers(user1)
    response = client.post("/api/v1/photos", 
                          json={"title": "User1 Photo"}, 
                          headers=headers1)
    photo_hash = response.json()["hothash"]
    
    # User2 tries to access User1's photo
    headers2 = get_auth_headers(user2)
    response = client.get(f"/api/v1/photos/{photo_hash}", headers=headers2)
    assert response.status_code == 404  # Not found (access denied)
```

## 🚀 Implementation Steps

### Step 1: Backup & Clean Database
```bash
# Backup current database (if exists)
cd fase1
mv imalink.db imalink.db.single_user_backup

# Create fresh multi-user database
uv run python scripts/create_multiuser_database.py
```

### Step 2: Install Dependencies
```bash
# Add authentication dependencies
cd fase1
uv add "python-jose[cryptography]" "passlib[bcrypt]"
```

### Step 3: Implement Core Models
```bash
# Update models with user_id fields
# Implement User model
# Update all relationships
```

### Step 4: Add Authentication
```bash
# Implement JWT authentication
# Add auth endpoints
# Protect existing endpoints
```

### Step 5: Test & Verify
```bash
# Run test suite
uv run pytest tests/

# Manual testing
# 1. Register user
# 2. Login
# 3. Create photos
# 4. Verify isolation
```

## ✅ Benefits of Clean Start Approach

1. **🎯 Focused Development** - No legacy concerns
2. **🔧 Simpler Code** - Built for multi-user from start
3. **⚡ Faster Implementation** - No migration complexity
4. **🧪 Better Testing** - Clean test data scenarios
5. **📈 Better Performance** - Optimized for user-scoped queries
6. **🔐 Security First** - Authentication required from day one

## 🎯 Timeline Estimate

- **Week 1**: Core models + database creation
- **Week 2**: Authentication & user management
- **Week 3**: User-scoped services & API protection
- **Week 4**: Testing & frontend integration
- **Week 5**: Production deployment & monitoring

Denne tilnærmingen er mye renere og raskere å implementere. Vil du at jeg starter med implementeringen av Fase 1 (Core Multi-User Foundation)?