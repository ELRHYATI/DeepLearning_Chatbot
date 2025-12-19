"""
Unit tests for Health Check utilities
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.health_check import (
    check_database,
    check_redis,
    check_celery,
    check_disk_space,
    check_memory,
    check_models,
    get_comprehensive_health
)


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for Health Check utilities"""
    
    @patch('app.utils.health_check.SessionLocal')
    def test_check_database_healthy(self, mock_session_local):
        """Test database health check when healthy"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock query results
        mock_db.execute.return_value = None
        mock_db.query.return_value.count.return_value = 10
        
        result = check_database()
        
        assert result["status"] == "healthy"
        assert result["connected"] == True
        assert "stats" in result
    
    @patch('app.utils.health_check.SessionLocal')
    def test_check_database_unhealthy(self, mock_session_local):
        """Test database health check when unhealthy"""
        mock_session_local.side_effect = Exception("Connection failed")
        
        result = check_database()
        
        assert result["status"] == "unhealthy"
        assert result["connected"] == False
        assert "error" in result
    
    @patch('app.utils.health_check.cache')
    def test_check_redis_healthy(self, mock_cache):
        """Test Redis health check when healthy"""
        mock_cache.use_redis = True
        mock_cache.get_stats.return_value = {"hits": 100, "misses": 50}
        
        result = check_redis()
        
        assert result["status"] == "healthy"
        assert result["connected"] == True
    
    @patch('app.utils.health_check.cache')
    def test_check_redis_degraded(self, mock_cache):
        """Test Redis health check when using fallback"""
        mock_cache.use_redis = False
        mock_cache.get_stats.return_value = {}
        
        result = check_redis()
        
        assert result["status"] == "degraded"
        assert result["connected"] == False
        assert "fallback" in result
    
    @patch('app.utils.health_check.celery_app')
    def test_check_celery_healthy(self, mock_celery):
        """Test Celery health check when healthy"""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {"worker1": [], "worker2": []}
        mock_celery.control.inspect.return_value = mock_inspect
        
        result = check_celery()
        
        assert result["status"] == "healthy"
        assert result["connected"] == True
        assert result["active_workers"] == 2
    
    @patch('app.utils.health_check.celery_app')
    def test_check_celery_no_workers(self, mock_celery):
        """Test Celery health check when no workers"""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = None
        mock_celery.control.inspect.return_value = mock_inspect
        
        result = check_celery()
        
        assert result["status"] == "degraded"
        assert result["active_workers"] == 0
    
    @patch('app.utils.health_check.psutil')
    def test_check_disk_space_healthy(self, mock_psutil):
        """Test disk space check when healthy"""
        mock_disk = MagicMock()
        mock_disk.free = 50 * (1024 ** 3)  # 50 GB free
        mock_disk.total = 100 * (1024 ** 3)  # 100 GB total
        mock_disk.used = 50 * (1024 ** 3)  # 50 GB used
        mock_psutil.disk_usage.return_value = mock_disk
        
        result = check_disk_space()
        
        assert result["status"] == "healthy"
        assert "free_gb" in result
        assert "used_percent" in result
    
    @patch('app.utils.health_check.psutil')
    def test_check_disk_space_critical(self, mock_psutil):
        """Test disk space check when critical"""
        mock_disk = MagicMock()
        mock_disk.free = 5 * (1024 ** 3)  # 5 GB free
        mock_disk.total = 100 * (1024 ** 3)  # 100 GB total
        mock_disk.used = 95 * (1024 ** 3)  # 95 GB used
        mock_psutil.disk_usage.return_value = mock_disk
        
        result = check_disk_space()
        
        assert result["status"] == "critical"
    
    @patch('app.utils.health_check.psutil')
    def test_check_memory_healthy(self, mock_psutil):
        """Test memory check when healthy"""
        mock_memory = MagicMock()
        mock_memory.percent = 50.0
        mock_memory.available = 8 * (1024 ** 3)  # 8 GB available
        mock_memory.total = 16 * (1024 ** 3)  # 16 GB total
        mock_psutil.virtual_memory.return_value = mock_memory
        
        result = check_memory()
        
        assert result["status"] == "healthy"
        assert "used_percent" in result
        assert "available_gb" in result
    
    @patch('app.utils.health_check.psutil')
    def test_check_memory_critical(self, mock_psutil):
        """Test memory check when critical"""
        mock_memory = MagicMock()
        mock_memory.percent = 95.0
        mock_memory.available = 0.5 * (1024 ** 3)  # 0.5 GB available
        mock_memory.total = 16 * (1024 ** 3)  # 16 GB total
        mock_psutil.virtual_memory.return_value = mock_memory
        
        result = check_memory()
        
        assert result["status"] == "critical"
    
    @patch('app.services.grammar_service.GrammarService')
    @patch('app.services.qa_service.QAService')
    @patch('app.services.reformulation_service.ReformulationService')
    def test_check_models_healthy(
        self, mock_reformulation, mock_qa, mock_grammar
    ):
        """Test models check when all models are ready"""
        from app.utils.health_check import check_models
        
        mock_grammar_service = MagicMock()
        mock_grammar_service.tool = MagicMock()
        mock_grammar.return_value = mock_grammar_service
        
        mock_qa_service = MagicMock()
        mock_qa_service.qa_pipeline = MagicMock()
        mock_qa.return_value = mock_qa_service
        
        mock_reformulation_service = MagicMock()
        mock_reformulation_service.reformulation_pipeline = MagicMock()
        mock_reformulation.return_value = mock_reformulation_service
        
        result = check_models()
        
        assert result["status"] in ["healthy", "degraded"]
        assert "models" in result
        assert "grammar" in result["models"]
        assert "qa" in result["models"]
        assert "reformulation" in result["models"]
    
    @patch('app.utils.health_check.check_database')
    @patch('app.utils.health_check.check_redis')
    @patch('app.utils.health_check.check_celery')
    @patch('app.utils.health_check.check_disk_space')
    @patch('app.utils.health_check.check_memory')
    @patch('app.utils.health_check.check_models')
    def test_get_comprehensive_health(
        self, mock_models, mock_memory, mock_disk,
        mock_celery, mock_redis, mock_db
    ):
        """Test comprehensive health check"""
        mock_db.return_value = {"status": "healthy"}
        mock_redis.return_value = {"status": "healthy"}
        mock_celery.return_value = {"status": "healthy"}
        mock_disk.return_value = {"status": "healthy"}
        mock_memory.return_value = {"status": "healthy"}
        mock_models.return_value = {"status": "healthy"}
        
        result = get_comprehensive_health()
        
        assert "timestamp" in result
        assert "database" in result
        assert "redis" in result
        assert "celery" in result
        assert "overall_status" in result
        assert result["overall_status"] == "healthy"
    
    @patch('app.utils.health_check.psutil', None)
    def test_check_disk_space_no_psutil(self):
        """Test disk space check when psutil is not available"""
        result = check_disk_space()
        
        assert result["status"] == "unknown"
        assert "error" in result
    
    @patch('app.utils.health_check.psutil', None)
    def test_check_memory_no_psutil(self):
        """Test memory check when psutil is not available"""
        result = check_memory()
        
        assert result["status"] == "unknown"
        assert "error" in result

