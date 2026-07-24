from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from app.callbacks.factories import MenuCallback, NavCallback
from app.core.formatting import format_countdown, format_name
from app.db.models import User
from app.i18n.translator import t
from app.keyboards.menu import home_keyboard
from app.services.home_service import get_home_summary
from app.utils.telegram import edit_or_ignore

router = Router(name="menu")


async def render_home(session: Any, user: User) -> tuple[str, InlineKeyboardMarkup]:
    summary = await get_home_summary(session, user)
    lang = user.language

    lines = [t("screen.home.title", lang), ""]

    if summary.nearest_event is None:
        lines.append(t("screen.home.empty", lang))
    else:
        lines.append(t("screen.home.today", lang, count=summary.today_count))
        lines.append(t("screen.home.week", lang, count=summary.week_count))
        nearest_name = format_name(
            summary.nearest_event.first_name, summary.nearest_event.last_name
        )
        countdown = format_countdown(summary.nearest_days_until or 0)
        lines.append(t("screen.home.nearest", lang, name=nearest_name, countdown=countdown))

    lines.append("")
    lines.append(t("screen.home.prompt", lang))

    text = "\n".join(lines)
    keyboard = home_keyboard(lang)
    return text, keyboard


@router.callback_query(MenuCallback.filter(F.action == "home"))
async def cb_menu_home(
    callback: CallbackQuery, session: Any, user: User
) -> None:
    text, keyboard = await render_home(session, user)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(NavCallback.filter(F.action == "home"))
async def cb_nav_home(callback: CallbackQuery, session: Any, user: User) -> None:
    text, keyboard = await render_home(session, user)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()
