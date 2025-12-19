"""
Integration tests for Authentication API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
class TestAuthAPI:
    """Test suite for Authentication API endpoints"""
    
    def test_register_user(self, client):
        """Test POST /api/auth/register"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Register endpoint returns UserResponse (not Token with access_token)
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registering with duplicate email"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        
        # Should return error for duplicate email
        # Can be 400 (bad request) or 422 (validation error)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_login_success(self, client, test_user):
        """Test POST /api/auth/login with valid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user.username,
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user.username,
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

