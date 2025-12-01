"""
Tests for Photo visibility feature (Phase 1)

Tests visibility UPDATE and ACCESS CONTROL only.
Photo creation with visibility is tested in test_real_photo_create_schema_usage.py
"""
import pytest
from tests.fixtures.real_photo_create_schemas import load_photo_create_schema, BASIC


class TestPhotoVisibilityUpdate:
    """Test updating photo visibility"""
    
    def test_update_visibility_to_public(self, authenticated_client, input_channel):
        """Update photo visibility from private to public"""
        # Create private photo via PhotoCreateSchema
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="private",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        photo = create_response.json()
        photo_hash = photo["hothash"]
        
        # Update to public
        update_response = authenticated_client.put(
            f"/api/v1/photos/{photo_hash}",
            json={"visibility": "public"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code == 200
        updated_photo = update_response.json()
        assert updated_photo["visibility"] == "public"
    
    def test_update_visibility_to_authenticated(self, authenticated_client, input_channel):
        """Update photo visibility to authenticated"""
        # Create private photo
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="private",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        photo_hash = create_response.json()["hothash"]
        
        # Update to authenticated
        update_response = authenticated_client.put(
            f"/api/v1/photos/{photo_hash}",
            json={"visibility": "authenticated"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code == 200
        assert update_response.json()["visibility"] == "authenticated"
    
    def test_update_visibility_invalid_value(self, authenticated_client, input_channel):
        """Updating with invalid visibility should fail"""
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="private",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        photo_hash = create_response.json()["hothash"]
        
        # Try invalid visibility
        update_response = authenticated_client.put(
            f"/api/v1/photos/{photo_hash}",
            json={"visibility": "invalid_level"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code in [400, 422]


class TestPhotoVisibilityAccessControl:
    """Test who can see photos based on visibility level"""
    
    def test_owner_sees_own_private_photo(self, authenticated_client, input_channel):
        """Owner can see their own private photos"""
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="private",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        photo_hash = create_response.json()["hothash"]
        
        # Owner can retrieve it
        get_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        
        assert get_response.status_code == 200
        assert get_response.json()["visibility"] == "private"
    
    def test_anonymous_cannot_see_private_photo(self, client, authenticated_client, input_channel):
        """Anonymous users cannot see private photos"""
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="private",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        photo_hash = create_response.json()["hothash"]
        
        # Anonymous cannot see it
        get_response = client.get(f"/api/v1/photos/{photo_hash}")
        assert get_response.status_code == 404
    
    def test_anonymous_can_see_public_photo(self, client, authenticated_client, input_channel):
        """Anonymous users CAN see public photos"""
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="public",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        photo_hash = create_response.json()["hothash"]
        
        # Anonymous CAN see it
        get_response = client.get(f"/api/v1/photos/{photo_hash}")
        assert get_response.status_code == 200
        assert get_response.json()["visibility"] == "public"
    
    def test_anonymous_cannot_see_authenticated_photo(self, client, authenticated_client, input_channel):
        """Anonymous users cannot see authenticated-only photos"""
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="authenticated",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        photo_hash = create_response.json()["hothash"]
        
        # Anonymous cannot see it
        get_response = client.get(f"/api/v1/photos/{photo_hash}")
        assert get_response.status_code == 404


class TestPhotoVisibilitySpacePhase1:
    """Test space visibility (Phase 1 - treated as private)"""
    
    def test_space_visibility_treated_as_private(self, client, authenticated_client, input_channel):
        """In Phase 1, space visibility behaves like private"""
        photo_create_data = load_photo_create_schema(
            BASIC,
            
            rating=0,
            visibility="space",
            input_channel_id=input_channel.id
        )
        create_response = authenticated_client.post(
            "/api/v1/photos/create",
            json={
                "photo_create_schema": photo_create_data,
                "tags": []
            },
            headers=authenticated_client.auth_headers
        )
        photo_hash = create_response.json()["hothash"]
        
        # Anonymous cannot see space photos (like private)
        get_response = client.get(f"/api/v1/photos/{photo_hash}")
        assert get_response.status_code == 404
