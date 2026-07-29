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
        # Created lazily on first acquire(), not here: an asyncio.Lock binds
        # to whatever event loop is running when it's constructed, but this
        # limiter is a module-level singleton that must work across the
        # multiple event loops a long-lived process (or per-test loops in
        # pytest-asyncio) can create over its lifetime.
        self._lock: asyncio.Lock | None = None

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Block until a token is available, then consume it."""
        if self._lock is None:
            self._lock = asyncio.Lock()
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

    Buckets are created lazily. At bot scale (SPEC.md targets ~5,000 users)
    that alone is a bounded, small amount of state, but a burst of distinct
    user_ids (spam, scanning) could otherwise grow this dict without limit —
    so idle buckets (untouched for over an hour) are swept out periodically.
    """

    _IDLE_EVICT_SECONDS = 3600
    _SWEEP_EVERY = 500

    def __init__(self, rate_per_minute: int) -> None:
        self._rate_per_minute = rate_per_minute
        self._buckets: dict[int, tuple[float, float]] = {}
        self._calls_since_sweep = 0

    def _evict_idle(self, now: float) -> None:
        cutoff = now - self._IDLE_EVICT_SECONDS
        idle_keys = [key for key, (_, last_refill) in self._buckets.items() if last_refill < cutoff]
        for key in idle_keys:
            del self._buckets[key]

    def allow(self, key: int) -> bool:
        """True if the action for ``key`` is allowed right now (and consumes a token)."""
        now = time.monotonic()

        self._calls_since_sweep += 1
        if self._calls_since_sweep >= self._SWEEP_EVERY:
            self._calls_since_sweep = 0
            self._evict_idle(now)

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


class Debouncer:
    """Per-key minimum-interval gate — blocks a second call within ``interval_seconds``.

    Unlike a token bucket (which allows bursts up to its capacity), this never
    allows two calls closer together than ``interval_seconds``. That's exactly
    what's needed to stop accidental double-taps on save/confirm/toggle
    buttons, independent of the broader per-minute rate limits.
    """

    _IDLE_EVICT_SECONDS = 3600
    _SWEEP_EVERY = 500

    def __init__(self, interval_seconds: float) -> None:
        self._interval_seconds = interval_seconds
        self._last_call: dict[int, float] = {}
        self._calls_since_sweep = 0

    def _evict_idle(self, now: float) -> None:
        cutoff = now - self._IDLE_EVICT_SECONDS
        idle_keys = [key for key, last in self._last_call.items() if last < cutoff]
        for key in idle_keys:
            del self._last_call[key]

    def allow(self, key: int) -> bool:
        """True if the action for ``key`` is allowed right now (and records it)."""
        now = time.monotonic()

        self._calls_since_sweep += 1
        if self._calls_since_sweep >= self._SWEEP_EVERY:
            self._calls_since_sweep = 0
            self._evict_idle(now)

        last = self._last_call.get(key)
        if last is not None and now - last < self._interval_seconds:
            return False

        self._last_call[key] = now
        return True


__all__ = ["AsyncRateLimiter", "Debouncer", "PerUserTokenBucket"]
