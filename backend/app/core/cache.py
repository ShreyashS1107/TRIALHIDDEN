import json
import logging
from typing import Optional, Any
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import redis
    if settings.REDIS_URL:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    else:
        redis_client = None
except ImportError:
    redis_client = None

def get_cache(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        val = redis_client.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        logger.warning(f"Redis get failed: {e}")
    return None

def set_cache(key: str, value: Any, ttl: int = 3600):
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Redis set failed: {e}")

def cached(prefix: str, ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not redis_client:
                return func(*args, **kwargs)
                
            # Build cache key only from safe serializable kwargs
            safe_kwargs = {}
            for k, v in kwargs.items():
                if isinstance(v, (str, int, float, bool, type(None))):
                    safe_kwargs[k] = v
                    
            key_parts = [f"{k}={v}" for k, v in sorted(safe_kwargs.items()) if v is not None]
            cache_key = f"{prefix}:" + "&".join(key_parts)
            
            cached_val = get_cache(cache_key)
            if cached_val is not None:
                return cached_val
                
            result = func(*args, **kwargs)
            
            if hasattr(result, "model_dump"):
                cache_data = result.model_dump(mode="json")
            elif hasattr(result, "dict"):
                cache_data = result.dict()
            else:
                cache_data = result
                
            set_cache(cache_key, cache_data, ttl)
            return result
        return wrapper
    return decorator
