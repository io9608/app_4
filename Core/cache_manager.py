import redis
import json
import hashlib
import time
from functools import wraps
from typing import Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced caching system with Redis backend"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError:
            logger.warning("Redis not available, using in-memory cache")
            self.redis_client = None
            self.memory_cache = {}
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            except Exception as e:
                logger.error(f"Cache get error: {e}")
                return None
        else:
            return self.memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.redis_client:
                return self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                self.memory_cache[key] = {'value': value, 'expires': time.time() + ttl}
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if self.redis_client:
            return bool(self.redis_client.delete(key))
        else:
            self.memory_cache.pop(key, None)
            return True
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        if self.redis_client:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        return 0
    
    def cache_decorator(self, ttl: int = 3600):
        """Decorator for caching function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self._generate_key(func.__name__, *args, *sorted(kwargs.items()))
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                logger.debug(f"Cache miss for {cache_key}, storing result")
                return result
            return wrapper
        return decorator
    
    def invalidate_related(self, model_name: str):
        """Invalidate cache for related models"""
        pattern = f"*{model_name}*"
        cleared = self.clear_pattern(pattern)
        logger.info(f"Cleared {cleared} cache entries for {model_name}")

# Global cache instance
cache_manager = CacheManager()
