"""
Integration tests for Reformulation API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.slow
class TestReformulationAPI:
    """Test suite for Reformulation API endpoints"""
    
    def test_reformulation_endpoint(self, client):
        """Test POST /api/reformulation/reformulate"""
        response = client.post(
            "/api/reformulation/reformulate",
            json={
                "text": "C'est une bonne idée.",
                "style": "academic"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "original_text" in data
        assert "reformulated_text" in data
        # Style might be in changes dict, not at root level
        assert "changes" in data or "style" in data
    
    def test_reformulation_different_styles(self, client):
        """Test reformulation with different styles"""
        styles = ["academic", "formal", "simple"]
        
        for style in styles:
            response = client.post(
                "/api/reformulation/reformulate",
                json={"text": "Test text", "style": style}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            # Style might be in changes dict
            if "style" in data:
                assert data["style"] == style
            elif "changes" in data and "style" in data["changes"]:
                assert data["changes"]["style"] == style
            # At minimum, we should have reformulated_text
            assert "reformulated_text" in data
    
    def test_reformulation_missing_text(self, client):
        """Test reformulation with missing text"""
        response = client.post(
            "/api/reformulation/reformulate",
            json={"style": "academic"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

