"""
Integration tests for API Keys endpoints
"""
import pytest
from fastapi import status
from app.models import User, APIKey


@pytest.mark.integration
class TestAPIKeysAPI:
    """Test suite for API Keys API endpoints"""
    
    def test_create_and_list_api_keys(self, client, auth_headers, test_user, db_session):
        """Test creating and listing API keys"""
        # Create API key
        create_response = client.post(
            "/api/keys/",
            headers=auth_headers,
            json={
                "key_name": "Test Key",
                "expires_in_days": 30
            }
        )
        
        assert create_response.status_code == status.HTTP_200_OK
        create_data = create_response.json()
        assert "api_key" in create_data
        assert create_data["key_name"] == "Test Key"
        
        # List API keys
        list_response = client.get(
            "/api/keys/",
            headers=auth_headers
        )
        
        assert list_response.status_code == status.HTTP_200_OK
        list_data = list_response.json()
        assert isinstance(list_data, list)
        assert len(list_data) >= 1
    
    def test_revoke_api_key(self, client, auth_headers, test_user, db_session):
        """Test revoking an API key"""
        # Create API key first
        create_response = client.post(
            "/api/keys/",
            headers=auth_headers,
            json={"key_name": "Key to Revoke"}
        )
        key_id = create_response.json()["id"]
        
        # Revoke it
        revoke_response = client.delete(
            f"/api/keys/{key_id}",
            headers=auth_headers
        )
        
        assert revoke_response.status_code == status.HTTP_200_OK
        
        # Verify it's deactivated
        list_response = client.get(
            "/api/keys/",
            headers=auth_headers
        )
        keys = list_response.json()
        revoked_key = next((k for k in keys if k["id"] == key_id), None)
        assert revoked_key is not None
        assert revoked_key["is_active"] == False
    
    def test_regenerate_api_key(self, client, auth_headers, test_user, db_session):
        """Test regenerating an API key"""
        # Create API key
        create_response = client.post(
            "/api/keys/",
            headers=auth_headers,
            json={"key_name": "Key to Regenerate"}
        )
        key_id = create_response.json()["id"]
        original_key = create_response.json()["api_key"]
        
        # Regenerate
        regenerate_response = client.post(
            f"/api/keys/{key_id}/regenerate",
            headers=auth_headers
        )
        
        assert regenerate_response.status_code == status.HTTP_200_OK
        new_key = regenerate_response.json()["api_key"]
        assert new_key != original_key

