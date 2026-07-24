from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Binds ``update_id`` as a correlation id and logs handler entry/duration."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update: Update | None = data.get("event_update")
        correlation_id = update.update_id if update is not None else None

        structlog.contextvars.bind_contextvars(update_id=correlation_id)
        start = time.monotonic()
        try:
            logger.info("update_received", extra={"update_id": correlation_id})
            return await handler(event, data)
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "update_handled",
                extra={"update_id": correlation_id, "duration_ms": duration_ms},
            )
            structlog.contextvars.clear_contextvars()
