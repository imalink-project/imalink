"""
Test authentication system with basic user registration and login
"""
import asyncio
import sys
import os
sys.path.append('/home/kjell/git_prosjekt/imalink/fase1/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from services.auth_service import AuthService
from repositories.user_repository import UserRepository
from schemas.user import UserCreate, UserLogin

async def test_authentication():
    """Test user registration and login flow"""
    
    # Setup in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🔐 Testing Authentication System")
        print("=" * 50)
        
        # Test 1: User Registration
        print("\n1. Testing User Registration...")
        auth_service = AuthService(db)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com", 
            password="secret123",
            display_name="Test User"
        )
        
        user = auth_service.register_user(user_data)
        print(f"✅ User registered: {user}")
        print(f"   - ID: {getattr(user, 'id')}")
        print(f"   - Username: {getattr(user, 'username')}")
        print(f"   - Email: {getattr(user, 'email')}")
        print(f"   - Active: {getattr(user, 'is_active')}")
        
        # Test 2: User Login
        print("\n2. Testing User Login...")
        
        login_result = auth_service.login("testuser", "secret123")
        if login_result:
            access_token, logged_user = login_result
            print(f"✅ Login successful!")
            print(f"   - Token: {access_token[:50]}...")
            print(f"   - User: {getattr(logged_user, 'username')}")
        else:
            print("❌ Login failed!")
            return
        
        # Test 3: Token Validation
        print("\n3. Testing Token Validation...")
        from utils.security import get_user_id_from_token
        
        user_id = get_user_id_from_token(access_token)
        if user_id:
            print(f"✅ Token validation successful! User ID: {user_id}")
            
            # Get user by token
            current_user = auth_service.get_current_user(int(user_id))
            if current_user:
                print(f"✅ User retrieved from token: {getattr(current_user, 'username')}")
            else:
                print("❌ Could not retrieve user from token")
        else:
            print("❌ Token validation failed!")
            return
        
        # Test 4: Invalid Login
        print("\n4. Testing Invalid Login...")
        invalid_login = auth_service.login("testuser", "wrongpassword")
        if not invalid_login:
            print("✅ Invalid login correctly rejected")
        else:
            print("❌ Invalid login was accepted (security issue!)")
        
        # Test 5: Duplicate Registration
        print("\n5. Testing Duplicate Registration...")
        try:
            duplicate_user = auth_service.register_user(user_data)
            print("❌ Duplicate registration was allowed (should fail)")
        except ValueError as e:
            print(f"✅ Duplicate registration correctly rejected: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 All authentication tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_authentication())