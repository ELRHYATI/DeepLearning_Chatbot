"""
Integration tests for Grammar API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
class TestGrammarAPI:
    """Test suite for Grammar API endpoints"""
    
    def test_grammar_correct_endpoint(self, client):
        """Test POST /api/grammar/correct"""
        response = client.post(
            "/api/grammar/correct",
            json={"text": "Je suis allé a la bibliothèque"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "corrected_text" in data
        assert "corrections" in data
        assert isinstance(data["corrections"], list)
    
    def test_grammar_correct_empty_text(self, client):
        """Test grammar correction with empty text"""
        response = client.post(
            "/api/grammar/correct",
            json={"text": ""}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "corrected_text" in data
    
    def test_grammar_correct_missing_text(self, client):
        """Test grammar correction with missing text field"""
        response = client.post(
            "/api/grammar/correct",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_grammar_correct_no_auth_required(self, client):
        """Test grammar correction without authentication (should work)"""
        response = client.post(
            "/api/grammar/correct",
            json={"text": "Test"}
        )
        
        # Grammar endpoint doesn't require authentication
        assert response.status_code == status.HTTP_200_OK

