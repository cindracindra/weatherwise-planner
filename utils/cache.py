"""
Time-based cache decorator for API responses.

This module provides a simple timed cache to reduce redundant API calls
and improve performance on slow hosting platforms. Cached results expire
after a specified time period (TTL - Time To Live).
"""

from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Callable

# Global cache storage: {cache_key: (result, expiry_time)}
# Example: {"get_current_weather_()_{}" : (WeatherReading(...), datetime(...))}
_cache: Dict[str, Tuple[Any, datetime]] = {}


def timed_cache(seconds: int) -> Callable:
    """
    Cache decorator that stores function results for a specified time period.

    This decorator wraps a function and caches its return value for `seconds`.
    Subsequent calls within the cache period return the cached result instantly
    without re-executing the function (no API calls).

    Args:
        seconds: Time-to-live (TTL) in seconds. How long to cache results.
                 Examples: 600 = 10 minutes, 3600 = 1 hour

    Returns:
        Decorator function that wraps the target function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create a unique cache key
            # Combines function name with its arguments
            cache_key = f"{func.__name__}_{args}_{kwargs}"

            # Check if we have a cached result
            now = datetime.now()
            if cache_key in _cache:
                # Found cached result - check if it's still fresh
                cached_result, expiry_time = _cache[cache_key]

                if now < expiry_time:
                    # Cache is still fresh. Return immediately
                    return cached_result

            # No cached result OR cache expired
            # Call the actual function (makes API request)
            result = func(*args, **kwargs)

            # Store result in cache with expiry time
            expiry_time = now + timedelta(seconds=seconds)
            _cache[cache_key] = (result, expiry_time)

            # Return the fresh result
            return result

        return wrapper
    return decorator


def clear_cache() -> None:
    """
    Clear all cached data.

    Useful for testing or when you need to force fresh data.
    """
    _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring/debugging.

    Returns:
        Dictionary with cache size and keys.
    """
    return {
        'size': len(_cache),
        'keys': list(_cache.keys())
    }
