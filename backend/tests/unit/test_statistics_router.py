"""
Unit tests for Statistics Router
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from app.routers.statistics import get_empty_stats, router
from app.models import User, ChatSession, Message


@pytest.mark.unit
class TestStatisticsRouter:
    """Test suite for Statistics Router"""
    
    def test_get_empty_stats(self):
        """Test that get_empty_stats returns correct structure"""
        stats = get_empty_stats()
        
        assert isinstance(stats, dict)
        assert "total_messages" in stats
        assert "total_sessions" in stats
        assert "shared_sessions" in stats
        assert "total_documents" in stats
        assert "recent_activity" in stats
        assert "module_usage" in stats
        assert stats["total_messages"] == 0
        assert stats["total_sessions"] == 0
        assert isinstance(stats["module_usage"], dict)
    
    @patch('app.routers.statistics.get_user_statistics')
    def test_get_statistics_with_user(self, mock_get_stats, client, auth_headers, test_user):
        """Test GET /api/statistics/stats with authenticated user"""
        mock_get_stats.return_value = {
            "total_messages": 10,
            "total_sessions": 5,
            "module_usage": {"grammar": 3, "qa": 7}
        }
        
        response = client.get(
            "/api/statistics/stats?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_messages" in data
        assert data["total_messages"] == 10
        mock_get_stats.assert_called_once()
    
    def test_get_statistics_without_user(self, client):
        """Test GET /api/statistics/stats without authentication"""
        response = client.get("/api/statistics/stats?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_messages"] == 0
        assert data["total_sessions"] == 0
    
    @patch('app.routers.statistics.get_user_statistics')
    def test_get_statistics_error_handling(self, mock_get_stats, client, auth_headers):
        """Test error handling in get_statistics"""
        mock_get_stats.side_effect = Exception("Database error")
        
        response = client.get(
            "/api/statistics/stats?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 500
    
    @patch('app.routers.statistics.get_usage_trends')
    def test_get_trends_with_user(self, mock_get_trends, client, auth_headers):
        """Test GET /api/statistics/stats/trends with authenticated user"""
        mock_get_trends.return_value = {
            "daily_activity": [],
            "module_trends": {}
        }
        
        response = client.get(
            "/api/statistics/stats/trends?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "daily_activity" in data
        assert "module_trends" in data
    
    def test_get_trends_without_user(self, client):
        """Test GET /api/statistics/stats/trends without authentication"""
        response = client.get("/api/statistics/stats/trends?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert "daily_activity" in data
        assert "module_trends" in data
    
    @patch('app.routers.statistics.get_performance_metrics')
    def test_get_performance_with_user(self, mock_get_metrics, client, auth_headers):
        """Test GET /api/statistics/stats/performance with authenticated user"""
        mock_get_metrics.return_value = {
            "most_used_module": "qa",
            "most_used_module_count": 10,
            "average_messages_per_session": 5.5,
            "active_sessions": 3
        }
        
        response = client.get(
            "/api/statistics/stats/performance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "most_used_module" in data
        assert "average_messages_per_session" in data
    
    def test_get_performance_without_user(self, client):
        """Test GET /api/statistics/stats/performance without authentication"""
        response = client.get("/api/statistics/stats/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["most_used_module"] is None
        assert data["most_used_module_count"] == 0

