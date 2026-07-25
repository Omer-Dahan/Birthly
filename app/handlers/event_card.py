from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.callbacks.factories import EventCallback
from app.core.dates import age_at, days_until
from app.core.formatting import format_countdown, format_date, format_name
from app.core.text import esc
from app.db.models import User
from app.db.repositories.reminders import ReminderRuleRepository
from app.i18n.translator import t
from app.keyboards.events import card_keyboard, delete_confirm_keyboard, delete_done_keyboard
from app.services.clock import user_today
from app.services.event_card_service import render_card_text
from app.services.event_service import (
    delete_event,
    get_owned_event,
    restore_event,
    toggle_mute,
)
from app.services.exceptions import NotFoundError
from app.utils.telegram import edit_or_ignore

router = Router(name="event_card")


def _share_text(user: User, event: Any) -> str:
    """Plain-text one-liner for the card's switch_inline_query share button."""
    assert event.next_occurrence is not None
    name = format_name(event.first_name, event.last_name)
    today = user_today(user)
    countdown = format_countdown(days_until(event.next_occurrence, today))
    date_str = format_date(event.next_occurrence, user.date_format)
    age = age_at(event.calendar_type, event.year, event.month, event.day, event.next_occurrence)
    if age is not None:
        return f"🎂 {name} — {date_str} ({age}) — {countdown}"
    return f"🎂 {name} — {date_str} — {countdown}"


async def render_card(session: Any, user: User, event_id: int) -> tuple[str, Any]:
    event = await get_owned_event(session, user, event_id)
    rule_repo = ReminderRuleRepository(session, user.id)
    rules = await rule_repo.list_for_event(event_id)
    text = render_card_text(user, event, rules)
    keyboard = card_keyboard(user.language, event_id, event.is_active, _share_text(user, event))
    return text, keyboard


@router.callback_query(EventCallback.filter(F.action == "v"))
async def cb_event_view(
    callback: CallbackQuery, callback_data: EventCallback, session: Any, user: User
) -> None:
    try:
        text, keyboard = await render_card(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(EventCallback.filter(F.action == "mute"))
async def cb_event_mute(
    callback: CallbackQuery, callback_data: EventCallback, session: Any, user: User
) -> None:
    try:
        await toggle_mute(session, user, callback_data.event_id)
        text, keyboard = await render_card(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(EventCallback.filter(F.action == "d"))
async def cb_event_delete_confirm(
    callback: CallbackQuery, callback_data: EventCallback, session: Any, user: User
) -> None:
    try:
        event = await get_owned_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    name = esc(format_name(event.first_name, event.last_name))
    text = (
        f"{t('delete.confirm.title', user.language, name=name)}\n\n"
        f"{t('delete.confirm.body', user.language)}"
    )
    keyboard = delete_confirm_keyboard(user.language, callback_data.event_id)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(EventCallback.filter(F.action == "dy"))
async def cb_event_delete_confirmed(
    callback: CallbackQuery, callback_data: EventCallback, session: Any, user: User
) -> None:
    try:
        event = await delete_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    name = esc(format_name(event.first_name, event.last_name))
    text = t("delete.done", user.language, name=name, gender=event.gender)
    keyboard = delete_done_keyboard(user.language, callback_data.event_id)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(EventCallback.filter(F.action == "undo"))
async def cb_event_restore(
    callback: CallbackQuery, callback_data: EventCallback, session: Any, user: User
) -> None:
    try:
        event = await restore_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    name = esc(format_name(event.first_name, event.last_name))
    await callback.answer(t("delete.restored", user.language, name=name, gender=event.gender), show_alert=False)

    text, keyboard = await render_card(session, user, callback_data.event_id)
    await edit_or_ignore(callback, text, keyboard)
