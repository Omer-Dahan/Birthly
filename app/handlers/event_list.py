from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.callbacks.factories import ListCallback, MenuCallback
from app.config import settings
from app.core.dates import age_at, days_until
from app.core.formatting import format_countdown, format_name
from app.core.text import esc
from app.db.models import Event, User
from app.db.repositories.events import EventRepository
from app.i18n.translator import t
from app.keyboards.events import list_keyboard
from app.services.clock import user_today
from app.utils.telegram import edit_or_ignore

router = Router(name="event_list")


def _row_label(user: User, event: Event) -> str:
    assert event.next_occurrence is not None  # cached at create/update time

    today = user_today(user)
    name = format_name(event.first_name, event.last_name)
    countdown = format_countdown(days_until(event.next_occurrence, today))

    age = age_at(event.calendar_type, event.year, event.month, event.day, event.next_occurrence)
    if age is not None:
        return f"{name} — {countdown} ({age})"
    return f"{name} — {countdown}"


async def _render_list(session: Any, user: User, *, page: int) -> tuple[str, Any]:
    repo = EventRepository(session, user.id)
    sort = user.list_sort
    events, total = await repo.list_page(
        sort=sort, page=page, page_size=settings.page_size, view="upcoming"
    )

    lang = user.language
    if total == 0:
        text = f"{t('list.title', lang, count=0)}\n\n{t('list.empty', lang)}"
    else:
        header = t("list.title", lang, count=total)
        sort_line = t(f"list.sort_{sort}", lang)
        filter_line = t("list.filter_all", lang)
        text = f"{header}\n{sort_line}  ·  {filter_line}"

    row_labels = [(e.id, esc(_row_label(user, e))) for e in events]
    total_pages = max(1, (total + settings.page_size - 1) // settings.page_size)
    keyboard = list_keyboard(lang, row_labels, page, total_pages)
    return text, keyboard


@router.callback_query(MenuCallback.filter(F.action == "list"))
async def cb_menu_list(callback: CallbackQuery, session: Any, user: User) -> None:
    text, keyboard = await _render_list(session, user, page=0)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(ListCallback.filter(F.action == "p"))
async def cb_list_page(
    callback: CallbackQuery, callback_data: ListCallback, session: Any, user: User
) -> None:
    page = int(callback_data.value)
    text, keyboard = await _render_list(session, user, page=page)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()
