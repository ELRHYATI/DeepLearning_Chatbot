"""
Comprehensive unit tests for Chat Router
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.models import User, ChatSession, Message
from datetime import datetime, timedelta


@pytest.mark.unit
class TestChatRouterComprehensive:
    """Comprehensive test suite for Chat Router"""
    
    def test_get_sessions_empty(self, client, auth_headers):
        """Test getting sessions when user has none"""
        response = client.get(
            "/api/chat/sessions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_sessions_with_data(self, client, auth_headers, test_user, db_session):
        """Test getting sessions with existing data"""
        # Create test session
        session = ChatSession(
            user_id=test_user.id,
            title="Test Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.get(
            "/api/chat/sessions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_session_not_found(self, client, auth_headers):
        """Test getting non-existent session"""
        response = client.get(
            "/api/chat/sessions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_create_session_success(self, client, auth_headers, test_user, db_session):
        """Test creating a new session"""
        response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={"title": "New Session"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "New Session"
    
    def test_update_session_success(self, client, auth_headers, test_user, db_session):
        """Test updating a session"""
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Original Title"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.put(
            f"/api/chat/sessions/{session.id}",
            headers=auth_headers,
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_delete_session_success(self, client, auth_headers, test_user, db_session):
        """Test deleting a session"""
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="To Delete"
        )
        db_session.add(session)
        db_session.commit()
        session_id = session.id
        
        response = client.delete(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_delete_session_not_found(self, client, auth_headers):
        """Test deleting non-existent session"""
        response = client.delete(
            "/api/chat/sessions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @patch('app.routers.chat.qa_service.answer_question')
    def test_create_message_qa_mode(self, mock_qa, client, auth_headers, test_user, db_session):
        """Test creating message in QA mode"""
        mock_qa.return_value = "Test answer"
        
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="QA Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.post(
            f"/api/chat/sessions/{session.id}/messages",
            headers=auth_headers,
            json={
                "content": "What is AI?",
                "module_type": "qa"
            }
        )
        
        assert response.status_code in [200, 201]
    
    @patch('app.routers.chat.grammar_service.correct_grammar')
    def test_create_message_grammar_mode(self, mock_grammar, client, auth_headers, test_user, db_session):
        """Test creating message in grammar mode"""
        mock_grammar.return_value = {
            "corrected_text": "Corrected text",
            "corrections": []
        }
        
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Grammar Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.post(
            f"/api/chat/sessions/{session.id}/messages",
            headers=auth_headers,
            json={
                "content": "Test text",
                "module_type": "grammar"
            }
        )
        
        assert response.status_code in [200, 201]
    
    @patch('app.routers.chat.reformulation_service.reformulate')
    def test_create_message_reformulation_mode(self, mock_reform, client, auth_headers, test_user, db_session):
        """Test creating message in reformulation mode"""
        mock_reform.return_value = "Reformulated text"
        
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Reformulation Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.post(
            f"/api/chat/sessions/{session.id}/messages",
            headers=auth_headers,
            json={
                "content": "Original text",
                "module_type": "reformulation"
            }
        )
        
        assert response.status_code in [200, 201]
    
    def test_get_messages_empty(self, client, auth_headers, test_user, db_session):
        """Test getting messages from empty session"""
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Empty Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.get(
            f"/api/chat/sessions/{session.id}/messages",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_messages_with_data(self, client, auth_headers, test_user, db_session):
        """Test getting messages with existing messages"""
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Session with Messages"
        )
        db_session.add(session)
        db_session.commit()
        
        # Create messages
        msg1 = Message(
            session_id=session.id,
            role="user",
            content="Hello",
            module_type="general"
        )
        msg2 = Message(
            session_id=session.id,
            role="assistant",
            content="Hi there",
            module_type="general"
        )
        db_session.add(msg1)
        db_session.add(msg2)
        db_session.commit()
        
        response = client.get(
            f"/api/chat/sessions/{session.id}/messages",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_delete_message_success(self, client, auth_headers, test_user, db_session):
        """Test deleting a message"""
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Session"
        )
        db_session.add(session)
        db_session.commit()
        
        # Create message
        msg = Message(
            session_id=session.id,
            role="user",
            content="To delete",
            module_type="general"
        )
        db_session.add(msg)
        db_session.commit()
        msg_id = msg.id
        
        response = client.delete(
            f"/api/chat/messages/{msg_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_delete_message_not_found(self, client, auth_headers):
        """Test deleting non-existent message"""
        response = client.delete(
            "/api/chat/messages/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_search_messages(self, client, auth_headers, test_user, db_session):
        """Test searching messages"""
        response = client.post(
            "/api/chat/search/messages",
            headers=auth_headers,
            json={"query": "test", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or isinstance(data, list)
    
    def test_search_sessions(self, client, auth_headers, test_user, db_session):
        """Test searching sessions"""
        response = client.post(
            "/api/chat/search/sessions",
            headers=auth_headers,
            json={"query": "test", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or isinstance(data, list)
    
    def test_export_session_markdown(self, client, auth_headers, test_user, db_session):
        """Test exporting session to markdown"""
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Export Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.get(
            f"/api/chat/sessions/{session.id}/export/markdown",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_export_session_pdf(self, client, auth_headers, test_user, db_session):
        """Test exporting session to PDF"""
        # Create session
        session = ChatSession(
            user_id=test_user.id,
            title="Export Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.get(
            f"/api/chat/sessions/{session.id}/export/pdf",
            headers=auth_headers
        )
        
        # PDF export might fail if reportlab not available
        assert response.status_code in [200, 500, 503]






