"""
Unit tests for chat router functions
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.routers.chat import get_current_user
from app.models import User


@pytest.mark.unit
class TestChatRouterFunctions:
    """Test suite for chat router helper functions"""
    
    @patch('jose.jwt.decode')
    def test_get_current_user_with_token(self, mock_jwt_decode, db_session):
        """Test get_current_user with valid token"""
        from app.routers.chat import HTTPAuthorizationCredentials
        
        # Create mock credentials
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"
        
        # Mock JWT decode
        mock_jwt_decode.return_value = {"sub": "test@example.com"}
        
        # Create test user
        user = User(username="testuser", email="test@example.com", hashed_password="")
        db_session.add(user)
        db_session.commit()
        
        # Test function
        result = get_current_user(mock_credentials, db_session)
        assert result is not None
        assert result.email == "test@example.com"
    
    def test_get_current_user_without_token(self, db_session):
        """Test get_current_user without token (default user)"""
        result = get_current_user(None, db_session)
        assert result is not None
        assert result.username == "default"
    
    @patch('jose.jwt.decode')
    def test_get_current_user_invalid_token(self, mock_jwt_decode, db_session):
        """Test get_current_user with invalid token"""
        from app.routers.chat import HTTPAuthorizationCredentials
        from jose import JWTError
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"
        
        # Mock JWT decode to raise JWTError
        mock_jwt_decode.side_effect = JWTError("Invalid token")
        
        result = get_current_user(mock_credentials, db_session)
        # Should return default user on error
        assert result is not None
        assert result.username == "default"

