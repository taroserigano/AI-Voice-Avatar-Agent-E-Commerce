"""Fixed-window counters for sign-in attempts.

Counters live in Redis because they are expendable: losing them only resets a window. If
Redis is unreachable we fall back to a per-process counter rather than letting sign-in
attempts through unlimited.
"""

from __future__ import annotations

import contextlib
import logging
import threading
import time
from functools import lru_cache

import redis

from commerce.config import get_settings

log = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, client: redis.Redis[bytes] | None) -> None:
        self._client = client
        self._local: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, window_seconds: int) -> int:
        """Count one event for ``key`` and return the count in the current window."""
        if self._client is not None:
            try:
                pipe = self._client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window_seconds, nx=True)
                count, _ = pipe.execute()
                return int(count)
            except redis.RedisError:
                log.warning("rate limiter: redis unavailable, using in-process counter")
        return self._hit_local(key, window_seconds)

    def peek(self, key: str) -> int:
        if self._client is not None:
            try:
                value = self._client.get(key)
                return int(value) if value else 0
            except redis.RedisError:
                pass
        with self._lock:
            count, expires = self._local.get(key, (0, 0.0))
            return count if expires > time.monotonic() else 0

    def reset(self, key: str) -> None:
        if self._client is not None:
            with contextlib.suppress(redis.RedisError):
                self._client.delete(key)
        with self._lock:
            self._local.pop(key, None)

    def _hit_local(self, key: str, window_seconds: int) -> int:
        now = time.monotonic()
        with self._lock:
            count, expires = self._local.get(key, (0, 0.0))
            if expires <= now:
                count, expires = 0, now + window_seconds
            count += 1
            self._local[key] = (count, expires)
            return count


@lru_cache
def get_rate_limiter() -> RateLimiter:
    url = get_settings().redis_url
    client = redis.Redis.from_url(url, socket_timeout=0.25, socket_connect_timeout=0.25)
    return RateLimiter(client)
