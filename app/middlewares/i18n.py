from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import partial
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import settings
from app.i18n.translator import t


class I18nMiddleware(BaseMiddleware):
    """Injects ``_`` into handler data: a translator bound to the current user's language."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        language = user.language if user is not None else settings.default_language
        data["_"] = partial(t, lang=language)
        return await handler(event, data)
