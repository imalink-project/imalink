"""
Tests for PhotoText document and Photo visibility synchronization

When a PhotoText document is created or updated with a certain visibility level,
all photos referenced in the document should automatically be updated to match
that visibility level.
"""
import pytest
import base64
from PIL import Image
import io


@pytest.fixture
def sample_hotpreview():
    """Generate a sample 150x150 JPEG hotpreview as base64"""
    img = Image.new('RGB', (150, 150), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def make_unique_hotpreview(color_value: int = 0) -> str:
    """Generate a unique hotpreview by varying the color"""
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
        "filename": "test_sync.jpg",
        "hotpreview": sample_hotpreview,
        "file_size": 1024,
        "width": 4000,
        "height": 3000
    }


class TestPhotoTextPhotoVisibilitySync:
    """Test that PhotoText documents sync visibility to referenced photos"""
    
    def test_create_public_document_updates_photos(self, authenticated_client, photo_data):
        """Creating a public PhotoText document should make referenced photos public"""
        # Create a private photo
        photo_data_1 = {**photo_data, "hotpreview": make_unique_hotpreview(300), "visibility": "private"}
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_1,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        photo_hash = create_response.json()["photo_hothash"]
        
        # Verify photo is private
        photo_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert photo_response.status_code == 200
        assert photo_response.json()["visibility"] == "private"
        
        # Create a public PhotoText document referencing the photo
        document_data = {
            "title": "Public Album",
            "document_type": "album",
            "is_published": True,
            "visibility": "public",
            "content": {
                "version": "1.0",
                "documentType": "album",
                "title": "Public Album",
                "blocks": [
                    {
                        "type": "image",
                        "hash": photo_hash,
                        "alt": "Test image"
                    }
                ]
            }
        }
        
        doc_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        assert doc_response.status_code == 201
        assert doc_response.json()["visibility"] == "public"
        
        # Verify photo is now public
        photo_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert photo_response.status_code == 200
        assert photo_response.json()["visibility"] == "public"
    
    def test_update_document_visibility_updates_photos(self, authenticated_client, photo_data):
        """Updating a document's visibility should update referenced photos"""
        # Create a private photo
        photo_data_1 = {**photo_data, "hotpreview": make_unique_hotpreview(400), "visibility": "private"}
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_1,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        photo_hash = create_response.json()["photo_hothash"]
        
        # Create a private PhotoText document
        document_data = {
            "title": "Private Album",
            "document_type": "album",
            "is_published": False,
            "visibility": "private",
            "content": {
                "version": "1.0",
                "documentType": "album",
                "title": "Private Album",
                "blocks": [
                    {
                        "type": "image",
                        "hash": photo_hash,
                        "alt": "Test image"
                    }
                ]
            }
        }
        
        doc_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        assert doc_response.status_code == 201
        doc_id = doc_response.json()["id"]
        
        # Update document to authenticated
        update_response = authenticated_client.put(
            f"/api/v1/phototext/{doc_id}",
            json={"visibility": "authenticated"},
            headers=authenticated_client.auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["visibility"] == "authenticated"
        
        # Verify photo is now authenticated
        photo_response = authenticated_client.get(
            f"/api/v1/photos/{photo_hash}",
            headers=authenticated_client.auth_headers
        )
        assert photo_response.status_code == 200
        assert photo_response.json()["visibility"] == "authenticated"
    
    def test_document_with_multiple_photos_syncs_all(self, authenticated_client, photo_data):
        """All photos in a document should be synced to document visibility"""
        # Create three private photos with unique hotpreviews
        photo_hashes = []
        for i in range(3):
            photo_data_i = {**photo_data, "hotpreview": make_unique_hotpreview(500 + i * 100), "visibility": "private", "filename": f"photo_{i}.jpg"}
            create_response = authenticated_client.post(
                "/api/v1/photos/new-photo",
                json=photo_data_i,
                headers=authenticated_client.auth_headers
            )
            assert create_response.status_code == 201
            photo_hashes.append(create_response.json()["photo_hothash"])
        
        # Create a public collage document with all three photos
        document_data = {
            "title": "Public Collage",
            "document_type": "general",
            "is_published": True,
            "visibility": "public",
            "content": {
                "version": "1.0",
                "documentType": "general",
                "title": "Public Collage",
                "blocks": [
                    {
                        "type": "collage",
                        "layout": "grid",
                        "images": [
                            {"hash": photo_hashes[0], "alt": "Photo 1"},
                            {"hash": photo_hashes[1], "alt": "Photo 2"},
                            {"hash": photo_hashes[2], "alt": "Photo 3"}
                        ]
                    }
                ]
            }
        }
        
        doc_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        assert doc_response.status_code == 201
        
        # Verify all photos are now public
        for photo_hash in photo_hashes:
            photo_response = authenticated_client.get(
                f"/api/v1/photos/{photo_hash}",
                headers=authenticated_client.auth_headers
            )
            assert photo_response.status_code == 200
            assert photo_response.json()["visibility"] == "public"
    
    def test_anonymous_can_see_photos_in_public_document(self, client, authenticated_client, photo_data):
        """Anonymous users should see photos that are in public documents"""
        # Create a private photo
        photo_data_1 = {**photo_data, "hotpreview": make_unique_hotpreview(600), "visibility": "private"}
        create_response = authenticated_client.post(
            "/api/v1/photos/new-photo",
            json=photo_data_1,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        photo_hash = create_response.json()["photo_hothash"]
        
        # Anonymous cannot see private photo
        anon_response = client.get(f"/api/v1/photos/{photo_hash}")
        assert anon_response.status_code == 404
        
        # Create public document with the photo
        document_data = {
            "title": "Public Story",
            "document_type": "general",
            "is_published": True,
            "visibility": "public",
            "content": {
                "version": "1.0",
                "documentType": "general",
                "title": "Public Story",
                "blocks": [
                    {
                        "type": "heading",
                        "level": 1,
                        "text": "My Story"
                    },
                    {
                        "type": "image",
                        "hash": photo_hash,
                        "alt": "Story image"
                    }
                ]
            }
        }
        
        doc_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        assert doc_response.status_code == 201
        
        # Now anonymous user can see the photo
        anon_response = client.get(f"/api/v1/photos/{photo_hash}")
        assert anon_response.status_code == 200
        assert anon_response.json()["visibility"] == "public"
