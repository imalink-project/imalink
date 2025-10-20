"""
Unit tests for PhotoStack Repository
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from models.base import Base
from models.user import User
from models.photo import Photo
from models.photo_stack import PhotoStack
from repositories.photo_stack_repository import PhotoStackRepository


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def test_users(db_session):
    """Create test users"""
    user1 = User(
        username="testuser1",
        email="test1@example.com", 
        password_hash="hash123",
        display_name="Test User 1"
    )
    user2 = User(
        username="testuser2",
        email="test2@example.com",
        password_hash="hash456", 
        display_name="Test User 2"
    )
    
    db_session.add_all([user1, user2])
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)
    
    return user1, user2


@pytest.fixture
def test_photos(db_session, test_users):
    """Create test photos"""
    user1, user2 = test_users
    
    photos = []
    for i in range(5):
        photo = Photo(
            hothash=f"hash{i:03d}",
            width=1920,
            height=1080,
            user_id=user1.id,
            rating=i % 5 + 1
        )
        photos.append(photo)
    
    # Add one photo for user2
    photo_user2 = Photo(
        hothash="hash_user2",
        width=1920,
        height=1080,
        user_id=user2.id
    )
    photos.append(photo_user2)
    
    db_session.add_all(photos)
    db_session.commit()
    
    return [p.hothash for p in photos[:5]], photo_user2.hothash


@pytest.fixture
def photo_stack_repo(db_session):
    """Create PhotoStack repository instance"""
    return PhotoStackRepository(db_session)


class TestPhotoStackRepository:
    """Test PhotoStack repository operations"""
    
    def test_create_stack(self, photo_stack_repo, test_users):
        """Test creating a new photo stack"""
        user1, user2 = test_users
        
        stack_data = {
            "stack_type": "panorama",
            "cover_photo_hothash": "hash001"
        }
        
        stack = photo_stack_repo.create(stack_data, user1.id)
        
        assert stack is not None
        assert stack.stack_type == "panorama"
        assert stack.cover_photo_hothash == "hash001"
        assert stack.user_id == user1.id
        assert stack.created_at is not None
        assert stack.updated_at is not None
    
    def test_create_stack_minimal(self, photo_stack_repo, test_users):
        """Test creating stack with minimal data"""
        user1, user2 = test_users
        
        stack_data = {}
        stack = photo_stack_repo.create(stack_data, user1.id)
        
        assert stack is not None
        assert stack.stack_type is None
        assert stack.cover_photo_hothash is None
        assert stack.user_id == user1.id
    
    def test_get_by_id_user_isolation(self, photo_stack_repo, test_users):
        """Test that users can only access their own stacks"""
        user1, user2 = test_users
        
        # Create stack for user1
        stack_data = {"stack_type": "user1_stack"}
        stack = photo_stack_repo.create(stack_data, user1.id)
        
        # User1 can access their own stack
        retrieved = photo_stack_repo.get_by_id(stack.id, user1.id)
        assert retrieved is not None
        assert retrieved.id == stack.id
        
        # User2 cannot access user1's stack
        not_found = photo_stack_repo.get_by_id(stack.id, user2.id)
        assert not_found is None
    
    def test_get_all_user_isolation(self, photo_stack_repo, test_users):
        """Test pagination and user isolation"""
        user1, user2 = test_users
        
        # Create stacks for both users
        for i in range(3):
            photo_stack_repo.create({"stack_type": f"user1_stack_{i}"}, user1.id)
            photo_stack_repo.create({"stack_type": f"user2_stack_{i}"}, user2.id)
        
        # User1 should only see their stacks
        user1_stacks = photo_stack_repo.get_all(user1.id, offset=0, limit=10)
        assert len(user1_stacks) == 3
        for stack in user1_stacks:
            assert stack.user_id == user1.id
            assert "user1" in stack.stack_type
        
        # User2 should only see their stacks
        user2_stacks = photo_stack_repo.get_all(user2.id, offset=0, limit=10)
        assert len(user2_stacks) == 3
        for stack in user2_stacks:
            assert stack.user_id == user2.id
            assert "user2" in stack.stack_type
    
    def test_pagination(self, photo_stack_repo, test_users):
        """Test pagination works correctly"""
        user1, user2 = test_users
        
        # Create 5 stacks for user1
        for i in range(5):
            photo_stack_repo.create({"stack_type": f"stack_{i}"}, user1.id)
        
        # Test first page
        page1 = photo_stack_repo.get_all(user1.id, offset=0, limit=2)
        assert len(page1) == 2
        
        # Test second page
        page2 = photo_stack_repo.get_all(user1.id, offset=2, limit=2)
        assert len(page2) == 2
        
        # Test third page
        page3 = photo_stack_repo.get_all(user1.id, offset=4, limit=2)
        assert len(page3) == 1
        
        # Ensure no overlaps
        all_ids = set()
        for page in [page1, page2, page3]:
            for stack in page:
                assert stack.id not in all_ids
                all_ids.add(stack.id)
    
    def test_count_all(self, photo_stack_repo, test_users):
        """Test counting stacks per user"""
        user1, user2 = test_users
        
        # Initially no stacks
        assert photo_stack_repo.count_all(user1.id) == 0
        assert photo_stack_repo.count_all(user2.id) == 0
        
        # Add stacks for user1
        for i in range(3):
            photo_stack_repo.create({"stack_type": f"stack_{i}"}, user1.id)
        
        # Add stacks for user2
        for i in range(2):
            photo_stack_repo.create({"stack_type": f"stack_{i}"}, user2.id)
        
        # Check counts are correct and isolated
        assert photo_stack_repo.count_all(user1.id) == 3
        assert photo_stack_repo.count_all(user2.id) == 2
    
    def test_update_stack(self, photo_stack_repo, test_users):
        """Test updating stack metadata"""
        user1, user2 = test_users
        
        # Create stack
        stack = photo_stack_repo.create({"stack_type": "Original"}, user1.id)
        
        # Update stack
        update_data = {
            "stack_type": "burst",
            "cover_photo_hothash": "new_cover"
        }
        updated = photo_stack_repo.update(stack.id, update_data, user1.id)
        
        assert updated is not None
        assert updated.stack_type == "burst"
        assert updated.cover_photo_hothash == "new_cover"
        assert updated.user_id == user1.id
        
        # User2 cannot update user1's stack
        not_updated = photo_stack_repo.update(stack.id, {"stack_type": "Hacked"}, user2.id)
        assert not_updated is None
    
    def test_delete_stack(self, photo_stack_repo, test_users):
        """Test deleting stacks with user isolation"""
        user1, user2 = test_users
        
        # Create stack for user1
        stack = photo_stack_repo.create({"stack_type": "To delete"}, user1.id)
        stack_id = stack.id
        
        # Verify stack exists
        assert photo_stack_repo.get_by_id(stack_id, user1.id) is not None
        
        # User2 cannot delete user1's stack
        assert not photo_stack_repo.delete(stack_id, user2.id)
        assert photo_stack_repo.get_by_id(stack_id, user1.id) is not None
        
        # User1 can delete their own stack
        assert photo_stack_repo.delete(stack_id, user1.id)
        assert photo_stack_repo.get_by_id(stack_id, user1.id) is None
    
    def test_add_photos_to_stack(self, photo_stack_repo, test_users, test_photos):
        """Test adding photos to stack"""
        user1, user2 = test_users
        photo_hashes, user2_photo = test_photos
        
        # Create stack for user1
        stack = photo_stack_repo.create({"stack_type": "Photo stack"}, user1.id)
        
        # Add photos to stack (now sets stack_id on photos)
        success = photo_stack_repo.add_photos(stack.id, photo_hashes[:3], user1.id)
        assert success
        
        # Verify photos are in stack
        stack_photos = photo_stack_repo.get_photos_in_stack(stack.id, user1.id)
        assert len(stack_photos) == 3
        assert set(stack_photos) == set(photo_hashes[:3])
        
        # Try to add photo that's already in stack (should move it, no duplicates)
        success = photo_stack_repo.add_photos(stack.id, [photo_hashes[0]], user1.id)
        assert success
        
        # Should still have 3 unique photos
        stack_photos = photo_stack_repo.get_photos_in_stack(stack.id, user1.id)
        assert len(stack_photos) == 3
    
    def test_remove_photos_from_stack(self, photo_stack_repo, test_users, test_photos):
        """Test removing photos from stack"""
        user1, user2 = test_users
        photo_hashes, user2_photo = test_photos
        
        # Create stack and add photos
        stack = photo_stack_repo.create({"stack_type": "Photo stack"}, user1.id)
        photo_stack_repo.add_photos(stack.id, photo_hashes[:4], user1.id)
        
        # Remove some photos (now sets stack_id to None)
        success = photo_stack_repo.remove_photos(stack.id, photo_hashes[:2], user1.id)
        assert success
        
        # Verify correct photos remain
        remaining = photo_stack_repo.get_photos_in_stack(stack.id, user1.id)
        assert len(remaining) == 2
        assert set(remaining) == set(photo_hashes[2:4])
        
        # Remove non-existent photo (should not fail but return False)
        success = photo_stack_repo.remove_photos(stack.id, ["nonexistent"], user1.id)
        assert not success  # No photos were actually removed
    
    def test_get_photo_count(self, photo_stack_repo, test_users, test_photos):
        """Test counting photos in stack"""
        user1, user2 = test_users
        photo_hashes, user2_photo = test_photos
        
        # Create empty stack
        stack = photo_stack_repo.create({"stack_type": "Empty stack"}, user1.id)
        assert photo_stack_repo.get_photo_count(stack.id, user1.id) == 0
        
        # Add photos and verify count
        photo_stack_repo.add_photos(stack.id, photo_hashes[:3], user1.id)
        assert photo_stack_repo.get_photo_count(stack.id, user1.id) == 3
        
        # Remove photo and verify count
        photo_stack_repo.remove_photos(stack.id, [photo_hashes[0]], user1.id)
        assert photo_stack_repo.get_photo_count(stack.id, user1.id) == 2
        
        # User2 cannot access user1's stack count
        assert photo_stack_repo.get_photo_count(stack.id, user2.id) == 0
    
    def test_get_photo_stack(self, photo_stack_repo, test_users, test_photos):
        """Test getting the stack containing a specific photo (one-to-many)"""
        user1, user2 = test_users
        photo_hashes, user2_photo = test_photos
        
        target_photo = photo_hashes[0]
        
        # Create stacks
        stack1 = photo_stack_repo.create({"stack_type": "Stack 1"}, user1.id)
        stack2 = photo_stack_repo.create({"stack_type": "Stack 2"}, user1.id)
        
        # Photo not in any stack initially
        result = photo_stack_repo.get_photo_stack(target_photo, user1.id)
        assert result is None
        
        # Add photo to stack1
        photo_stack_repo.add_photos(stack1.id, [target_photo], user1.id)
        
        # Verify photo is in stack1
        result = photo_stack_repo.get_photo_stack(target_photo, user1.id)
        assert result is not None
        assert result.id == stack1.id
        assert result.stack_type == "Stack 1"
        
        # Move photo to stack2 (one-to-many: photo moves between stacks)
        photo_stack_repo.add_photos(stack2.id, [target_photo], user1.id)
        
        # Now photo should only be in stack2
        result = photo_stack_repo.get_photo_stack(target_photo, user1.id)
        assert result is not None
        assert result.id == stack2.id
        assert result.stack_type == "Stack 2"
        
        # User2 should not see user1's stack
        user2_result = photo_stack_repo.get_photo_stack(target_photo, user2.id)
        assert user2_result is None
        
        # Test with non-existent photo
        nonexistent_result = photo_stack_repo.get_photo_stack("nonexistent", user1.id)
        assert nonexistent_result is None
    
    def test_stack_deletion_cleans_memberships(self, photo_stack_repo, test_users, test_photos):
        """Test that deleting stack also removes all photo memberships"""
        user1, user2 = test_users
        photo_hashes, user2_photo = test_photos
        
        # Create stack and add photos
        stack = photo_stack_repo.create({"stack_type": "To delete"}, user1.id)
        photo_stack_repo.add_photos(stack.id, photo_hashes[:3], user1.id)
        
        # Verify photos are in stack
        assert photo_stack_repo.get_photo_count(stack.id, user1.id) == 3
        
        # Delete stack (should set stack_id to None on all photos)
        photo_stack_repo.delete(stack.id, user1.id)
        
        # Verify stack is gone
        assert photo_stack_repo.get_by_id(stack.id, user1.id) is None
        
        # Verify photos are no longer in any stack
        for photo_hash in photo_hashes[:3]:
            stack = photo_stack_repo.get_photo_stack(photo_hash, user1.id)
            assert stack is None