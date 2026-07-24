from __future__ import annotations

from aiogram import Dispatcher

from app.handlers import menu, start


def register_all_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(menu.router)
