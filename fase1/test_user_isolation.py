"""
Test complete user-scoped authentication and data isolation
"""
import sys
sys.path.append('/home/kjell/git_prosjekt/imalink/fase1/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Photo, Author
from services.auth_service import AuthService
from repositories.photo_repository import PhotoRepository
from repositories.author_repository import AuthorRepository
from schemas.user import UserCreate
from schemas.requests.author_requests import AuthorCreateRequest

def test_user_isolation():
    """Test that users can only see their own data"""
    
    # Setup in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🔒 Testing User Data Isolation")
        print("=" * 50)
        
        # Create two users
        auth_service = AuthService(db)
        
        user1 = auth_service.register_user(UserCreate(
            username="user1",
            email="user1@test.com",
            password="password1",
            display_name="User One"
        ))
        
        user2 = auth_service.register_user(UserCreate(
            username="user2", 
            email="user2@test.com",
            password="password2",
            display_name="User Two"
        ))
        
        user1_id = getattr(user1, 'id')
        user2_id = getattr(user2, 'id')
        
        print(f"✅ Created users: {getattr(user1, 'username')} (ID: {user1_id}) and {getattr(user2, 'username')} (ID: {user2_id})")
        
        # Test 1: Each user creates their own authors
        author_repo = AuthorRepository(db)
        
        author1 = author_repo.create(AuthorCreateRequest(
            name="User1 Author",
            email="author1@test.com",
            bio="Author created by user 1"
        ), user1_id)
        
        author2 = author_repo.create(AuthorCreateRequest(
            name="User2 Author", 
            email="author2@test.com",
            bio="Author created by user 2"
        ), user2_id)
        
        print(f"✅ User1 created author: {getattr(author1, 'name')}")
        print(f"✅ User2 created author: {getattr(author2, 'name')}")
        
        # Test 2: User isolation - each user can only see their own authors
        user1_authors = author_repo.get_all(user_id=user1_id)
        user2_authors = author_repo.get_all(user_id=user2_id)
        
        print(f"\\n🔍 Data Isolation Test:")
        print(f"   User1 sees {len(user1_authors)} authors: {[getattr(a, 'name') for a in user1_authors]}")
        print(f"   User2 sees {len(user2_authors)} authors: {[getattr(a, 'name') for a in user2_authors]}")
        
        if len(user1_authors) == 1 and len(user2_authors) == 1:
            if getattr(user1_authors[0], 'name') == "User1 Author" and getattr(user2_authors[0], 'name') == "User2 Author":
                print("✅ User data isolation working correctly!")
            else:
                print("❌ Data isolation failed - users seeing wrong authors")
                return False
        else:
            print("❌ Data isolation failed - wrong number of authors")
            return False
        
        # Test 3: Cross-user access should fail
        print(f"\\n🚫 Cross-User Access Test:")
        
        # User1 tries to access User2's author by ID
        user1_accessing_user2_author = author_repo.get_by_id(getattr(author2, 'id'), user1_id)
        if user1_accessing_user2_author is None:
            print("✅ User1 cannot access User2's author (correct)")
        else:
            print("❌ User1 can access User2's author (security issue!)")
            return False
        
        # User1 tries to update User2's author  
        update_result = author_repo.update(getattr(author2, 'id'), {"name": "Hacked Name"}, user1_id)
        if update_result is None:
            print("✅ User1 cannot update User2's author (correct)")
        else:
            print("❌ User1 can update User2's author (security issue!)")
            return False
        
        # User1 tries to delete User2's author
        delete_result = author_repo.delete(getattr(author2, 'id'), user1_id)
        if not delete_result:
            print("✅ User1 cannot delete User2's author (correct)")
        else:
            print("❌ User1 can delete User2's author (security issue!)")
            return False
        
        # Test 4: Authentication flow
        print(f"\\n🔐 Authentication Flow Test:")
        
        # Login as user1
        login_result = auth_service.login("user1", "password1")
        if login_result:
            token, logged_user = login_result
            print(f"✅ User1 login successful")
            
            # Verify token
            from utils.security import get_user_id_from_token
            token_user_id = get_user_id_from_token(token)
            if token_user_id and int(token_user_id) == user1_id:
                print(f"✅ Token validation successful")
            else:
                print(f"❌ Token validation failed")
                return False
        else:
            print(f"❌ User1 login failed")
            return False
        
        # Invalid login should fail
        invalid_login = auth_service.login("user1", "wrongpassword")
        if not invalid_login:
            print("✅ Invalid login correctly rejected")
        else:
            print("❌ Invalid login was accepted")
            return False
        
        print("\\n" + "=" * 50)
        print("🎉 All user isolation and authentication tests passed!")
        print("🔒 Multi-user system is secure and ready!")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = test_user_isolation()
    if success:
        print("\\n✅ USER ISOLATION TEST: PASSED")
    else:
        print("\\n❌ USER ISOLATION TEST: FAILED")
        sys.exit(1)