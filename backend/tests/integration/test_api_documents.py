"""
Integration tests for Documents API endpoints
"""
import pytest
import os
import tempfile
from fastapi import status


@pytest.mark.integration
class TestDocumentsAPI:
    """Test suite for Documents API endpoints"""
    
    def test_upload_document(self, client, auth_headers, temp_dir):
        """Test POST /api/documents/upload"""
        # Create a test TXT file
        txt_content = "Ceci est un document de test pour RAG."
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        # Upload document
        with open(txt_path, "rb") as f:
            response = client.post(
                "/api/documents/upload",
                files={"file": ("test.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "filename" in data
        assert data["filename"] == "test.txt"
        assert "file_type" in data
        assert data["file_type"] == "txt"
    
    def test_upload_document_unsupported_type(self, client, auth_headers, temp_dir):
        """Test uploading an unsupported file type"""
        # Create a test file with unsupported extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            with open(temp_path, "rb") as f:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("test.xyz", f, "application/octet-stream")},
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error_data = response.json()
            # Error handler returns "message" not "detail"
            assert "Unsupported file type" in error_data.get("message", error_data.get("detail", ""))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_get_documents(self, client, auth_headers, temp_dir):
        """Test GET /api/documents/"""
        # Upload a document first
        txt_content = "Test document for listing"
        txt_path = os.path.join(temp_dir, "test_list.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        with open(txt_path, "rb") as f:
            client.post(
                "/api/documents/upload",
                files={"file": ("test_list.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        # Get documents
        response = client.get("/api/documents/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_documents_empty(self, client, auth_headers):
        """Test GET /api/documents/ when user has no documents"""
        # Use a different user or clear documents
        response = client.get("/api/documents/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    def test_delete_document(self, client, auth_headers, temp_dir):
        """Test DELETE /api/documents/{document_id}"""
        # Upload a document first
        txt_content = "Test document for deletion"
        txt_path = os.path.join(temp_dir, "test_delete.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        with open(txt_path, "rb") as f:
            upload_response = client.post(
                "/api/documents/upload",
                files={"file": ("test_delete.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        document_id = upload_response.json()["id"]
        
        # Delete the document
        response = client.delete(
            f"/api/documents/{document_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()
        
        # Verify it's deleted
        get_response = client.get("/api/documents/", headers=auth_headers)
        document_ids = [d["id"] for d in get_response.json()]
        assert document_id not in document_ids
    
    def test_delete_nonexistent_document(self, client, auth_headers):
        """Test deleting a non-existent document"""
        response = client.delete(
            "/api/documents/99999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "Document not found" in error_data.get("message", error_data.get("detail", ""))
    
    def test_delete_document_other_user(self, client, auth_headers, test_user, db_session):
        """Test that users cannot delete other users' documents"""
        from app.models import Document, User
        from passlib.context import CryptContext
        
        # Create another user
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password=pwd_context.hash("password123")
        )
        db_session.add(other_user)
        db_session.commit()
        
        # Create a document for the other user
        document = Document(
            user_id=other_user.id,
            filename="other_user_doc.txt",
            file_path="/tmp/other_user_doc.txt",
            file_type="txt",
            processed=False
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Try to delete it as the test user
        response = client.delete(
            f"/api/documents/{document.id}",
            headers=auth_headers
        )
        
        # Should return 404 (not found for this user)
        assert response.status_code == status.HTTP_404_NOT_FOUND

