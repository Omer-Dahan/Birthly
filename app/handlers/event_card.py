from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.callbacks.factories import EventCallback
from app.core.formatting import format_name
from app.core.text import esc
from app.db.models import User
from app.db.repositories.reminders import ReminderRuleRepository
from app.i18n.translator import t
from app.keyboards.events import card_keyboard, delete_confirm_keyboard, delete_done_keyboard
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


async def render_card(session: Any, user: User, event_id: int) -> tuple[str, Any]:
    event = await get_owned_event(session, user, event_id)
    rule_repo = ReminderRuleRepository(session, user.id)
    rules = await rule_repo.list_for_event(event_id)
    text = render_card_text(user, event, rules)
    keyboard = card_keyboard(user.language, event_id, event.is_active)
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
    text = t("delete.done", user.language, name=name)
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
    await callback.answer(t("delete.restored", user.language, name=name), show_alert=False)

    text, keyboard = await render_card(session, user, callback_data.event_id)
    await edit_or_ignore(callback, text, keyboard)
