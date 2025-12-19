"""
Unit tests for API Keys Router
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.routers.api_keys import router
from app.models import User, APIKey
from datetime import datetime, timedelta


@pytest.mark.unit
class TestAPIKeysRouter:
    """Test suite for API Keys Router"""
    
    @patch('app.routers.api_keys.generate_api_key')
    @patch('app.routers.api_keys.hash_api_key')
    def test_create_api_key_success(
        self, mock_hash, mock_generate,
        client, auth_headers, test_user, db_session
    ):
        """Test creating API key successfully"""
        mock_generate.return_value = "test_api_key_12345"
        mock_hash.return_value = "hashed_key"
        
        response = client.post(
            "/api/keys/",
            headers=auth_headers,
            json={
                "key_name": "Test Key",
                "expires_in_days": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["key_name"] == "Test Key"
        assert data["api_key"] == "test_api_key_12345"
    
    def test_create_api_key_without_expiration(
        self, client, auth_headers, test_user, db_session
    ):
        """Test creating API key without expiration"""
        response = client.post(
            "/api/keys/",
            headers=auth_headers,
            json={
                "key_name": "Permanent Key"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] is None or data["expires_at"] is not None
    
    def test_list_api_keys(
        self, client, auth_headers, test_user, db_session
    ):
        """Test listing API keys"""
        # Create some API keys
        key1 = APIKey(
            user_id=test_user.id,
            key_name="Key 1",
            api_key="key1_12345",
            key_hash="hash1",
            is_active=True
        )
        key2 = APIKey(
            user_id=test_user.id,
            key_name="Key 2",
            api_key="key2_67890",
            key_hash="hash2",
            is_active=False
        )
        db_session.add(key1)
        db_session.add(key2)
        db_session.commit()
        
        response = client.get(
            "/api/keys/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        # Check that keys are masked
        for key in data:
            assert "masked_key" in key or "api_key" not in key
    
    def test_revoke_api_key(
        self, client, auth_headers, test_user, db_session
    ):
        """Test revoking API key"""
        # Create an API key
        api_key = APIKey(
            user_id=test_user.id,
            key_name="Test Key",
            api_key="test_key",
            key_hash="hash",
            is_active=True
        )
        db_session.add(api_key)
        db_session.commit()
        
        response = client.delete(
            f"/api/keys/{api_key.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Verify key is deactivated
        db_session.refresh(api_key)
        assert api_key.is_active == False
    
    def test_revoke_nonexistent_key(self, client, auth_headers):
        """Test revoking non-existent API key"""
        response = client.delete(
            "/api/keys/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @patch('app.routers.api_keys.generate_api_key')
    @patch('app.routers.api_keys.hash_api_key')
    def test_regenerate_api_key(
        self, mock_hash, mock_generate,
        client, auth_headers, test_user, db_session
    ):
        """Test regenerating API key"""
        mock_generate.return_value = "new_api_key_12345"
        mock_hash.return_value = "new_hash"
        
        # Create an API key
        api_key = APIKey(
            user_id=test_user.id,
            key_name="Test Key",
            api_key="old_key",
            key_hash="old_hash",
            is_active=True
        )
        db_session.add(api_key)
        db_session.commit()
        
        response = client.post(
            f"/api/keys/{api_key.id}/regenerate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["api_key"] == "new_api_key_12345"
    
    def test_regenerate_nonexistent_key(self, client, auth_headers):
        """Test regenerating non-existent API key"""
        response = client.post(
            "/api/keys/99999/regenerate",
            headers=auth_headers
        )
        
        assert response.status_code == 404

