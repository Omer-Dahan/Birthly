from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "app"

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.db.session import get_sessionmaker
from app.handlers import register_all_routers
from app.i18n.translator import load_locales
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.i18n import I18nMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.user import UserMiddleware
from app.scheduler.scheduler import build_scheduler
from app.utils.logger import setup_logging

logger = logging.getLogger(__name__)


def _register_middlewares(dp: Dispatcher) -> None:
    """Order is load-bearing: see SPEC.md chapter 5."""
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserMiddleware())
    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.update.outer_middleware(I18nMiddleware())


async def _sync_admins(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Sync is_admin flag from ADMIN_IDS env var to the users table (SPEC.md ch.17)."""
    if not settings.admin_ids:
        return
    async with session_factory() as session:
        from sqlalchemy import select

        from app.db.models import User

        result = await session.execute(
            select(User).where(User.id.in_(settings.admin_ids))
        )
        users = list(result.scalars().all())
        for user in users:
            user.is_admin = True
        await session.commit()
    logger.info("admins_synced", extra={"admin_ids": settings.admin_ids})


async def main() -> None:
    setup_logging()
    load_locales()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    _register_middlewares(dp)
    register_all_routers(dp)

    session_factory = get_sessionmaker()

    # Sync admin flags from config → DB on every startup
    await _sync_admins(session_factory)

    # Build and start the scheduler before polling begins
    scheduler = build_scheduler(bot, session_factory)
    scheduler.start()
    logger.info("scheduler_started")

    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("bot_starting")
    try:
        await dp.start_polling(bot)
    finally:
        # Graceful shutdown: wait for running jobs to complete
        scheduler.shutdown(wait=True)
        logger.info("scheduler_stopped")
        await bot.session.close()
        logger.info("bot_stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
