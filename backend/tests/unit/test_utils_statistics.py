"""
Unit tests for Statistics utilities
"""
import pytest
from unittest.mock import Mock, patch
from app.utils.statistics import (
    get_user_statistics,
    get_usage_trends,
    get_performance_metrics
)
from app.models import User, ChatSession, Message


@pytest.mark.unit
class TestStatisticsUtils:
    """Test suite for Statistics utilities"""
    
    def test_get_user_statistics(self, db_session, test_user):
        """Test getting user statistics"""
        # Create test data
        session = ChatSession(user_id=test_user.id, title="Test")
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            role="user",
            content="Test",
            module_type="general"
        )
        db_session.add(message)
        db_session.commit()
        
        stats = get_user_statistics(db_session, test_user.id, days=30)
        
        assert isinstance(stats, dict)
        assert "total_messages" in stats
        assert "total_sessions" in stats
        assert stats["total_sessions"] >= 1
    
    def test_get_usage_trends(self, db_session, test_user):
        """Test getting usage trends"""
        trends = get_usage_trends(db_session, test_user.id, days=30)
        
        assert isinstance(trends, dict)
        assert "messages_trend" in trends or "daily_activity" in trends
        assert "module_trends" in trends
    
    def test_get_performance_metrics(self, db_session, test_user):
        """Test getting performance metrics"""
        metrics = get_performance_metrics(db_session, test_user.id)
        
        assert isinstance(metrics, dict)
        assert "most_used_module" in metrics
        assert "average_messages_per_session" in metrics

