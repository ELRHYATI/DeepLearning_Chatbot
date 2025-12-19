"""
Integration tests for Statistics API endpoints
"""
import pytest
from fastapi import status
from app.models import User, ChatSession, Message


@pytest.mark.integration
class TestStatisticsAPI:
    """Test suite for Statistics API endpoints"""
    
    def test_get_statistics_authenticated(self, client, auth_headers, test_user, db_session):
        """Test GET /api/statistics/stats with authenticated user"""
        # Create some test data
        session = ChatSession(user_id=test_user.id, title="Test Session")
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            role="user",
            content="Test message",
            module_type="general"
        )
        db_session.add(message)
        db_session.commit()
        
        response = client.get(
            "/api/statistics/stats?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_messages" in data
        assert "total_sessions" in data
        assert data["total_sessions"] >= 1
    
    def test_get_statistics_unauthenticated(self, client):
        """Test GET /api/statistics/stats without authentication"""
        response = client.get("/api/statistics/stats?days=30")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_messages"] == 0
    
    def test_get_trends_authenticated(self, client, auth_headers, test_user, db_session):
        """Test GET /api/statistics/stats/trends with authenticated user"""
        response = client.get(
            "/api/statistics/stats/trends?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # API returns messages_trend or daily_activity depending on implementation
        assert "messages_trend" in data or "daily_activity" in data
        assert "module_trends" in data
    
    def test_get_performance_authenticated(self, client, auth_headers, test_user, db_session):
        """Test GET /api/statistics/stats/performance with authenticated user"""
        response = client.get(
            "/api/statistics/stats/performance",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "most_used_module" in data
        assert "average_messages_per_session" in data

