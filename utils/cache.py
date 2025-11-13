"""
Caching Module
LRU and time-based caching for performance optimization
"""

import hashlib
import json
import logging
import pickle
import time
from collections import OrderedDict
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
import threading

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) Cache

    Stores a limited number of items and evicts the least recently used
    when the cache is full.
    """

    def __init__(self, maxsize: int = 1000):
        """
        Initialize LRU cache

        Args:
            maxsize: Maximum number of items to store
        """
        self.maxsize = maxsize
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None

    def put(self, key: str, value: Any) -> None:
        """
        Put item into cache

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache.move_to_end(key)
            else:
                # Add new key
                if len(self.cache) >= self.maxsize:
                    # Remove least recently used
                    self.cache.popitem(last=False)

            self.cache[key] = value

    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0

            return {
                'size': len(self.cache),
                'maxsize': self.maxsize,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.2f}%"
            }

    def __len__(self) -> int:
        """Get current cache size"""
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        """Check if key is in cache"""
        return key in self.cache


class TTLCache:
    """
    Time-To-Live Cache

    Items expire after a specified time period.
    """

    def __init__(self, ttl_seconds: int = 300, maxsize: int = 1000):
        """
        Initialize TTL cache

        Args:
            ttl_seconds: Time-to-live in seconds
            maxsize: Maximum number of items to store
        """
        self.ttl_seconds = ttl_seconds
        self.maxsize = maxsize
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache if not expired

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                # Check if expired
                if time.time() - timestamp < self.ttl_seconds:
                    self.hits += 1
                    return value
                else:
                    # Remove expired item
                    del self.cache[key]
                    self.evictions += 1

            self.misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        """
        Put item into cache with current timestamp

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            # Clean up expired entries if cache is full
            if len(self.cache) >= self.maxsize:
                self._evict_expired()

                # If still full, remove oldest
                if len(self.cache) >= self.maxsize:
                    oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
                    del self.cache[oldest_key]
                    self.evictions += 1

            self.cache[key] = (value, time.time())

    def _evict_expired(self) -> None:
        """Remove all expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]
            self.evictions += 1

    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            # Clean expired entries for accurate count
            self._evict_expired()

            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0

            return {
                'size': len(self.cache),
                'maxsize': self.maxsize,
                'ttl_seconds': self.ttl_seconds,
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate': f"{hit_rate:.2f}%"
            }


class DiskCache:
    """
    Persistent disk-based cache

    Stores cache entries on disk for persistence across sessions.
    """

    def __init__(self, cache_dir: str = ".cache", max_age_days: int = 7):
        """
        Initialize disk cache

        Args:
            cache_dir: Directory to store cache files
            max_age_days: Maximum age of cache entries in days
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_seconds = max_age_days * 24 * 3600
        self.hits = 0
        self.misses = 0

        logger.info(f"Disk cache initialized at: {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key"""
        # Hash the key to create filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from disk cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            self.misses += 1
            return None

        try:
            # Check age
            age = time.time() - cache_path.stat().st_mtime
            if age > self.max_age_seconds:
                # Remove expired cache
                cache_path.unlink()
                self.misses += 1
                return None

            # Load from disk
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)

            self.hits += 1
            return value

        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            self.misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        """
        Put item into disk cache

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)

        except Exception as e:
            logger.error(f"Error writing cache: {e}")

    def clear(self) -> None:
        """Clear all cache entries"""
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error deleting cache file {cache_file}: {e}")

        self.hits = 0
        self.misses = 0

    def clean_expired(self) -> int:
        """
        Remove expired cache entries

        Returns:
            Number of entries removed
        """
        removed = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                age = current_time - cache_file.stat().st_mtime
                if age > self.max_age_seconds:
                    cache_file.unlink()
                    removed += 1
            except Exception as e:
                logger.warning(f"Error cleaning cache file {cache_file}: {e}")

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)

        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            'entries': len(cache_files),
            'size_bytes': total_size,
            'size_mb': f"{total_size / (1024*1024):.2f}",
            'cache_dir': str(self.cache_dir),
            'max_age_days': self.max_age_seconds / (24 * 3600),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%"
        }


# Decorator for function caching
def cached(cache: Optional[LRUCache] = None, key_func: Optional[Callable] = None):
    """
    Decorator to cache function results

    Args:
        cache: Cache instance to use (default: create new LRUCache)
        key_func: Function to generate cache key from arguments

    Example:
        >>> feature_cache = LRUCache(maxsize=1000)
        >>> @cached(cache=feature_cache)
        ... def extract_features(packet_data):
        ...     # Expensive computation
        ...     return features
    """
    if cache is None:
        cache = LRUCache()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Compute and cache result
            result = func(*args, **kwargs)
            cache.put(cache_key, result)
            return result

        wrapper.cache = cache  # Expose cache for inspection
        return wrapper

    return decorator
