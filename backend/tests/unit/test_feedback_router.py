"""
Unit tests for Feedback Router
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.routers.feedback import router
from app.models import User, Message, Feedback, ChatSession


@pytest.mark.unit
class TestFeedbackRouter:
    """Test suite for Feedback Router"""
    
    def test_create_feedback_success(
        self, client, auth_headers, test_user, db_session
    ):
        """Test creating feedback successfully"""
        # Create a chat session
        session = ChatSession(
            user_id=test_user.id,
            title="Test Session"
        )
        db_session.add(session)
        db_session.commit()
        
        # Create an assistant message
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
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["rating"] == 1
    
    def test_create_feedback_without_auth(self, client):
        """Test creating feedback without authentication"""
        response = client.post(
            "/api/feedback/",
            json={
                "message_id": 1,
                "rating": 1
            }
        )
        
        assert response.status_code == 401
    
    def test_create_feedback_message_not_found(
        self, client, auth_headers, test_user, db_session
    ):
        """Test creating feedback for non-existent message"""
        response = client.post(
            "/api/feedback/",
            headers=auth_headers,
            json={
                "message_id": 99999,
                "rating": 1
            }
        )
        
        assert response.status_code == 404
    
    def test_create_feedback_invalid_rating(
        self, client, auth_headers, test_user, db_session
    ):
        """Test creating feedback with invalid rating"""
        # Create session and message
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
        
        response = client.post(
            "/api/feedback/",
            headers=auth_headers,
            json={
                "message_id": message.id,
                "rating": 5  # Invalid rating
            }
        )
        
        assert response.status_code == 400
    
    def test_create_feedback_user_message(
        self, client, auth_headers, test_user, db_session
    ):
        """Test creating feedback on user message (should fail)"""
        session = ChatSession(user_id=test_user.id, title="Test")
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            role="user",  # User message
            content="Test",
            module_type="general"
        )
        db_session.add(message)
        db_session.commit()
        
        response = client.post(
            "/api/feedback/",
            headers=auth_headers,
            json={
                "message_id": message.id,
                "rating": 1
            }
        )
        
        assert response.status_code == 400
    
    def test_update_existing_feedback(
        self, client, auth_headers, test_user, db_session
    ):
        """Test updating existing feedback"""
        # Create session and message
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
        
        # Create initial feedback
        feedback = Feedback(
            message_id=message.id,
            user_id=test_user.id,
            rating=1
        )
        db_session.add(feedback)
        db_session.commit()
        
        # Update feedback
        response = client.post(
            "/api/feedback/",
            headers=auth_headers,
            json={
                "message_id": message.id,
                "rating": -1,
                "comment": "Changed my mind"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == -1
    
    def test_get_feedback_for_message(
        self, client, auth_headers, test_user, db_session
    ):
        """Test getting feedback for a message"""
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
        
        feedback = Feedback(
            message_id=message.id,
            user_id=test_user.id,
            rating=1
        )
        db_session.add(feedback)
        db_session.commit()
        
        response = client.get(
            f"/api/feedback/message/{message.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["rating"] == 1
    
    def test_get_feedback_stats(
        self, client, auth_headers, test_user, db_session
    ):
        """Test getting feedback statistics"""
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
        
        # Create some feedback
        feedback1 = Feedback(message_id=message.id, user_id=test_user.id, rating=1)
        feedback2 = Feedback(
            message_id=message.id,
            user_id=test_user.id,
            rating=-1
        )
        db_session.add(feedback1)
        db_session.add(feedback2)
        db_session.commit()
        
        response = client.get(
            "/api/feedback/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_feedbacks" in data
        assert "positive_feedbacks" in data
        assert "negative_feedbacks" in data
        assert data["total_feedbacks"] >= 2
    
    def test_delete_feedback(
        self, client, auth_headers, test_user, db_session
    ):
        """Test deleting feedback"""
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
        
        feedback = Feedback(
            message_id=message.id,
            user_id=test_user.id,
            rating=1
        )
        db_session.add(feedback)
        db_session.commit()
        
        response = client.delete(
            f"/api/feedback/{feedback.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "message" in response.json()

