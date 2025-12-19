"""
Extended integration tests for Chat API document endpoints
"""
import pytest
import os
import tempfile
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestChatAPIDocumentsExtended:
    """Extended test suite for Chat API document endpoints"""
    
    def test_upload_document_txt(self, client, auth_headers, temp_dir):
        """Test uploading a TXT document to a chat session"""
        # Create a session first
        create_response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]
        
        # Create a test TXT file
        txt_content = "Ceci est un document de test avec des erreurs grammaticaux."
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        # Upload document
        with open(txt_path, "rb") as f:
            response = client.post(
                f"/api/chat/sessions/{session_id}/documents",
                files={"file": ("test.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        # Should accept the upload (may take time to process)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]
        data = response.json()
        assert "message" in data or "original_filename" in data
    
    def test_upload_document_invalid_type(self, client, auth_headers):
        """Test uploading an unsupported file type"""
        # Create a session first
        create_response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]
        
        # Try to upload an unsupported file type
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            with open(temp_path, "rb") as f:
                response = client.post(
                    f"/api/chat/sessions/{session_id}/documents",
                    files={"file": ("test.xyz", f, "application/octet-stream")},
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error_data = response.json()
            assert "Unsupported file type" in error_data.get("message", error_data.get("detail", ""))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_download_processed_document_not_found(self, client, auth_headers):
        """Test downloading a non-existent processed document"""
        response = client.get(
            "/api/chat/download/nonexistent_file.txt",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_upload_document_to_nonexistent_session(self, client, auth_headers, temp_dir):
        """Test uploading a document to a non-existent session"""
        # Create a test TXT file
        txt_content = "Test content"
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        # Try to upload to non-existent session
        with open(txt_path, "rb") as f:
            response = client.post(
                "/api/chat/sessions/99999/documents",
                files={"file": ("test.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "Session not found" in error_data.get("message", error_data.get("detail", ""))

