from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

from app.config import settings
from app.utils.ratelimit import Debouncer


class CallbackDebounceMiddleware(BaseMiddleware):
    """Blocks a second button tap from the same user within a short window.

    Nearly every write action in this bot (edit, settings, reminders,
    templates, backup import) is triggered by a callback button, so a short
    per-user debounce here doubles as anti-double-submit protection for all
    of them without touching each handler individually. Silently swallowed —
    the tap is acknowledged (so Telegram's client-side spinner clears) but the
    handler never runs.
    """

    def __init__(self) -> None:
        self._debouncer = Debouncer(settings.callback_debounce_ms / 1000)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        if not self._debouncer.allow(event.from_user.id):
            await event.answer()
            return None

        return await handler(event, data)
