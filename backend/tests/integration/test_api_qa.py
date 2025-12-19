"""
Integration tests for QA API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.slow
class TestQAAPI:
    """Test suite for QA API endpoints"""
    
    def test_qa_answer_endpoint(self, client):
        """Test POST /api/qa/answer"""
        response = client.post(
            "/api/qa/answer",
            json={
                "question": "Qu'est-ce que la photosynthèse?",
                "context": "La photosynthèse est un processus biologique."
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert "confidence" in data
        assert "sources" in data
        assert isinstance(data["confidence"], float)
        assert 0 <= data["confidence"] <= 1
    
    def test_qa_answer_without_context(self, client):
        """Test QA without context"""
        response = client.post(
            "/api/qa/answer",
            json={"question": "Qu'est-ce que l'ADN?"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
    
    def test_qa_answer_missing_question(self, client):
        """Test QA with missing question"""
        response = client.post(
            "/api/qa/answer",
            json={}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_qa_answer_empty_question(self, client):
        """Test QA with empty question"""
        response = client.post(
            "/api/qa/answer",
            json={"question": ""}
        )
        
        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

