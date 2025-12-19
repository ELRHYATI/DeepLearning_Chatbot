"""
Extended integration tests for Chat API to improve coverage
"""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestChatAPIExtended:
    """Extended test suite for Chat API endpoints"""
    
    def test_create_message_grammar_mode(self, client, auth_headers):
        """Test creating message in grammar mode"""
        # Create session
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "Grammar Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]
        
        # Create message in grammar mode
        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "Je suis allé a la bibliothèque",
                "module_type": "grammar"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
    
    def test_create_message_qa_mode(self, client, auth_headers):
        """Test creating message in QA mode"""
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "QA Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]
        
        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "Qu'est-ce que la photosynthèse?",
                "module_type": "qa"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
    
    def test_create_message_reformulation_mode(self, client, auth_headers):
        """Test creating message in reformulation mode"""
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "Reformulation Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]
        
        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "C'est une bonne idée.",
                "module_type": "reformulation"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
    
    def test_get_session_not_found(self, client, auth_headers):
        """Test getting non-existent session"""
        response = client.get(
            "/api/chat/sessions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_message_invalid_session(self, client, auth_headers):
        """Test creating message in non-existent session"""
        response = client.post(
            "/api/chat/sessions/99999/messages",
            json={
                "content": "Test",
                "module_type": "general"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_session_with_title(self, client, auth_headers):
        """Test creating session with custom title"""
        response = client.post(
            "/api/chat/sessions",
            json={"title": "Custom Title Session"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Custom Title Session"
    
    def test_create_session_without_title(self, client, auth_headers):
        """Test creating session without title (should use default)"""
        response = client.post(
            "/api/chat/sessions",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "title" in data
    
    def test_create_message_greeting(self, client, auth_headers):
        """Test creating a greeting message"""
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "Greeting Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]
        
        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "Bonjour",
                "module_type": "general"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
    
    def test_create_message_conversational(self, client, auth_headers):
        """Test creating a conversational question"""
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "Conversational Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]
        
        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "Vous pouvez m'aider?",
                "module_type": "general"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
    
    def test_create_message_scientific_mode(self, client, auth_headers):
        """Test creating message in scientific writing mode"""
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "Scientific Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]
        
        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "Aide-moi à écrire scientifiquement",
                "module_type": "general"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data