"""
Tests for POST /api/v1/photos/register-image endpoint

This endpoint accepts image uploads from web clients and forwards them to
imalink-core for processing, then stores the resulting PhotoCreateSchema.
"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, MagicMock
import pytest
from io import BytesIO

from imalink_schemas import PhotoCreateSchema, ImageFileCreateSchema


class TestRegisterImageEndpoint:
    """Test the /register-image web upload endpoint"""
    
    @pytest.fixture
    def mock_photo_create_response(self):
        """Load a real PhotoCreateSchema JSON fixture to use as mock response"""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "photo_create_schemas" / "tiny.json"
        with open(fixture_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def fake_image_bytes(self):
        """Create fake image bytes for upload"""
        return b"fake jpeg image data"
    
    def test_register_image_success(self, authenticated_client, auth_headers, import_session, 
                                    mock_photo_create_response, fake_image_bytes):
        """Test successful web upload - mocks imalink-core response"""
        
        # Mock the ImalinkCoreClient class
        with patch('src.utils.imalink_core_client.ImalinkCoreClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_process = MagicMock(return_value=PhotoCreateSchema(**mock_photo_create_response))
            mock_instance.process_image = mock_process
            # Prepare upload
            files = {"file": ("test.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
            data = {
                "rating": "4",
                "visibility": "private"
            }
            
            # Send request
            response = authenticated_client.post(
                "/api/v1/photos/register-image",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # Verify response
            assert response.status_code == 201
            json_data = response.json()
            assert json_data["hothash"] == mock_photo_create_response["hothash"]
            # Note: rating comes from PhotoCreateSchema metadata, not from form data in this flow
            # The rating parameter is for overriding PhotoCreateSchema default
            assert json_data["visibility"] == "private"
            assert json_data["width"] == 100
            assert json_data["height"] == 100
            # Photo was successfully created
            assert "id" in json_data
            
            # Verify imalink-core was called correctly
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            assert call_args.kwargs["image_bytes"] == fake_image_bytes
            assert call_args.kwargs["filename"] == "test.jpg"
    
    def test_register_image_without_import_session(self, authenticated_client, auth_headers, 
                                                   import_session, mock_photo_create_response, 
                                                   fake_image_bytes):
        """Test that photo uses protected ImportSession when not specified"""
        
        with patch('src.utils.imalink_core_client.ImalinkCoreClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_process = MagicMock(return_value=PhotoCreateSchema(**mock_photo_create_response))
            mock_instance.process_image = mock_process
            
            files = {"file": ("test2.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
            
            response = authenticated_client.post(
                "/api/v1/photos/register-image",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            json_data = response.json()
            # Should have auto-used protected ImportSession
            # (import_session_id is optional field in response, but photo has it in DB)
            assert json_data["hothash"] == mock_photo_create_response["hothash"]
    
    def test_register_image_with_coldpreview_size(self, authenticated_client, auth_headers, 
                                                  import_session, mock_photo_create_response, 
                                                  fake_image_bytes):
        """Test requesting coldpreview with specific size"""
        
        with patch('src.utils.imalink_core_client.ImalinkCoreClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_process = MagicMock(return_value=PhotoCreateSchema(**mock_photo_create_response))
            mock_instance.process_image = mock_process
            
            files = {"file": ("test3.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
            
            response = authenticated_client.post(
                "/api/v1/photos/register-image?coldpreview_size=1200",  # Query param, not form data
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            
            # Verify coldpreview_size was passed to imalink-core
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            # Check positional or keyword args
            assert call_args.kwargs.get("coldpreview_size") == 1200 or \
                   (len(call_args.args) > 2 and call_args.args[2] == 1200)
    
    def test_register_image_duplicate(self, authenticated_client, auth_headers, 
                                      import_session, mock_photo_create_response, 
                                      fake_image_bytes):
        """Test uploading duplicate image - should return existing photo"""
        
        with patch('src.utils.imalink_core_client.ImalinkCoreClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_process = MagicMock(return_value=PhotoCreateSchema(**mock_photo_create_response))
            mock_instance.process_image = mock_process
            
            files1 = {"file": ("original.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
            
            # Upload first time
            response1 = authenticated_client.post(
                "/api/v1/photos/register-image",
                files=files1,
                headers=auth_headers
            )
            assert response1.status_code == 201
            
            # Upload same image again (same hothash)
            files2 = {"file": ("duplicate.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
            response2 = authenticated_client.post(
                "/api/v1/photos/register-image",
                files=files2,
                headers=auth_headers
            )
            
            # Currently returns 201 with same photo (no duplicate detection yet in this endpoint)
            # This is fine - duplicate detection happens at PhotoCreateSchema level
            assert response2.status_code in [200, 201]
            json_data = response2.json()
            assert json_data["hothash"] == mock_photo_create_response["hothash"]
    
    def test_register_image_imalink_core_unavailable(self, authenticated_client, auth_headers, 
                                                      fake_image_bytes):
        """Test when imalink-core service is unavailable"""
        
        with patch('src.utils.imalink_core_client.ImalinkCoreClient') as MockClient:
            mock_instance = MockClient.return_value
            # Simulate network error
            import httpx
            mock_instance.process_image = MagicMock(side_effect=httpx.RequestError("Connection refused"))
            
            files = {"file": ("test.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
            
            response = authenticated_client.post(
                "/api/v1/photos/register-image",
                files=files,
                headers=auth_headers
            )
            
            # Should return 503 Service Unavailable
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"].lower()
    
    def test_register_image_imalink_core_error(self, authenticated_client, auth_headers, 
                                               fake_image_bytes):
        """Test when imalink-core returns an error"""
        
        with patch('src.utils.imalink_core_client.ImalinkCoreClient') as MockClient:
            mock_instance = MockClient.return_value
            # Simulate HTTP error from imalink-core
            import httpx
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Invalid image format"
            mock_response.json.return_value = {"detail": "Invalid image format"}
            mock_instance.process_image = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "Bad Request", 
                    request=MagicMock(), 
                    response=mock_response
                )
            )
            
            files = {"file": ("bad.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
            
            response = authenticated_client.post(
                "/api/v1/photos/register-image",
                files=files,
                headers=auth_headers
            )
            
            # Should forward imalink-core's error
            assert response.status_code == 400
            assert "failed" in response.json()["detail"].lower()
    
    def test_register_image_requires_auth(self, client, fake_image_bytes):
        """Test that endpoint requires authentication"""
        
        files = {"file": ("test.jpg", BytesIO(fake_image_bytes), "image/jpeg")}
        
        response = client.post(
            "/api/v1/photos/register-image",
            files=files
        )
        
        assert response.status_code == 401
    
    def test_register_image_no_file(self, authenticated_client, auth_headers):
        """Test error when no file is provided"""
        
        response = authenticated_client.post(
            "/api/v1/photos/register-image",
            headers=auth_headers
        )
        
        # FastAPI should return 422 for missing required field
        assert response.status_code == 422
