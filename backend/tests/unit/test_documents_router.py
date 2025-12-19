"""
Unit tests for Documents Router
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import tempfile
from fastapi import HTTPException
from app.routers.documents import router, get_current_user
from app.models import User, Document


@pytest.mark.unit
class TestDocumentsRouter:
    """Test suite for Documents Router"""
    
    def test_get_current_user_with_token(self, db_session):
        """Test get_current_user with valid token"""
        from jose import jwt
        import os
        from datetime import datetime, timedelta
        
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create token
        expire = datetime.utcnow() + timedelta(hours=24)
        token_data = {"sub": user.email, "exp": expire}
        token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        # Mock credentials
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        result = get_current_user(credentials, db_session)
        assert result is not None
        assert result.email == user.email
    
    def test_get_current_user_without_token(self, db_session):
        """Test get_current_user without token (should return default user)"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = None
        
        result = get_current_user(credentials, db_session)
        assert result is not None
        assert result.username == "default"
    
    @patch('app.routers.documents.rag_service')
    @patch('app.routers.documents.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_document_success(
        self, mock_file, mock_exists, mock_rag_service,
        client, auth_headers, test_user, db_session, temp_dir
    ):
        """Test successful document upload"""
        import io
        
        mock_exists.return_value = True
        mock_rag_service.process_document.return_value = True
        
        # Create a mock file
        file_content = b"Test document content"
        file_obj = io.BytesIO(file_content)
        
        # Mock the file upload
        files = {"file": ("test.txt", file_obj, "text/plain")}
        
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files=files
        )
        
        # Should succeed (200 or 201)
        assert response.status_code in [200, 201]
    
    def test_upload_document_unsupported_type(self, client, auth_headers):
        """Test upload with unsupported file type"""
        import io
        
        file_content = b"Test content"
        file_obj = io.BytesIO(file_content)
        files = {"file": ("test.exe", file_obj, "application/x-msdownload")}
        
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 400
    
    @patch('app.routers.documents.os.path.exists')
    @patch('app.routers.documents.os.remove')
    def test_delete_document_success(
        self, mock_remove, mock_exists,
        client, auth_headers, test_user, db_session
    ):
        """Test successful document deletion"""
        mock_exists.return_value = True
        
        # Create a document
        document = Document(
            user_id=test_user.id,
            filename="test.txt",
            file_path="./uploads/test.txt",
            file_type="txt",
            processed=True
        )
        db_session.add(document)
        db_session.commit()
        
        response = client.delete(
            f"/api/documents/{document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_delete_document_not_found(self, client, auth_headers):
        """Test deletion of non-existent document"""
        response = client.delete(
            "/api/documents/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_documents(self, client, auth_headers, test_user, db_session):
        """Test getting user documents"""
        # Create test documents
        doc1 = Document(
            user_id=test_user.id,
            filename="doc1.txt",
            file_path="./uploads/doc1.txt",
            file_type="txt",
            processed=True
        )
        doc2 = Document(
            user_id=test_user.id,
            filename="doc2.pdf",
            file_path="./uploads/doc2.pdf",
            file_type="pdf",
            processed=False
        )
        db_session.add(doc1)
        db_session.add(doc2)
        db_session.commit()
        
        response = client.get(
            "/api/documents/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

