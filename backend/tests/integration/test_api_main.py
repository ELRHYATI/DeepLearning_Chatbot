"""
Integration tests for Main API endpoints
"""
import pytest
from unittest.mock import patch
from fastapi import status


@pytest.mark.integration
class TestMainAPI:
    """Test suite for Main API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test GET / root endpoint"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "status" in data
    
    def test_health_check(self, client):
        """Test GET /api/health"""
        response = client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    @patch('app.utils.health_check.get_comprehensive_health')
    def test_detailed_health_check(self, mock_health, client):
        """Test GET /api/health/detailed"""
        mock_health.return_value = {
            "database": {"status": "healthy"},
            "redis": {"status": "healthy"},
            "overall_status": "healthy"
        }
        
        response = client.get("/api/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "database" in data
    
    @patch('app.utils.health_check.check_database')
    @patch('app.utils.health_check.check_models')
    def test_readiness_check_ready(self, mock_models, mock_db, client):
        """Test GET /api/health/ready when ready"""
        mock_db.return_value = {"status": "healthy"}
        mock_models.return_value = {"status": "healthy"}
        
        response = client.get("/api/health/ready")
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_liveness_check(self, client):
        """Test GET /api/health/live"""
        response = client.get("/api/health/live")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"

