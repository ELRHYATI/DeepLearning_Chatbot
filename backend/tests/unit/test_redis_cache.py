"""
Unit tests for Redis Cache utility
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.redis_cache import RedisCache, cache_result


@pytest.mark.unit
class TestRedisCache:
    """Test suite for Redis Cache"""
    
    @patch('app.utils.redis_cache.redis')
    def test_redis_cache_initialization_with_redis(self, mock_redis):
        """Test RedisCache initialization with Redis available"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.Redis.return_value = mock_client
        
        cache = RedisCache()
        
        assert cache is not None
        assert hasattr(cache, 'redis_client')
    
    @patch('app.utils.redis_cache.REDIS_AVAILABLE', False)
    def test_redis_cache_initialization_without_redis(self):
        """Test RedisCache initialization without Redis"""
        cache = RedisCache()
        
        assert cache is not None
        assert cache.use_redis is False
    
    def test_generate_key(self):
        """Test key generation"""
        cache = RedisCache()
        key = cache._generate_key("test", "arg1", "arg2", kwarg1="value1")
        
        assert isinstance(key, str)
        assert key.startswith("test:")
    
    def test_get_not_found(self):
        """Test getting non-existent key"""
        cache = RedisCache()
        result = cache.get("nonexistent_key")
        
        assert result is None
    
    def test_set_and_get(self):
        """Test setting and getting a value"""
        cache = RedisCache()
        cache.set("test_key", {"data": "value"}, ttl=3600)
        result = cache.get("test_key")
        
        assert result is not None
        assert result.get("data") == "value"
    
    def test_delete(self):
        """Test deleting a cached value"""
        cache = RedisCache()
        cache.set("test_key", {"data": "value"})
        cache.delete("test_key")
        result = cache.get("test_key")
        
        assert result is None
    
    def test_delete_multiple(self):
        """Test deleting multiple keys"""
        cache = RedisCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.delete("key1")
        cache.delete("key2")
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_result_decorator(self):
        """Test cache_result decorator"""
        cache = RedisCache()
        
        call_count = 0
        
        @cache_result("test", ttl=3600)
        def test_function():
            nonlocal call_count
            call_count += 1
            return {"result": "data"}
        
        # First call should execute function
        result1 = test_function()
        assert call_count == 1
        assert result1 == {"result": "data"}
        
        # Second call should use cache
        result2 = test_function()
        assert call_count == 1  # Should not increment
        assert result2 == {"result": "data"}

