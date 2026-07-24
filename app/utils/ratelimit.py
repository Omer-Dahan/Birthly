from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    """Token-bucket rate limiter for async code.

    Refills continuously at ``rate`` tokens/second up to ``capacity``.
    ``acquire()`` waits until a token is available before returning.
    """

    def __init__(self, rate: float, capacity: int | None = None) -> None:
        self._rate = rate
        self._capacity = capacity if capacity is not None else max(1, int(rate))
        self._tokens = float(self._capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Block until a token is available, then consume it."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                deficit = 1 - self._tokens
                wait_time = deficit / self._rate
            await asyncio.sleep(wait_time)


class PerUserTokenBucket:
    """Per-key token bucket for chat-level rate limiting (e.g. per Telegram user_id).

    Buckets are created lazily and never explicitly expired; at bot scale
    (SPEC.md targets ~5,000 users) this is a bounded, small amount of state.
    """

    def __init__(self, rate_per_minute: int) -> None:
        self._rate_per_minute = rate_per_minute
        self._buckets: dict[int, tuple[float, float]] = {}

    def allow(self, key: int) -> bool:
        """True if the action for ``key`` is allowed right now (and consumes a token)."""
        now = time.monotonic()
        tokens, last_refill = self._buckets.get(key, (float(self._rate_per_minute), now))

        elapsed = now - last_refill
        refill_rate = self._rate_per_minute / 60.0
        tokens = min(self._rate_per_minute, tokens + elapsed * refill_rate)

        if tokens >= 1:
            tokens -= 1
            self._buckets[key] = (tokens, now)
            return True

        self._buckets[key] = (tokens, now)
        return False


__all__ = ["AsyncRateLimiter", "PerUserTokenBucket"]
