"""
Tests for PhotoText Document visibility feature (Phase 1)

Tests four-level visibility system for PhotoText documents:
- private: Only owner
- space: Space members (Phase 2 - not yet functional, treated as private)
- authenticated: All logged-in users
- public: Everyone including anonymous
"""
import pytest


@pytest.fixture
def document_data():
    """Base PhotoText document creation data"""
    return {
        "title": "Test Document",
        "document_type": "general",
        "is_published": False,
        "content": {
            "version": "1.0",
            "documentType": "general",
            "title": "Test Document",
            "blocks": [
                {
                    "type": "heading",
                    "level": 1,
                    "text": "Test Heading"
                },
                {
                    "type": "paragraph",
                    "text": "This is a test document paragraph."
                }
            ]
        }
    }


class TestPhotoTextVisibilityDefaults:
    """Test default visibility behavior for PhotoText documents"""
    
    def test_new_document_defaults_to_private(self, authenticated_client, document_data):
        """New documents should default to visibility='private'"""
        response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        
        if response.status_code != 201:
            print(f"Error response: {response.json()}")
        assert response.status_code == 201
        data = response.json()
        assert data["visibility"] == "private"
    
    def test_document_list_includes_visibility(self, authenticated_client, document_data):
        """Document list should include visibility field"""
        # Create a document first
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        
        # List documents
        response = authenticated_client.get(
            "/api/v1/phototext",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        if len(data["documents"]) > 0:
            assert "visibility" in data["documents"][0]


class TestPhotoTextVisibilityCreation:
    """Test creating documents with different visibility levels"""
    
    def test_create_private_document(self, authenticated_client, document_data):
        """Can create document with visibility='private'"""
        document_data["visibility"] = "private"
        response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["visibility"] == "private"
    
    def test_create_authenticated_document(self, authenticated_client, document_data):
        """Can create document with visibility='authenticated'"""
        document_data["visibility"] = "authenticated"
        response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["visibility"] == "authenticated"
    
    def test_create_public_document(self, authenticated_client, document_data):
        """Can create document with visibility='public'"""
        document_data["visibility"] = "public"
        response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["visibility"] == "public"
    
    def test_create_space_document(self, authenticated_client, document_data):
        """Can create document with visibility='space' (accepted but not functional in Phase 1)"""
        document_data["visibility"] = "space"
        response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["visibility"] == "space"
    
    def test_create_document_invalid_visibility(self, authenticated_client, document_data):
        """Creating document with invalid visibility should fail"""
        document_data["visibility"] = "invalid_value"
        response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        
        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]


class TestPhotoTextVisibilityUpdate:
    """Test updating document visibility"""
    
    def test_update_visibility_to_public(self, authenticated_client, document_data):
        """Can change document visibility from private to public"""
        # Create private document
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        doc_id = create_response.json()["id"]
        
        # Update to public
        update_response = authenticated_client.put(
            f"/api/v1/phototext/{doc_id}",
            json={"visibility": "public"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code == 200
        assert update_response.json()["visibility"] == "public"
    
    def test_update_visibility_to_authenticated(self, authenticated_client, document_data):
        """Can change document visibility to authenticated"""
        # Create document
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        doc_id = create_response.json()["id"]
        
        # Update to authenticated
        update_response = authenticated_client.put(
            f"/api/v1/phototext/{doc_id}",
            json={"visibility": "authenticated"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code == 200
        assert update_response.json()["visibility"] == "authenticated"
    
    def test_update_visibility_invalid_value(self, authenticated_client, document_data):
        """Updating to invalid visibility should fail"""
        # Create document
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        doc_id = create_response.json()["id"]
        
        # Try invalid update
        update_response = authenticated_client.put(
            f"/api/v1/phototext/{doc_id}",
            json={"visibility": "invalid"},
            headers=authenticated_client.auth_headers
        )
        
        assert update_response.status_code in [400, 422]


class TestPhotoTextVisibilityAccessControl:
    """Test access control based on visibility"""
    
    def test_owner_sees_own_private_document(self, authenticated_client, document_data):
        """Owner can see their own private document"""
        # Create private document
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        doc_id = create_response.json()["id"]
        
        # Get document
        response = authenticated_client.get(
            f"/api/v1/phototext/{doc_id}",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["visibility"] == "private"
    
    def test_anonymous_cannot_see_private_document(self, client, authenticated_client, document_data):
        """Anonymous users cannot see private documents"""
        # Create private document
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        doc_id = create_response.json()["id"]
        
        # Try to access without auth
        response = client.get(f"/api/v1/phototext/{doc_id}")
        
        assert response.status_code == 404  # Returns 404 to prevent enumeration
    
    def test_anonymous_can_see_public_document(self, client, authenticated_client, document_data):
        """Anonymous users can see public documents"""
        # Create public document
        document_data["visibility"] = "public"
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        doc_id = create_response.json()["id"]
        
        # Access without auth
        response = client.get(f"/api/v1/phototext/{doc_id}")
        
        assert response.status_code == 200
        assert response.json()["visibility"] == "public"
    
    def test_anonymous_cannot_see_authenticated_document(self, client, authenticated_client, document_data):
        """Anonymous users cannot see authenticated documents"""
        # Create authenticated document
        document_data["visibility"] = "authenticated"
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        doc_id = create_response.json()["id"]
        
        # Try to access without auth
        response = client.get(f"/api/v1/phototext/{doc_id}")
        
        assert response.status_code == 404


class TestPhotoTextVisibilityListing:
    """Test document listing with visibility filtering"""
    
    def test_anonymous_list_only_shows_public(self, client, authenticated_client, document_data):
        """Anonymous users only see public documents in list"""
        # Create one private and one public document
        create_response1 = authenticated_client.post(
            "/api/v1/phototext",
            json={**document_data, "visibility": "private", "title": "Private Doc"},
            headers=authenticated_client.auth_headers
        )
        assert create_response1.status_code == 201
        
        create_response2 = authenticated_client.post(
            "/api/v1/phototext",
            json={**document_data, "visibility": "public", "title": "Public Doc"},
            headers=authenticated_client.auth_headers
        )
        assert create_response2.status_code == 201
        
        # List without auth
        response = client.get("/api/v1/phototext")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only contain public documents
        for doc in data["documents"]:
            assert doc["visibility"] == "public"
    
    def test_authenticated_user_sees_own_plus_public(self, authenticated_client, document_data):
        """Authenticated users see own documents + public documents"""
        # Create private document
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json={**document_data, "visibility": "private"},
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        
        # List with auth
        response = authenticated_client.get(
            "/api/v1/phototext",
            headers=authenticated_client.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include own private documents
        assert any(d["visibility"] == "private" for d in data["documents"])
    
    def test_authenticated_user_sees_authenticated_documents(self, authenticated_client, second_user_client, document_data):
        """Authenticated users see authenticated documents from other users"""
        # User 1 creates authenticated document
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json={**document_data, "visibility": "authenticated"},
            headers=authenticated_client.auth_headers
        )
        assert create_response.status_code == 201
        doc_id = create_response.json()["id"]
        
        # User 2 should see it
        response = second_user_client.get(
            f"/api/v1/phototext/{doc_id}",
            headers=second_user_client.auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["visibility"] == "authenticated"


class TestPhotoTextVisibilitySpacePhase1:
    """Test space visibility in Phase 1 (not yet functional)"""
    
    def test_space_visibility_treated_as_private(self, client, authenticated_client, document_data):
        """In Phase 1, space visibility should behave like private"""
        # Create space document
        document_data["visibility"] = "space"
        create_response = authenticated_client.post(
            "/api/v1/phototext",
            json=document_data,
            headers=authenticated_client.auth_headers
        )
        doc_id = create_response.json()["id"]
        
        # Anonymous user should not see it
        response = client.get(f"/api/v1/phototext/{doc_id}")
        assert response.status_code == 404
        
        # Owner should see it
        response = authenticated_client.get(
            f"/api/v1/phototext/{doc_id}",
            headers=authenticated_client.auth_headers
        )
        assert response.status_code == 200
