from __future__ import annotations

from aiogram import Dispatcher

from app.handlers import (
    admin,
    backup,
    errors,
    event_add,
    event_card,
    event_edit,
    event_list,
    fallback,
    menu,
    reminders,
    search,
    settings,
    start,
    stats,
    templates,
)


def register_all_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(event_add.router)
    dp.include_router(event_edit.router)
    dp.include_router(event_card.router)
    dp.include_router(event_list.router)
    dp.include_router(reminders.router)
    dp.include_router(search.router)
    dp.include_router(stats.router)
    dp.include_router(settings.router)
    dp.include_router(templates.router)
    dp.include_router(backup.router)
    dp.include_router(admin.router)
    dp.include_router(menu.router)
    dp.include_router(errors.router)
    # Fallback must be last to catch anything unhandled above.
    dp.include_router(fallback.router)
