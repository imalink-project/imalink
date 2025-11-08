"""
Tests for Photo visibility feature (Phase 1)

Tests four-level visibility system:
- private: Only owner
- space: Space members (Phase 2 - not yet functional, treated as private)
- authenticated: All logged-in users
- public: Everyone including anonymous
"""
import pytest
import base64
from PIL import Image
import io


@pytest.fixture
def sample_hotpreview():
    """Generate a sample 150x150 JPEG hotpreview as base64"""
    img = Image.new('RGB', (150, 150), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def make_unique_hotpreview(color_value: int = 0) -> str:
    """Generate a unique hotpreview by varying the color"""
    # Use RGB values to create unique images
    r = color_value % 256
    g = (color_value // 256) % 256
    b = (color_value // 65536) % 256
    img = Image.new('RGB', (150, 150), color=(r, g, b))
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


@pytest.fixture
def photo_data(sample_hotpreview):
    """Base photo creation data"""
    return {
        "hothash": "base_test_hash",
        "filename": "test_visibility.jpg",
        "hotpreview": sample_hotpreview,
        "file_size": 1024,
        "width": 4000,
        "height": 3000
    }


class TestPhotoVisibilityDefaults:
    """Test default visibility behavior"""
    
    def test_new_photo_defaults_to_private(self, authenticated_client, photo_data):
        """New photos should default to visibility='private'"""
        response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] == True
        assert data["photo_created"] == True
        
        # Get the photo to check its visibility
        photo_hash = data["photo_hothash"]
        get_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert get_response.status_code == 200
        photo = get_response.json()
        assert photo["visibility"] == "private"
    
    def test_photo_list_includes_visibility(self, authenticated_client, photo_data):
        """Photo list should include visibility field"""
        # Create a photo first
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        
        # List photos
        response = authenticated_client.get(
            "/api/v1/photos/",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
        assert "visibility" in data["data"][0]


class TestPhotoVisibilityCreation:
    """Test creating photos with different visibility levels"""
    
    def test_create_private_photo(self, authenticated_client, photo_data):
        """Can create photo with visibility='private'"""
        photo_data["visibility"] = "private"
        response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        photo_hash = response.json()["photo_hothash"]
        
        # Get the photo to verify visibility
        get_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["visibility"] == "private"
    
    def test_create_authenticated_photo(self, authenticated_client, photo_data):
        """Can create photo with visibility='authenticated'"""
        photo_data["visibility"] = "authenticated"
        photo_data["hothash"] = "auth_" + photo_data["hothash"]  # Unique hash
        response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        photo_hash = response.json()["photo_hothash"]
        
        # Get the photo to verify visibility
        get_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["visibility"] == "authenticated"
    
    def test_create_public_photo(self, authenticated_client, photo_data):
        """Can create photo with visibility='public'"""
        photo_data["visibility"] = "public"
        photo_data["hothash"] = "public_" + photo_data["hothash"]  # Unique hash
        response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        photo_hash = response.json()["photo_hothash"]
        
        # Get the photo to verify visibility
        get_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["visibility"] == "public"
    
    def test_create_space_photo(self, authenticated_client, photo_data):
        """Can create photo with visibility='space' (accepted but not functional in Phase 1)"""
        photo_data["visibility"] = "space"
        photo_data["hothash"] = "space_" + photo_data["hothash"]  # Unique hash
        response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        photo_hash = response.json()["photo_hothash"]
        
        # Get the photo to verify visibility
        get_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["visibility"] == "space"
    
    def test_create_photo_invalid_visibility(self, authenticated_client, photo_data):
        """Creating photo with invalid visibility should fail"""
        photo_data["visibility"] = "invalid_value"
        photo_data["hothash"] = "invalid_" + photo_data["hothash"]  # Unique hash
        response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        
        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]


class TestPhotoVisibilityUpdate:
    """Test updating photo visibility"""
    
    def test_update_visibility_to_public(self, authenticated_client, photo_data):
        """Can change photo visibility from private to public"""
        # Create private photo
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        hothash = create_response.json()["photo_hothash"]
        
        # Update to public
        update_response = authenticated_client.put(
            f"/api/v1/photos/{hothash}",
            json={"visibility": "public"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code == 200
        assert update_response.json()["visibility"] == "public"
    
    def test_update_visibility_to_authenticated(self, authenticated_client, photo_data):
        """Can change photo visibility to authenticated"""
        # Create photo
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        hothash = create_response.json()["photo_hothash"]
        
        # Update to authenticated
        update_response = authenticated_client.put(
            f"/api/v1/photos/{hothash}",
            json={"visibility": "authenticated"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code == 200
        assert update_response.json()["visibility"] == "authenticated"
    
    def test_update_visibility_invalid_value(self, authenticated_client, photo_data):
        """Updating to invalid visibility should fail"""
        # Create photo
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        hothash = create_response.json()["photo_hothash"]
        
        # Try invalid update
        update_response = authenticated_client.put(
            f"/api/v1/photos/{hothash}",
            json={"visibility": "invalid"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code in [400, 422]


class TestPhotoVisibilityAccessControl:
    """Test access control based on visibility"""
    
    def test_owner_sees_own_private_photo(self, authenticated_client, photo_data):
        """Owner can see their own private photo"""
        # Create private photo
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        hothash = create_response.json()["photo_hothash"]
        
        # Get photo
        response = authenticated_client.get(
            f"/api/v1/photos/{hothash}",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["visibility"] == "private"
    
    def test_anonymous_cannot_see_private_photo(self, client, authenticated_client, photo_data):
        """Anonymous users cannot see private photos"""
        # Create private photo
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        hothash = create_response.json()["photo_hothash"]
        
        # Try to access without auth
        response = client.get(f"/api/v1/photos/{hothash}")
        
        assert response.status_code == 404  # Returns 404 to prevent enumeration
    
    def test_anonymous_can_see_public_photo(self, client, authenticated_client, photo_data):
        """Anonymous users can see public photos"""
        # Create public photo
        photo_data["visibility"] = "public"
        photo_data["hothash"] = "anon_public_" + photo_data["hothash"]  # Unique hash
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        hothash = create_response.json()["photo_hothash"]
        
        # Access without auth
        response = client.get(f"/api/v1/photos/{hothash}")
        
        assert response.status_code == 200
        assert response.json()["visibility"] == "public"
    
    def test_anonymous_cannot_see_authenticated_photo(self, client, authenticated_client, photo_data):
        """Anonymous users cannot see authenticated photos"""
        # Create authenticated photo
        photo_data["visibility"] = "authenticated"
        photo_data["hothash"] = "anon_auth_" + photo_data["hothash"]  # Unique hash
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data,
            headers=authenticated_client.auth_headers
        )
        hothash = create_response.json()["photo_hothash"]
        
        # Try to access without auth
        response = client.get(f"/api/v1/photos/{hothash}")
        
        assert response.status_code == 404


class TestPhotoVisibilityListing:
    """Test photo listing with visibility filtering"""
    
    def test_anonymous_list_only_shows_public(self, client, authenticated_client, photo_data):
        """Anonymous users only see public photos in list"""
        # Create one private and one public photo with unique hotpreviews
        photo_data_private = {
            **photo_data,
            "hotpreview": make_unique_hotpreview(100),
            "visibility": "private"
        }
        create_response1 = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_private,
            headers=authenticated_client.auth_headers
        )
        assert create_response1.status_code == 201
        
        photo_data_public = {
            **photo_data,
            "hotpreview": make_unique_hotpreview(200),
            "visibility": "public",
            "filename": "public.jpg"
        }
        create_response2 = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_public,
            headers=authenticated_client.auth_headers
        )
        assert create_response2.status_code == 201
        
        # List without auth
        response = client.get("/api/v1/photos/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only contain public photos
        for photo in data["data"]:
            assert photo["visibility"] == "public"
    
    def test_authenticated_user_sees_own_plus_public(self, authenticated_client, photo_data):
        """Authenticated users see own photos + public photos"""
        # Create private photo with unique hash
        photo_data_own = {**photo_data, "hothash": "own_private_" + photo_data["hothash"], "visibility": "private"}
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_own,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        
        # List with auth
        response = authenticated_client.get(
            "/api/v1/photos/",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include own private photos
        assert any(p["visibility"] == "private" for p in data["data"])
    
    def test_authenticated_user_sees_authenticated_photos(self, authenticated_client, second_user_client, photo_data):
        """Authenticated users see authenticated photos from other users"""
        # User 1 creates authenticated photo with unique hash
        photo_data_auth = {**photo_data, "hothash": "user1_auth_" + photo_data["hothash"], "visibility": "authenticated"}
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_auth,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        hothash = create_response.json()["photo_hothash"]
        
        # User 2 should see it
        response = second_user_client.get(
            f"/api/v1/photos/{hothash}",
            headers=second_user_client.auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["visibility"] == "authenticated"


class TestPhotoVisibilitySpacePhase1:
    """Test space visibility in Phase 1 (not yet functional)"""
    
    def test_space_visibility_treated_as_private(self, client, authenticated_client, photo_data):
        """In Phase 1, space visibility should behave like private"""
        # Create space photo with unique hash
        photo_data_space = {**photo_data, "hothash": "space_phase1_" + photo_data["hothash"], "visibility": "space"}
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_space,
            headers=authenticated_client.auth_headers
        )
        hothash = create_response.json()["photo_hothash"]
        
        # Anonymous user should not see it
        response = client.get(f"/api/v1/photos/{hothash}")
        assert response.status_code == 404
        
        # Owner should see it
        response = authenticated_client.get(
            f"/api/v1/photos/{hothash}",
            headers=authenticated_client.auth_headers
        )
        assert response.status_code == 200
