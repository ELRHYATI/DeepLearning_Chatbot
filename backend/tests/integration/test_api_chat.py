"""
Integration tests for Chat API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
class TestChatAPI:
    """Test suite for Chat API endpoints"""
    
    def test_create_session(self, client, auth_headers):
        """Test POST /api/chat/sessions"""
        response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert data["title"] == "Test Session"
    
    def test_get_sessions(self, client, auth_headers):
        """Test GET /api/chat/sessions"""
        # Create a session first
        client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        
        response = client.get("/api/chat/sessions", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_session_by_id(self, client, auth_headers):
        """Test GET /api/chat/sessions/{id}"""
        # Create a session
        create_response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]
        
        # Get the session
        response = client.get(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == session_id
        assert "messages" in data
    
    def test_create_message(self, client, auth_headers):
        """Test POST /api/chat/sessions/{id}/messages"""
        # Create a session first
        create_response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]
        
        # Create a message (not a greeting to avoid greeting response)
        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "Qu'est-ce que l'ADN?",
                "module_type": "qa"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        # The response should contain message data
        # It might be a single message or a dict with messages
        assert isinstance(data, dict)
        # Check that we have either content or messages
        assert "content" in data or "messages" in data or "answer" in data
    
    def test_delete_session(self, client, auth_headers):
        """Test DELETE /api/chat/sessions/{id}"""
        # Create a session
        create_response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]
        
        # Delete the session
        response = client.delete(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify it's deleted
        get_response = client.get(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

