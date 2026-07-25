from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.callbacks.factories import EventCallback, MenuCallback, ReminderCallback
from app.constants import MAX_REMINDER_RULES_GLOBAL, MAX_REMINDER_RULES_PER_EVENT
from app.core.formatting import format_name
from app.core.text import esc
from app.db.models import ReminderRule, User
from app.db.repositories.reminders import ReminderRuleRepository
from app.i18n.translator import t
from app.keyboards.reminders import (
    add_rule_keyboard,
    rule_menu_keyboard,
    rules_list_keyboard,
    time_choice_keyboard,
)
from app.services.event_service import get_owned_event
from app.services.exceptions import NotFoundError
from app.services.reminder_service import offset_label
from app.utils.telegram import edit_or_ignore

router = Router(name="reminders")


async def _render_rules(
    callback: CallbackQuery, session: Any, user: User, event_id: int | None
) -> None:
    rule_repo = ReminderRuleRepository(session, user.id)
    if event_id is None:
        rules = await rule_repo.list_global()
        text = f"{t('rem.global.title', user.language)}\n\n{t('rem.global.hint', user.language)}"
    else:
        event = await get_owned_event(session, user, event_id)
        rules = await rule_repo.list_for_event(event_id)
        name = esc(format_name(event.first_name, event.last_name))
        text = t("rem.event.title", user.language, name=name)

    keyboard = rules_list_keyboard(user.language, rules, event_id)
    await edit_or_ignore(callback, text, keyboard)


@router.callback_query(MenuCallback.filter(F.action == "rem"))
async def cb_menu_reminders(
    callback: CallbackQuery, session: Any, user: User, state: FSMContext
) -> None:
    await state.update_data(rem_event_id=None)
    await _render_rules(callback, session, user, None)
    await callback.answer()


@router.callback_query(EventCallback.filter(F.action == "rem"))
async def cb_event_reminders(
    callback: CallbackQuery,
    callback_data: EventCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    event_id = callback_data.event_id
    try:
        await state.update_data(rem_event_id=event_id)
        await _render_rules(callback, session, user, event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "back"))
async def cb_rem_back(
    callback: CallbackQuery,
    callback_data: ReminderCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    await _render_rules(callback, session, user, callback_data.event_id)
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "add"))
async def cb_rem_add(callback: CallbackQuery, callback_data: ReminderCallback, user: User) -> None:
    await edit_or_ignore(
        callback,
        t("rem.add_title", user.language),
        add_rule_keyboard(user.language, callback_data.event_id),
    )
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "off"))
async def cb_rem_pick_offset(
    callback: CallbackQuery, callback_data: ReminderCallback, session: Any, user: User
) -> None:
    event_id = callback_data.event_id
    offset_days = int(callback_data.value or "0")

    rule_repo = ReminderRuleRepository(session, user.id)
    existing = (
        await rule_repo.count_for_event(event_id) if event_id else await rule_repo.count_global()
    )
    limit = MAX_REMINDER_RULES_PER_EVENT if event_id else MAX_REMINDER_RULES_GLOBAL
    if existing >= limit:
        await callback.answer(t("rem.max_reached", user.language, max=limit), show_alert=True)
        return

    if event_id is not None:
        try:
            await get_owned_event(session, user, event_id)
        except NotFoundError:
            await callback.answer(t("error.not_found", user.language), show_alert=True)
            return

    rule = ReminderRule(user_id=user.id, event_id=event_id, offset_days=offset_days, send_time=None)
    await rule_repo.create(rule)

    label = offset_label(offset_days, user.language)
    await callback.answer(t("rem.added", user.language, label=label, time=user.default_notify_time))
    await _render_rules(callback, session, user, event_id)


@router.callback_query(ReminderCallback.filter(F.action == "menu"))
async def cb_rem_rule_menu(
    callback: CallbackQuery, callback_data: ReminderCallback, session: Any, user: User
) -> None:
    rule_id = int(callback_data.value or "0")
    rule_repo = ReminderRuleRepository(session, user.id)
    rule = await rule_repo.get_owned(rule_id)
    if rule is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    label = offset_label(rule.offset_days, user.language) if rule.offset_days is not None else "?"
    time_str = rule.send_time or user.default_notify_time
    text = t("rem.rule_menu_title", user.language, label=label, time=time_str)
    await edit_or_ignore(
        callback, text, rule_menu_keyboard(user.language, rule_id, callback_data.event_id)
    )
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "tog"))
async def cb_rem_toggle(
    callback: CallbackQuery, callback_data: ReminderCallback, session: Any, user: User
) -> None:
    rule_repo = ReminderRuleRepository(session, user.id)
    rule = await rule_repo.get_owned(int(callback_data.value or "0"))
    if rule is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await rule_repo.toggle(rule)
    await _render_rules(callback, session, user, callback_data.event_id)
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "del"))
async def cb_rem_delete(
    callback: CallbackQuery, callback_data: ReminderCallback, session: Any, user: User
) -> None:
    rule_repo = ReminderRuleRepository(session, user.id)
    rule = await rule_repo.get_owned(int(callback_data.value or "0"))
    if rule is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await rule_repo.delete(rule)
    await callback.answer(t("rem.deleted", user.language))
    await _render_rules(callback, session, user, callback_data.event_id)


@router.callback_query(ReminderCallback.filter(F.action == "time_menu"))
async def cb_rem_time_menu(
    callback: CallbackQuery, callback_data: ReminderCallback, user: User
) -> None:
    rule_id = int(callback_data.value or "0")
    await edit_or_ignore(
        callback,
        t("rem.change_time", user.language),
        time_choice_keyboard(user.language, rule_id, callback_data.event_id),
    )
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "time"))
async def cb_rem_set_time(
    callback: CallbackQuery, callback_data: ReminderCallback, session: Any, user: User
) -> None:
    packed = callback_data.value or ""
    time_part, _, rule_id_part = packed.rpartition(":")
    hh, _, mm = time_part.partition("-")
    if not (hh.isdigit() and mm.isdigit() and rule_id_part.isdigit()):
        await callback.answer(t("error.generic", user.language), show_alert=True)
        return
    send_time = f"{int(hh):02d}:{mm}"

    rule_repo = ReminderRuleRepository(session, user.id)
    rule = await rule_repo.get_owned(int(rule_id_part))
    if rule is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    rule.send_time = send_time
    await rule_repo.update(rule)

    await callback.answer(t("common.saved", user.language))
    await _render_rules(callback, session, user, callback_data.event_id)
