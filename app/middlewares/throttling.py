from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import settings
from app.i18n.translator import t
from app.utils.ratelimit import PerUserTokenBucket

_SILENCE_SECONDS = 30


def _account_age_seconds(created_at: datetime | None) -> float:
    """Seconds since account creation. Treats a missing/unreadable value as brand new."""
    if created_at is None:
        return 0.0
    # SQLite has no native tz-aware DateTime, so a value round-tripped through
    # the DB comes back naive even though it was written as UTC — compare like
    # for like instead of letting a naive/aware subtraction raise.
    now = datetime.now(UTC) if created_at.tzinfo is not None else datetime.utcnow()
    return (now - created_at).total_seconds()


class ThrottlingMiddleware(BaseMiddleware):
    """Per-user rate limiting: separate buckets for messages and callbacks.

    Accounts still within their grace period (SPEC: fresh Telegram accounts
    are the ones most likely to be spam/scanning bots) get a stricter pair of
    buckets. On the first violation, replies once with a rate-limit message,
    then silently drops further updates from that user for 30 seconds.
    """

    def __init__(self) -> None:
        self._message_bucket = PerUserTokenBucket(settings.rate_limit_messages)
        self._callback_bucket = PerUserTokenBucket(settings.rate_limit_callbacks)
        self._new_account_message_bucket = PerUserTokenBucket(
            settings.new_account_rate_limit_messages
        )
        self._new_account_callback_bucket = PerUserTokenBucket(
            settings.new_account_rate_limit_callbacks
        )
        # Insertion order == expiry order here (values are `now + constant` and
        # `now` is monotonically non-decreasing), so a silenced user who never
        # writes again still gets purged by _purge_expired instead of sitting
        # in this dict forever.
        self._silenced_until: dict[int, float] = {}

    def _purge_expired(self, now: float) -> None:
        while self._silenced_until:
            user_id, expiry = next(iter(self._silenced_until.items()))
            if expiry > now:
                return
            del self._silenced_until[user_id]

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
        user = data.get("user")
        is_message = isinstance(event, Message)

        grace_seconds = settings.new_account_grace_hours * 3600
        if user is not None and _account_age_seconds(user.created_at) < grace_seconds:
            bucket = self._new_account_message_bucket if is_message else self._new_account_callback_bucket
        else:
            bucket = self._message_bucket if is_message else self._callback_bucket

        now = time.monotonic()
        self._purge_expired(now)
        silenced_until = self._silenced_until.get(user_id)
        if silenced_until is not None:
            if now < silenced_until:
                return None
            del self._silenced_until[user_id]

        if not bucket.allow(user_id):
            self._silenced_until[user_id] = now + _SILENCE_SECONDS
            language = user.language if user is not None else settings.default_language
            await event.answer(t("error.rate_limit", language))
            return None

        return await handler(event, data)
