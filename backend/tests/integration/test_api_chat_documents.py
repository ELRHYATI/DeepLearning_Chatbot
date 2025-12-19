"""
Integration tests for Chat API document upload endpoints
"""
import pytest
import os
import tempfile
from fastapi import status


@pytest.mark.integration
class TestChatAPIDocuments:
    """Test suite for Chat API document upload endpoints"""
    
    def test_upload_document_to_chat(self, client, auth_headers, temp_dir):
        """Test uploading document to chat session"""
        # Create a session first
        create_response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]
        
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Ceci est un document de test.")
        
        # Upload document
        with open(test_file, "rb") as f:
            response = client.post(
                f"/api/chat/sessions/{session_id}/documents",
                files={"file": ("test.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        # Should accept the upload (might process asynchronously)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]
    
    def test_upload_document_invalid_session(self, client, auth_headers, temp_dir):
        """Test uploading document to invalid session"""
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Test")
        
        # Try to upload to non-existent session
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/chat/sessions/99999/documents",
                files={"file": ("test.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

