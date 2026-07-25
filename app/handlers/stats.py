from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import MenuCallback, NavCallback, StatsCallback
from app.constants import HEBREW_MONTH_NAMES
from app.core.formatting import format_countdown, format_name
from app.core.text import esc
from app.db.models import User
from app.i18n.translator import t
from app.services.event_card_service import category_label
from app.services.stats_service import UserStats, get_user_stats
from app.utils.telegram import edit_or_ignore

router = Router(name="stats")

_MONTH_NAMES_EN = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)  # fmt: skip

_BAR_MAX_LEN = 10


def _bar(count: int, max_count: int) -> str:
    if max_count <= 0:
        return ""
    filled = max(1, round(count / max_count * _BAR_MAX_LEN)) if count > 0 else 0
    return "▓" * filled


def _month_label(month: int, lang: str) -> str:
    if lang == "he":
        return HEBREW_MONTH_NAMES[month - 1] if month <= 12 else str(month)
    return _MONTH_NAMES_EN[month - 1]


def _render_home(stats: UserStats, user: User) -> str:
    lang = user.language
    if stats.total == 0:
        return f"{t('stats.title', lang)}\n\n{t('stats.empty', lang)}"

    lines = [t("stats.title", lang), ""]
    lines.append(t("stats.total", lang, count=stats.total))
    lines.append(t("stats.today", lang, count=stats.today))
    lines.append(t("stats.this_week", lang, count=stats.this_week))
    lines.append(t("stats.this_month", lang, count=stats.this_month))
    lines.append("")

    if stats.nearest is not None and stats.nearest_days_until is not None:
        name = esc(format_name(stats.nearest.first_name, stats.nearest.last_name))
        countdown = format_countdown(stats.nearest_days_until)
        lines.append(t("stats.nearest", lang, name=name, countdown=countdown))

    if stats.youngest is not None:
        event, age = stats.youngest
        name = esc(format_name(event.first_name, event.last_name))
        lines.append(t("stats.youngest", lang, name=name, age=age))

    if stats.oldest is not None:
        event, age = stats.oldest
        name = esc(format_name(event.first_name, event.last_name))
        lines.append(t("stats.oldest", lang, name=name, age=age))

    if stats.avg_age is not None:
        lines.append(t("stats.avg_age", lang, age=round(stats.avg_age)))

    if stats.by_category:
        lines.append("")
        lines.append(t("stats.by_category_title", lang))
        parts = [f"{category_label(cat, lang)} {count}" for cat, count in stats.by_category.items()]
        lines.append(" · ".join(parts))

    if stats.by_month:
        lines.append("")
        lines.append(t("stats.by_month_title", lang))
        max_count = max(stats.by_month.values())
        for month in sorted(stats.by_month):
            count = stats.by_month[month]
            lines.append(f"{_month_label(month, lang)} {_bar(count, max_count)} {count}")

    return "\n".join(lines)


def _home_keyboard(lang: str) -> InlineKeyboardMarkup:
    months_btn = InlineKeyboardButton(
        text=t("stats.by_months_btn", lang), callback_data=StatsCallback(action="months").pack()
    )
    cats_btn = InlineKeyboardButton(
        text=t("stats.by_categories_btn", lang), callback_data=StatsCallback(action="cats").pack()
    )
    ages_btn = InlineKeyboardButton(
        text=t("stats.by_ages_btn", lang), callback_data=StatsCallback(action="ages").pack()
    )
    home_btn = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[months_btn, cats_btn, ages_btn], [home_btn]])


@router.callback_query(MenuCallback.filter(F.action == "stat"))
async def cb_menu_stats(callback: CallbackQuery, session: Any, user: User) -> None:
    stats = await get_user_stats(session, user)
    text = _render_home(stats, user)
    await edit_or_ignore(callback, text, _home_keyboard(user.language))
    await callback.answer()


@router.callback_query(StatsCallback.filter(F.action == "home"))
async def cb_stats_home(callback: CallbackQuery, session: Any, user: User) -> None:
    stats = await get_user_stats(session, user)
    text = _render_home(stats, user)
    await edit_or_ignore(callback, text, _home_keyboard(user.language))
    await callback.answer()


@router.callback_query(StatsCallback.filter(F.action.in_(["months", "cats", "ages"])))
async def cb_stats_drilldown(
    callback: CallbackQuery, callback_data: StatsCallback, session: Any, user: User
) -> None:
    """All three drill-down views reuse the home render — its sections already
    cover months/categories/ages, so a single screen serves every entry point.
    """
    stats = await get_user_stats(session, user)
    text = _render_home(stats, user)
    await edit_or_ignore(callback, text, _home_keyboard(user.language))
    await callback.answer()
