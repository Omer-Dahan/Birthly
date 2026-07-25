from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.callbacks.factories import EventCallback, MenuCallback, NavCallback
from app.core.dates import age_at, days_until
from app.core.formatting import format_countdown, format_name
from app.core.text import esc
from app.db.models import Event, User
from app.i18n.translator import t
from app.services.clock import user_today
from app.services.search_service import search_events
from app.states.forms import Search
from app.utils.telegram import edit_or_ignore

router = Router(name="search")


def _row_label(user: User, event: Event) -> str:
    assert event.next_occurrence is not None
    today = user_today(user)
    name = format_name(event.first_name, event.last_name)
    countdown = format_countdown(days_until(event.next_occurrence, today))
    age = age_at(event.calendar_type, event.year, event.month, event.day, event.next_occurrence)
    if age is not None:
        return f"{name} — {countdown} ({age})"
    return f"{name} — {countdown}"


def _results_keyboard(user: User, events: list[Event]) -> InlineKeyboardMarkup:
    lang = user.language
    rows = [
        [
            InlineKeyboardButton(
                text=esc(_row_label(user, e)),
                callback_data=EventCallback(action="v", event_id=e.id).pack(),
            )
        ]
        for e in events
    ]
    again = InlineKeyboardButton(
        text=t("search.again", lang), callback_data=MenuCallback(action="srch").pack()
    )
    home = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )
    rows.append([again, home])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(MenuCallback.filter(F.action == "srch"))
async def cb_menu_search(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(Search.query)
    text = f"{t('search.title', user.language)}\n<i>{t('search.hint', user.language)}</i>"
    cancel = InlineKeyboardButton(
        text=t("common.cancel", user.language), callback_data=NavCallback(action="cancel").pack()
    )
    await edit_or_ignore(callback, text, InlineKeyboardMarkup(inline_keyboard=[[cancel]]))
    await callback.answer()


@router.message(Search.query)
async def msg_search_query(message: Message, session: Any, user: User, state: FSMContext) -> None:
    query = (message.text or "").strip()
    if not query:
        return

    events = await search_events(session, user, query)
    await state.clear()

    lang = user.language
    if not events:
        text = t("search.no_results", lang, query=esc(query))
        again = InlineKeyboardButton(
            text=t("search.again", lang), callback_data=MenuCallback(action="srch").pack()
        )
        home = InlineKeyboardButton(
            text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[again, home]])
        await message.answer(text, reply_markup=keyboard)
        return

    text = t("search.results_title", lang, count=len(events))
    await message.answer(text, reply_markup=_results_keyboard(user, events))
