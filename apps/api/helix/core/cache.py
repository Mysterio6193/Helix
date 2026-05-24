"""Multi-layer caching system: L1 (in-process LRU) + L2 (Redis) + L3 (disk).

Provides intelligent caching for:
- LLM responses (prompt hash → response)
- Embeddings (text hash → vector)
- API responses (URL + params → response)
- Database query results (query hash → rows)
- Tool outputs (tool name + args → result)

All caches respect TTL and support cache warming, invalidation, and metrics.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.core.redis import get_redis

log = get_logger("helix.cache")
settings = get_settings()

T = TypeVar("T")


class L1Cache:
    """In-process LRU cache with TTL."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            self._misses += 1
            return None
        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            self._misses += 1
            return None
        self._cache.move_to_end(key)
        self._hits += 1
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or self._default_ttl
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.time() + ttl)
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0,
            "size": len(self._cache),
            "max_size": self._max_size,
        }


class L2Cache:
    """Redis-backed cache with serialization."""

    def __init__(self, default_ttl: int = 600) -> None:
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def _key(self, namespace: str, key: str) -> str:
        return f"helix:cache:{namespace}:{key}"

    async def get(self, namespace: str, key: str) -> Any | None:
        try:
            redis = get_redis()
            data = await redis.get(self._key(namespace, key))
            if data is None:
                self._misses += 1
                return None
            self._hits += 1
            return pickle.loads(data)
        except Exception as exc:
            log.warning("l2_cache_get_error", error=str(exc))
            return None

    async def set(self, namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            redis = get_redis()
            ttl = ttl or self._default_ttl
            await redis.setex(self._key(namespace, key), ttl, pickle.dumps(value))
        except Exception as exc:
            log.warning("l2_cache_set_error", error=str(exc))

    async def delete(self, namespace: str, key: str) -> None:
        try:
            redis = get_redis()
            await redis.delete(self._key(namespace, key))
        except Exception:
            pass

    async def clear_namespace(self, namespace: str) -> None:
        try:
            redis = get_redis()
            pattern = f"helix:cache:{namespace}:*"
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as exc:
            log.warning("l2_cache_clear_error", error=str(exc))

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0,
        }


class SmartCache:
    """Multi-layer cache: L1 (memory) → L2 (Redis) → compute.

    Usage:
        cache = SmartCache()
        result = await cache.get_or_compute(
            "llm", prompt_hash,
            compute_fn=lambda: generate_text(prompt),
            ttl=300
        )
    """

    def __init__(self) -> None:
        self.l1 = L1Cache(
            max_size=getattr(settings, "cache_l1_size", 1000),
            default_ttl=getattr(settings, "cache_l1_ttl", 300),
        )
        self.l2 = L2Cache(default_ttl=getattr(settings, "cache_l2_ttl", 600))
        self._compute_times: list[float] = []

    def _hash_key(self, *args: Any) -> str:
        """Create a deterministic hash key from arguments."""
        data = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    async def get_or_compute(
        self,
        namespace: str,
        key: str,
        compute_fn: Callable[[], Any],
        ttl: int | None = None,
        use_l1: bool = True,
        use_l2: bool = True,
    ) -> Any:
        """Get from cache or compute and cache the result."""
        full_key = f"{namespace}:{key}"

        # L1 check
        if use_l1:
            value = self.l1.get(full_key)
            if value is not None:
                log.debug("cache_l1_hit", namespace=namespace, key=key)
                return value

        # L2 check
        if use_l2:
            value = await self.l2.get(namespace, key)
            if value is not None:
                log.debug("cache_l2_hit", namespace=namespace, key=key)
                # Backfill L1
                if use_l1:
                    self.l1.set(full_key, value, ttl)
                return value

        # Compute
        log.debug("cache_compute", namespace=namespace, key=key)
        start = time.time()
        value = await compute_fn() if callable(compute_fn) and hasattr(compute_fn, "__await__") else compute_fn()
        if hasattr(value, "__await__"):
            value = await value
        elapsed = time.time() - start
        self._compute_times.append(elapsed)

        # Store in caches
        if use_l1:
            self.l1.set(full_key, value, ttl)
        if use_l2:
            await self.l2.set(namespace, key, value, ttl)

        return value

    async def get(self, namespace: str, key: str) -> Any | None:
        """Get from cache without computing."""
        full_key = f"{namespace}:{key}"
        value = self.l1.get(full_key)
        if value is not None:
            return value
        value = await self.l2.get(namespace, key)
        if value is not None:
            self.l1.set(full_key, value)
            return value
        return None

    async def set(self, namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cache value."""
        full_key = f"{namespace}:{key}"
        self.l1.set(full_key, value, ttl)
        await self.l2.set(namespace, key, value, ttl)

    async def delete(self, namespace: str, key: str) -> None:
        """Delete from all cache layers."""
        full_key = f"{namespace}:{key}"
        self.l1.delete(full_key)
        await self.l2.delete(namespace, key)

    async def invalidate_namespace(self, namespace: str) -> None:
        """Clear all keys in a namespace."""
        # Clear L1 keys matching namespace
        keys_to_remove = [k for k in self.l1._cache if k.startswith(f"{namespace}:")]
        for k in keys_to_remove:
            self.l1.delete(k)
        await self.l2.clear_namespace(namespace)

    @property
    def stats(self) -> dict[str, Any]:
        avg_compute = sum(self._compute_times[-100:]) / len(self._compute_times[-100:]) if self._compute_times else 0
        return {
            "l1": self.l1.stats,
            "l2": self.l2.stats,
            "avg_compute_time_ms": round(avg_compute * 1000, 2),
            "total_computes": len(self._compute_times),
        }


# Global cache instance
_cache: SmartCache | None = None


def get_cache() -> SmartCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = SmartCache()
    return _cache


def cached(namespace: str, ttl: int = 300, key_fn: Callable | None = None):
    """Decorator to cache function results.

    Usage:
        @cached("llm", ttl=600)
        async def generate_text(prompt: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache()
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = cache._hash_key(func.__name__, args, kwargs)

            return await cache.get_or_compute(
                namespace, key,
                compute_fn=lambda: func(*args, **kwargs),
                ttl=ttl,
            )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, only use L1 cache
            cache = get_cache()
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = cache._hash_key(func.__name__, args, kwargs)

            value = cache.l1.get(f"{namespace}:{key}")
            if value is not None:
                return value

            value = func(*args, **kwargs)
            cache.l1.set(f"{namespace}:{key}", value, ttl)
            return value

        return async_wrapper if hasattr(func, "__await__") else sync_wrapper
    return decorator


async def warm_cache(namespace: str, items: dict[str, Any], ttl: int = 3600) -> None:
    """Pre-populate cache with known values."""
    cache = get_cache()
    for key, value in items.items():
        await cache.set(namespace, key, value, ttl)
    log.info("cache_warmed", namespace=namespace, count=len(items))
