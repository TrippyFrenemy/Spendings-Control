import functools
import json
import logging
from typing import Optional, Callable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

logger = logging.getLogger(__name__)

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)


def redis_cache(
        expire: int = 3600,
        prefix: str = "cache",
        key_builder: Optional[Callable[..., str]] = None
):
    """
    Redis cache decorator that handles getting and setting cached values.

    Args:
        expire (int): Cache expiration time in seconds (default: 1 hour)
        prefix (str): Prefix for the cache key (default: "cache")
        key_builder (Callable): Custom function to build cache key (optional)
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip first argument if it's an AsyncSession
            cache_args = args[1:] if args and isinstance(args[0], AsyncSession) else args

            # Build cache key
            if key_builder:
                cache_key = key_builder(*cache_args, **kwargs)
            else:
                # Default key building: combine prefix, function name and arguments
                key_parts = [prefix, func.__name__]

                # Add positional args to key
                if cache_args:
                    key_parts.extend(str(arg) for arg in cache_args)

                # Add keyword args to key
                if kwargs:
                    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

                cache_key = ":".join(key_parts)

            try:
                # Try to get cached value
                cached_value = await redis.get(cache_key)

                if cached_value:
                    return json.loads(cached_value)

                # If no cached value, execute function
                result = await func(*args, **kwargs)

                # Cache the result
                if result is not None:
                    await redis.set(
                        cache_key,
                        json.dumps(result),
                        ex=expire
                    )

                return result

            except Exception as e:
                logger.error(f"Redis cache error for key {cache_key}: {str(e)}")
                # If caching fails, just execute the function
                return await func(*args, **kwargs)

        # Add helper method to invalidate cache
        async def invalidate_cache(*args, **kwargs):
            cache_args = args[1:] if args and isinstance(args[0], AsyncSession) else args
            if key_builder:
                cache_key = key_builder(*cache_args, **kwargs)
            else:
                key_parts = [prefix, func.__name__]
                if cache_args:
                    key_parts.extend(str(arg) for arg in cache_args)
                if kwargs:
                    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            await redis.delete(cache_key)

        wrapper.invalidate_cache = invalidate_cache
        return wrapper
    return decorator
