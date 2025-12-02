"""
Tests for Event API endpoints
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import User, Photo, Event, PhotoEvent, Author
from src.utils.security import create_access_token


class TestEventsAPI:
    """Test suite for Event API endpoints"""
    
    def test_create_event_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test creating a basic event"""
        response = client.post(
            "/api/v1/events/",
            json={
                "name": "London Trip 2025",
                "description": "Summer vacation in London",
                "start_date": "2025-07-01T00:00:00",
                "end_date": "2025-07-10T00:00:00",
                "location_name": "London, UK",
                "sort_order": 0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "London Trip 2025"
        assert data["description"] == "Summer vacation in London"
        assert data["user_id"] == test_user.id
        assert data["parent_event_id"] is None
        assert "id" in data
    
    def test_create_child_event(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test creating hierarchical events"""
        # Create parent
        parent = Event(
            user_id=test_user.id,
            name="London Trip",
            sort_order=0
        )
        test_db_session.add(parent)
        test_db_session.commit()
        
        # Create child
        response = client.post(
            "/api/v1/events/",
            json={
                "name": "Tower of London",
                "parent_event_id": parent.id,
                "sort_order": 0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Tower of London"
        assert data["parent_event_id"] == parent.id
    
    def test_create_event_requires_auth(self, client: TestClient):
        """Test that creating event requires authentication"""
        response = client.post(
            "/api/v1/events/",
            json={"name": "Test Event"}
        )
        assert response.status_code == 401
    
    def test_list_events_empty(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test listing events when none exist"""
        response = client.get("/api/v1/events/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_root_events(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test listing only root events"""
        # Create root events
        event1 = Event(user_id=test_user.id, name="Trip 1", sort_order=0)
        event2 = Event(user_id=test_user.id, name="Trip 2", sort_order=1)
        test_db_session.add_all([event1, event2])
        test_db_session.commit()
        
        # Create child (should not appear in root list)
        child = Event(user_id=test_user.id, name="Child", parent_event_id=event1.id, sort_order=0)
        test_db_session.add(child)
        test_db_session.commit()
        
        response = client.get("/api/v1/events/", headers=auth_headers)
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 2
        assert events[0]["name"] == "Trip 1"
        assert events[1]["name"] == "Trip 2"
    
    def test_list_events_by_parent(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test filtering events by parent_id"""
        parent = Event(user_id=test_user.id, name="Parent", sort_order=0)
        test_db_session.add(parent)
        test_db_session.commit()
        
        child1 = Event(user_id=test_user.id, name="Child 1", parent_event_id=parent.id, sort_order=0)
        child2 = Event(user_id=test_user.id, name="Child 2", parent_event_id=parent.id, sort_order=1)
        test_db_session.add_all([child1, child2])
        test_db_session.commit()
        
        response = client.get(f"/api/v1/events/?parent_id={parent.id}", headers=auth_headers)
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 2
        assert events[0]["name"] == "Child 1"
        assert events[1]["name"] == "Child 2"
    
    def test_list_events_user_isolation(self, client: TestClient, test_db_session: Session):
        """Test that users only see their own events"""
        # Create users
        user1 = User(username="user1", email="user1@example.com", password_hash="hash1", is_active=True)
        user2 = User(username="user2", email="user2@example.com", password_hash="hash2", is_active=True)
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        
        event1 = Event(user_id=user1.id, name="User 1 Event", sort_order=0)
        event2 = Event(user_id=user2.id, name="User 2 Event", sort_order=0)
        test_db_session.add_all([event1, event2])
        test_db_session.commit()
        
        user1_token = create_access_token({"sub": str(user1.id)})
        
        response = client.get(
            "/api/v1/events/",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["name"] == "User 1 Event"
    
    def test_get_event_tree(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test getting full hierarchical tree"""
        # Create hierarchy: Root -> Child -> Grandchild
        root = Event(user_id=test_user.id, name="Root", sort_order=0)
        test_db_session.add(root)
        test_db_session.commit()
        
        child = Event(user_id=test_user.id, name="Child", parent_event_id=root.id, sort_order=0)
        test_db_session.add(child)
        test_db_session.commit()
        
        grandchild = Event(user_id=test_user.id, name="Grandchild", parent_event_id=child.id, sort_order=0)
        test_db_session.add(grandchild)
        test_db_session.commit()
        
        response = client.get("/api/v1/events/tree", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 3
        assert len(data["events"]) == 1  # One root
        
        root_node = data["events"][0]
        assert root_node["name"] == "Root"
        assert len(root_node["children"]) == 1
        
        child_node = root_node["children"][0]
        assert child_node["name"] == "Child"
        assert len(child_node["children"]) == 1
        
        grandchild_node = child_node["children"][0]
        assert grandchild_node["name"] == "Grandchild"
        assert len(grandchild_node["children"]) == 0
    
    def test_get_event_by_id(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test getting single event by ID"""
        event = Event(user_id=test_user.id, name="Test Event", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        
        response = client.get(f"/api/v1/events/{event.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event.id
        assert data["name"] == "Test Event"
    
    def test_get_event_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent event"""
        response = client.get("/api/v1/events/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_event(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test updating event"""
        event = Event(user_id=test_user.id, name="Original Name", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        
        response = client.put(
            f"/api/v1/events/{event.id}",
            json={"name": "Updated Name", "description": "New description"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"
    
    def test_move_event(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test moving event to new parent"""
        parent1 = Event(user_id=test_user.id, name="Parent 1", sort_order=0)
        parent2 = Event(user_id=test_user.id, name="Parent 2", sort_order=1)
        child = Event(user_id=test_user.id, name="Child", parent_event_id=parent1.id, sort_order=0)
        test_db_session.add_all([parent1, parent2, child])
        test_db_session.commit()
        
        # Move child from parent1 to parent2
        response = client.post(
            f"/api/v1/events/{child.id}/move",
            json={"new_parent_id": parent2.id},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent_event_id"] == parent2.id
    
    def test_move_event_prevents_cycle(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test that moving event to its own descendant fails"""
        parent = Event(user_id=test_user.id, name="Parent", sort_order=0)
        test_db_session.add(parent)
        test_db_session.commit()
        
        child = Event(user_id=test_user.id, name="Child", parent_event_id=parent.id, sort_order=0)
        test_db_session.add(child)
        test_db_session.commit()
        
        # Try to move parent under child (would create cycle)
        response = client.post(
            f"/api/v1/events/{parent.id}/move",
            json={"new_parent_id": child.id},
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_delete_event(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test deleting event"""
        event = Event(user_id=test_user.id, name="To Delete", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        event_id = event.id
        
        response = client.delete(f"/api/v1/events/{event_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify deleted
        assert test_db_session.query(Event).filter_by(id=event_id).first() is None
    
    def test_delete_event_orphans_children(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test that deleting parent orphans children (sets parent_event_id to NULL)"""
        parent = Event(user_id=test_user.id, name="Parent", sort_order=0)
        test_db_session.add(parent)
        test_db_session.commit()
        
        child = Event(user_id=test_user.id, name="Child", parent_event_id=parent.id, sort_order=0)
        test_db_session.add(child)
        test_db_session.commit()
        child_id = child.id
        
        # Delete parent
        response = client.delete(f"/api/v1/events/{parent.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Child should still exist but be orphaned
        test_db_session.expire(child)
        child = test_db_session.query(Event).filter_by(id=child_id).first()
        assert child is not None
        assert child.parent_event_id is None
    
    def test_add_photos_to_event(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test adding photos to event"""
        event = Event(user_id=test_user.id, name="Test Event", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        
        photo1 = Photo(hothash="hash1", hotpreview=b"preview1", user_id=test_user.id, 
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        photo2 = Photo(hothash="hash2", hotpreview=b"preview2", user_id=test_user.id,
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        test_db_session.add_all([photo1, photo2])
        test_db_session.commit()
        
        response = client.post(
            f"/api/v1/events/{event.id}/photos",
            json={"photo_ids": [photo1.id, photo2.id]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["photos_added"] == 2
    
    def test_add_photos_to_event_idempotent(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test that adding same photo twice is idempotent"""
        event = Event(user_id=test_user.id, name="Test Event", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        
        photo = Photo(hothash="hash1", hotpreview=b"preview1", user_id=test_user.id,
                      taken_at=datetime.now(timezone.utc), input_channel_id=1)
        test_db_session.add(photo)
        test_db_session.commit()
        
        # Add first time
        response1 = client.post(
            f"/api/v1/events/{event.id}/photos",
            json={"photo_ids": [photo.id]},
            headers=auth_headers
        )
        assert response1.json()["photos_added"] == 1
        
        # Add second time (duplicate)
        response2 = client.post(
            f"/api/v1/events/{event.id}/photos",
            json={"photo_ids": [photo.id]},
            headers=auth_headers
        )
        assert response2.json()["photos_added"] == 0  # Already added
    
    def test_remove_photos_from_event(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test removing photos from event"""
        event = Event(user_id=test_user.id, name="Test Event", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        
        photo = Photo(hothash="hash1", hotpreview=b"preview1", user_id=test_user.id,
                      taken_at=datetime.now(timezone.utc), input_channel_id=1)
        test_db_session.add(photo)
        test_db_session.commit()
        
        # Add photo
        photo_event = PhotoEvent(photo_id=photo.id, event_id=event.id)
        test_db_session.add(photo_event)
        test_db_session.commit()
        
        # Remove photo
        response = client.request(
            "DELETE",
            f"/api/v1/events/{event.id}/photos",
            json={"photo_ids": [photo.id]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["photos_removed"] == 1
    
    def test_get_event_photos(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test getting photos in event"""
        event = Event(user_id=test_user.id, name="Test Event", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        
        photo1 = Photo(hothash="hash1", hotpreview=b"preview1", user_id=test_user.id,
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        photo2 = Photo(hothash="hash2", hotpreview=b"preview2", user_id=test_user.id,
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        test_db_session.add_all([photo1, photo2])
        test_db_session.commit()
        
        photo_event1 = PhotoEvent(photo_id=photo1.id, event_id=event.id)
        photo_event2 = PhotoEvent(photo_id=photo2.id, event_id=event.id)
        test_db_session.add_all([photo_event1, photo_event2])
        test_db_session.commit()
        
        response = client.get(f"/api/v1/events/{event.id}/photos", headers=auth_headers)
        assert response.status_code == 200
        photos = response.json()
        assert len(photos) == 2
    
    def test_get_event_photos_recursive(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test getting photos in event including descendants"""
        parent = Event(user_id=test_user.id, name="Parent", sort_order=0)
        test_db_session.add(parent)
        test_db_session.commit()
        
        child = Event(user_id=test_user.id, name="Child", parent_event_id=parent.id, sort_order=0)
        test_db_session.add(child)
        test_db_session.commit()
        
        photo1 = Photo(hothash="hash1", hotpreview=b"preview1", user_id=test_user.id,
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        photo2 = Photo(hothash="hash2", hotpreview=b"preview2", user_id=test_user.id,
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        test_db_session.add_all([photo1, photo2])
        test_db_session.commit()
        
        # Photo1 in parent, Photo2 in child
        test_db_session.add(PhotoEvent(photo_id=photo1.id, event_id=parent.id))
        test_db_session.add(PhotoEvent(photo_id=photo2.id, event_id=child.id))
        test_db_session.commit()
        
        # Get photos without recursion (parent only)
        response1 = client.get(
            f"/api/v1/events/{parent.id}/photos",
            headers=auth_headers
        )
        assert len(response1.json()) == 1
        
        # Get photos with recursion (parent + child)
        response2 = client.get(
            f"/api/v1/events/{parent.id}/photos?include_descendants=true",
            headers=auth_headers
        )
        assert len(response2.json()) == 2
    
    def test_event_photo_count_in_list(self, client: TestClient, test_user: User, auth_headers: dict, test_db_session: Session):
        """Test that list endpoint includes photo counts"""
        event = Event(user_id=test_user.id, name="Test Event", sort_order=0)
        test_db_session.add(event)
        test_db_session.commit()
        
        photo1 = Photo(hothash="hash1", hotpreview=b"preview1", user_id=test_user.id,
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        photo2 = Photo(hothash="hash2", hotpreview=b"preview2", user_id=test_user.id,
                       taken_at=datetime.now(timezone.utc), input_channel_id=1)
        test_db_session.add_all([photo1, photo2])
        test_db_session.commit()
        
        test_db_session.add(PhotoEvent(photo_id=photo1.id, event_id=event.id))
        test_db_session.add(PhotoEvent(photo_id=photo2.id, event_id=event.id))
        test_db_session.commit()
        
        response = client.get("/api/v1/events/", headers=auth_headers)
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["photo_count"] == 2
