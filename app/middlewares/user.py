from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.i18n.translator import t
from app.services.user_service import get_or_create_user


class UserMiddleware(BaseMiddleware):
    """Loads (or creates) the DB user for this update and short-circuits blocked users."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user: TelegramUser | None = data.get("event_from_user")
        if telegram_user is None:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        user = await get_or_create_user(
            session,
            user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            is_admin=telegram_user.id in settings.admin_ids,
        )
        data["user"] = user

        if user.is_blocked:
            answer = getattr(event, "answer", None)
            if answer is not None:
                await answer(t("error.blocked", user.language))
            return None

        return await handler(event, data)
