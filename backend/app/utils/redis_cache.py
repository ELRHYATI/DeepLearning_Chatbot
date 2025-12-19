"""
Service de cache Redis pour les réponses fréquentes
"""
import json
import hashlib
from typing import Optional, Any, Dict
import os
from app.utils.logger import get_logger

logger = get_logger()

# Tentative d'import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisCache:
    """Service de cache Redis avec fallback en mémoire"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}  # Fallback cache en mémoire
        self.use_redis = False
        
        if REDIS_AVAILABLE:
            try:
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", 6379))
                redis_db = int(os.getenv("REDIS_DB", 0))
                redis_password = os.getenv("REDIS_PASSWORD", None)
                
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                
                # Test de connexion
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis not available, using memory cache: {e}")
                self.use_redis = False
        else:
            logger.warning("Redis library not installed, using memory cache")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Génère une clé de cache unique
        
        Args:
            prefix: Préfixe de la clé (ex: "qa", "grammar", "reformulation")
            *args: Arguments positionnels
            **kwargs: Arguments nommés
        
        Returns:
            Clé de cache hashée
        """
        key_parts = [prefix]
        
        # Ajouter les arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, dict):
                key_parts.append(json.dumps(arg, sort_keys=True))
        
        # Ajouter les kwargs
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(json.dumps(sorted_kwargs, sort_keys=True))
        
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache
        
        Args:
            key: Clé de cache
        
        Returns:
            Valeur en cache ou None
        """
        try:
            if self.use_redis and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Fallback en mémoire
                if key in self.memory_cache:
                    return self.memory_cache[key]
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Stocke une valeur dans le cache
        
        Args:
            key: Clé de cache
            value: Valeur à stocker
            ttl: Time to live en secondes (défaut: 1 heure)
        
        Returns:
            True si succès, False sinon
        """
        try:
            value_json = json.dumps(value, ensure_ascii=False)
            
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, ttl, value_json)
                return True
            else:
                # Fallback en mémoire (limité à 1000 entrées)
                if len(self.memory_cache) >= 1000:
                    # Supprimer la première entrée (FIFO)
                    first_key = next(iter(self.memory_cache))
                    del self.memory_cache[first_key]
                
                self.memory_cache[key] = value
                return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Supprime une clé du cache
        
        Args:
            key: Clé de cache
        
        Returns:
            True si succès, False sinon
        """
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Supprime toutes les clés correspondant à un pattern
        
        Args:
            pattern: Pattern de clés (ex: "qa:*")
        
        Returns:
            Nombre de clés supprimées
        """
        try:
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # Fallback en mémoire
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(pattern.replace("*", ""))]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                return len(keys_to_delete)
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache
        
        Returns:
            Statistiques du cache
        """
        try:
            if self.use_redis and self.redis_client:
                info = self.redis_client.info("memory")
                return {
                    "type": "redis",
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "keys": self.redis_client.dbsize()
                }
            else:
                return {
                    "type": "memory",
                    "keys": len(self.memory_cache),
                    "max_keys": 1000
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"type": "unknown", "error": str(e)}


# Instance globale du cache
cache = RedisCache()


def cache_result(prefix: str, ttl: int = 3600):
    """
    Décorateur pour mettre en cache le résultat d'une fonction
    
    Args:
        prefix: Préfixe pour les clés de cache
        ttl: Time to live en secondes
    
    Returns:
        Décorateur
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Générer la clé de cache
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Vérifier le cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {prefix}: {key[:20]}...")
                return cached_result
            
            # Exécuter la fonction
            result = await func(*args, **kwargs)
            
            # Mettre en cache
            cache.set(key, result, ttl)
            logger.debug(f"Cached result for {prefix}: {key[:20]}...")
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            # Générer la clé de cache
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Vérifier le cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {prefix}: {key[:20]}...")
                return cached_result
            
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            # Mettre en cache
            cache.set(key, result, ttl)
            logger.debug(f"Cached result for {prefix}: {key[:20]}...")
            
            return result
        
        # Retourner le wrapper approprié selon si la fonction est async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

