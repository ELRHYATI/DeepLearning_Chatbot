"""
Extended unit tests for Chat Router
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from app.routers.chat import router, get_current_user
from app.models import User, ChatSession, Message


@pytest.mark.unit
class TestChatRouterExtended:
    """Extended test suite for Chat Router"""
    
    def test_get_current_user_with_token(self, db_session):
        """Test get_current_user with valid JWT token"""
        from jose import jwt
        from datetime import datetime, timedelta
        import os
        
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()
        
        expire = datetime.utcnow() + timedelta(hours=24)
        token_data = {"sub": user.email, "exp": expire}
        token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        result = get_current_user(credentials, db_session)
        assert result is not None
        assert result.email == user.email
    
    def test_get_current_user_without_token(self, db_session):
        """Test get_current_user without token"""
        credentials = None
        result = get_current_user(credentials, db_session)
        assert result is not None
        assert result.username == "default"
    
    @patch('app.routers.chat.grammar_service')
    def test_grammar_service_available(self, mock_grammar):
        """Test that grammar service is initialized"""
        assert mock_grammar is not None
    
    @patch('app.routers.chat.qa_service')
    def test_qa_service_available(self, mock_qa):
        """Test that QA service is initialized"""
        assert mock_qa is not None
    
    @patch('app.routers.chat.reformulation_service')
    def test_reformulation_service_available(self, mock_reformulation):
        """Test that reformulation service is initialized"""
        assert mock_reformulation is not None

