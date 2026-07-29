from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from aiogram.fsm.storage.base import StateType, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage


class IdleEvictingMemoryStorage(MemoryStorage):
    """MemoryStorage that doesn't grow forever.

    Vanilla MemoryStorage keeps ``self.storage`` as a ``defaultdict``, so a
    single read (``get_state``/``get_value``, which aiogram's dispatcher calls
    on every incoming update to resolve state-based filters) permanently
    creates a record for that user — even one who never entered a flow. On
    top of that, a user who starts a multi-step flow (e.g. adding an event)
    and never finishes it keeps their in-progress data in memory forever.

    This subclass (a) never creates a record on a pure read, and (b) evicts
    records that haven't been written to in ``max_age_seconds``, so memory use
    stays bounded by *currently active* users/flows rather than by every user
    who ever sent a message over the bot's lifetime.
    """

    def __init__(self, *, max_age_seconds: float, sweep_every: int = 200) -> None:
        super().__init__()
        self._max_age_seconds = max_age_seconds
        self._sweep_every = sweep_every
        self._touched: dict[StorageKey, float] = {}
        self._writes_since_sweep = 0

    def _touch(self, key: StorageKey) -> None:
        self._touched[key] = time.monotonic()
        self._writes_since_sweep += 1
        if self._writes_since_sweep >= self._sweep_every:
            self._writes_since_sweep = 0
            self._evict_stale()

    def _evict_stale(self) -> None:
        cutoff = time.monotonic() - self._max_age_seconds
        stale_keys = [key for key, last_write in self._touched.items() if last_write < cutoff]
        for key in stale_keys:
            del self._touched[key]
            self.storage.pop(key, None)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        self._touch(key)
        await super().set_state(key, state)

    async def get_state(self, key: StorageKey) -> str | None:
        record = self.storage.get(key)
        return record.state if record is not None else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        self._touch(key)
        await super().set_data(key, data)

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        record = self.storage.get(key)
        return record.data.copy() if record is not None else {}


__all__ = ["IdleEvictingMemoryStorage"]
