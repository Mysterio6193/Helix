"""Simple in-memory rate limiter for API key usage.

Uses a sliding window counter approach. Not distributed — intended as a
first-pass guard. Replace with Redis-based limiting at scale.
"""
from __future__ import annotations

import time
from collections import defaultdict
from functools import lru_cache


class MemorySlidingWindowCounter:
    """Per-key sliding window counter with configurable RPM.

    Each entry tracks (window_start, count). Windows are 60s wide.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._window_s: float = 60.0

    def check(self, key: str, max_requests: int = 60) -> bool:
        """Return True if the request is allowed (under limit)."""
        now = time.monotonic()
        cutoff = now - self._window_s

        # Prune expired buckets
        buckets = self._buckets[key]
        buckets[:] = [(t, c) for t, c in buckets if t > cutoff]

        total = sum(c for _, c in buckets)
        if total >= max_requests:
            return False

        # Record this request
        if buckets and buckets[-1][0] > now - 1:
            buckets[-1] = (buckets[-1][0], buckets[-1][1] + 1)
        else:
            buckets.append((now, 1))
        return True


@lru_cache
def get_rate_limiter() -> MemorySlidingWindowCounter:
    return MemorySlidingWindowCounter()


# Default rate limits per tier (requests per minute)
RATE_LIMITS = {
    "free": 20,
    "starter": 60,
    "pro": 300,
    "business": 1000,
}


def get_rate_limit_for_plan(plan: str) -> int:
    return RATE_LIMITS.get(plan, 20)
