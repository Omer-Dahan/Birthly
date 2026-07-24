from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.handlers import register_all_routers
from app.i18n.translator import load_locales
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.i18n import I18nMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.user import UserMiddleware
from app.utils.logger import setup_logging

logger = logging.getLogger(__name__)


def _register_middlewares(dp: Dispatcher) -> None:
    """Order is load-bearing: see SPEC.md chapter 5."""
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserMiddleware())
    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.update.outer_middleware(I18nMiddleware())


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

    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("bot_starting")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("bot_stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
