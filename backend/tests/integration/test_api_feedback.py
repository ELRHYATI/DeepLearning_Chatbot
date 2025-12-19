"""
Integration tests for Feedback API endpoints
"""
import pytest
from fastapi import status
from app.models import User, ChatSession, Message, Feedback


@pytest.mark.integration
class TestFeedbackAPI:
    """Test suite for Feedback API endpoints"""
    
    def test_create_feedback_flow(self, client, auth_headers, test_user, db_session):
        """Test complete feedback creation flow"""
        # Create session and message
        session = ChatSession(user_id=test_user.id, title="Test Session")
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            role="assistant",
            content="Test response",
            module_type="general"
        )
        db_session.add(message)
        db_session.commit()
        
        # Create feedback
        response = client.post(
            "/api/feedback/",
            headers=auth_headers,
            json={
                "message_id": message.id,
                "rating": 1,
                "comment": "Great response!"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rating"] == 1
        assert data["comment"] == "Great response!"
        
        # Get feedback
        get_response = client.get(
            f"/api/feedback/message/{message.id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == status.HTTP_200_OK
        feedback_data = get_response.json()
        assert feedback_data["rating"] == 1
    
    def test_feedback_stats(self, client, auth_headers, test_user, db_session):
        """Test feedback statistics"""
        session = ChatSession(user_id=test_user.id, title="Test")
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            role="assistant",
            content="Test",
            module_type="general"
        )
        db_session.add(message)
        db_session.commit()
        
        # Create multiple feedbacks
        for rating in [1, 1, -1]:
            feedback = Feedback(
                message_id=message.id,
                user_id=test_user.id,
                rating=rating
            )
            db_session.add(feedback)
        db_session.commit()
        
        response = client.get(
            "/api/feedback/stats",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_feedbacks"] >= 3
        assert data["positive_feedbacks"] >= 2
        assert data["negative_feedbacks"] >= 1

