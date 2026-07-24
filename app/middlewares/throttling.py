from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import settings
from app.i18n.translator import t
from app.utils.ratelimit import PerUserTokenBucket

_SILENCE_SECONDS = 30


class ThrottlingMiddleware(BaseMiddleware):
    """Per-user rate limiting: separate buckets for messages and callbacks.

    On the first violation, replies once with a rate-limit message, then
    silently drops further updates from that user for 30 seconds.
    """

    def __init__(self) -> None:
        self._message_bucket = PerUserTokenBucket(settings.rate_limit_messages)
        self._callback_bucket = PerUserTokenBucket(settings.rate_limit_callbacks)
        self._silenced_until: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user = data.get("event_from_user")
        if telegram_user is None or not isinstance(event, Message | CallbackQuery):
            return await handler(event, data)

        user_id = telegram_user.id
        bucket = self._message_bucket if isinstance(event, Message) else self._callback_bucket

        now = time.monotonic()
        silenced_until = self._silenced_until.get(user_id)
        if silenced_until is not None:
            if now < silenced_until:
                return None
            del self._silenced_until[user_id]

        if not bucket.allow(user_id):
            self._silenced_until[user_id] = now + _SILENCE_SECONDS
            user = data.get("user")
            language = user.language if user is not None else settings.default_language
            await event.answer(t("error.rate_limit", language))
            return None

        return await handler(event, data)
