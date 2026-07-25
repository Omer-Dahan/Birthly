from __future__ import annotations

import re
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.callbacks.factories import EventCallback, EventFlowCallback
from app.core.formatting import format_name
from app.core.text import esc
from app.core.validators import (
    ValidationError,
    validate_nickname,
    validate_notes,
    validate_phone,
    validate_relation,
)
from app.db.models import User
from app.handlers.event_card import render_card
from app.i18n.translator import t
from app.keyboards.events import (
    category_picker_keyboard,
    event_type_picker_keyboard,
    field_prompt_keyboard,
    gender_picker_keyboard,
    more_details_keyboard,
)
from app.services.event_service import get_owned_event, update_event_field
from app.services.exceptions import NotFoundError
from app.states.forms import EditEvent
from app.utils.telegram import edit_or_ignore

router = Router(name="event_edit")

_FIELD_VALIDATORS = {
    "relation": validate_relation,
    "phone": validate_phone,
    "nickname": validate_nickname,
    "notes": validate_notes,
}

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


async def _render_more_details(
    callback: CallbackQuery, session: Any, user: User, event_id: int
) -> None:
    event = await get_owned_event(session, user, event_id)
    name = esc(format_name(event.first_name, event.last_name))
    text = t("more.title", user.language, name=name)
    await edit_or_ignore(callback, text, more_details_keyboard(user.language, event))


@router.callback_query(EventCallback.filter(F.action == "e"))
async def cb_event_edit_menu(
    callback: CallbackQuery,
    callback_data: EventCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    """✏️ ערוך on the card — opens the same S6 field picker as ev:more."""
    event_id = callback_data.event_id
    try:
        await state.set_state(EditEvent.choosing_field)
        await state.update_data(event_id=event_id)
        await _render_more_details(callback, session, user, event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await callback.answer()


@router.callback_query(EventFlowCallback.filter(F.action == "more"))
async def cb_more_details(
    callback: CallbackQuery, session: Any, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await state.set_state(EditEvent.choosing_field)
    try:
        await _render_more_details(callback, session, user, event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await callback.answer()


@router.callback_query(EditEvent.choosing_field, EventFlowCallback.filter(F.action == "skip"))
async def cb_more_details_done(
    callback: CallbackQuery, session: Any, user: User, state: FSMContext
) -> None:
    """✅ סיימתי on the S6 field picker — leaves edit mode back to the card."""
    data = await state.get_data()
    event_id = data.get("event_id")
    await state.clear()
    if event_id is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    try:
        text, keyboard = await render_card(session, user, event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(EventFlowCallback.filter(F.action == "field"))
async def cb_field_pick(
    callback: CallbackQuery,
    callback_data: EventFlowCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    field = callback_data.value or ""
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    try:
        event = await get_owned_event(session, user, event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    await state.update_data(editing_field=field)

    if field == "category":
        await state.set_state(EditEvent.entering_value)
        await edit_or_ignore(
            callback,
            t("edit.pick_category", user.language),
            category_picker_keyboard(user.language),
        )
        await callback.answer()
        return
    if field == "gender":
        await state.set_state(EditEvent.entering_value)
        await edit_or_ignore(
            callback, t("edit.pick_gender", user.language), gender_picker_keyboard(user.language)
        )
        await callback.answer()
        return
    if field == "event_type":
        await state.set_state(EditEvent.entering_value)
        await edit_or_ignore(
            callback,
            t("edit.pick_event_type", user.language),
            event_type_picker_keyboard(user.language),
        )
        await callback.answer()
        return

    await state.set_state(EditEvent.entering_value)
    model_field = "photo_file_id" if field == "photo" else field
    has_value = bool(getattr(event, model_field))
    prompt_key = {
        "phone": "edit.phone_prompt",
        "event_time": "edit.time_prompt",
        "photo": "edit.photo_prompt",
    }.get(field, "field.prompt")
    await edit_or_ignore(
        callback,
        t(prompt_key, user.language),
        field_prompt_keyboard(user.language, field, has_value),
    )
    await callback.answer()


@router.callback_query(EditEvent.entering_value, EventFlowCallback.filter(F.action == "cat"))
async def cb_field_set_category(
    callback: CallbackQuery,
    callback_data: EventFlowCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    await _apply_field(callback, session, user, state, "category", callback_data.value)


@router.callback_query(EditEvent.entering_value, EventFlowCallback.filter(F.action == "gender"))
async def cb_field_set_gender(
    callback: CallbackQuery,
    callback_data: EventFlowCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    await _apply_field(callback, session, user, state, "gender", callback_data.value)


@router.callback_query(EditEvent.entering_value, EventFlowCallback.filter(F.action == "type"))
async def cb_field_set_event_type(
    callback: CallbackQuery,
    callback_data: EventFlowCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    await _apply_field(callback, session, user, state, "event_type", callback_data.value)


@router.callback_query(EditEvent.entering_value, EventFlowCallback.filter(F.action == "clear"))
async def cb_field_clear(
    callback: CallbackQuery,
    callback_data: EventFlowCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    await _apply_field(callback, session, user, state, callback_data.value or "", None)


@router.callback_query(EditEvent.entering_value, EventFlowCallback.filter(F.action == "skip"))
async def cb_field_skip(
    callback: CallbackQuery, session: Any, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await state.set_state(EditEvent.choosing_field)
    try:
        await _render_more_details(callback, session, user, event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await callback.answer()


@router.message(EditEvent.entering_value, F.photo)
async def msg_field_photo(message: Message, session: Any, user: User, state: FSMContext) -> None:
    data = await state.get_data()
    field = data.get("editing_field")
    event_id = data.get("event_id")
    if field != "photo" or event_id is None:
        return

    assert message.photo is not None
    file_id = message.photo[-1].file_id
    try:
        await update_event_field(session, user, event_id, photo_file_id=file_id)
    except NotFoundError:
        await message.answer(t("error.not_found", user.language))
        return

    await state.set_state(EditEvent.choosing_field)
    event = await get_owned_event(session, user, event_id)
    name = esc(format_name(event.first_name, event.last_name))
    text = f"{t('edit.field_saved', user.language)}\n\n{t('more.title', user.language, name=name)}"
    await message.answer(text, reply_markup=more_details_keyboard(user.language, event))


@router.message(EditEvent.entering_value)
async def msg_field_value(message: Message, session: Any, user: User, state: FSMContext) -> None:
    data = await state.get_data()
    field = data.get("editing_field")
    event_id = data.get("event_id")
    if field is None or event_id is None:
        return
    if field == "photo":
        return

    raw = message.text or ""

    if field == "event_time":
        m = _TIME_RE.match(raw.strip())
        if not m:
            await message.answer(t("edit.time_error", user.language))
            return
        value: object = f"{int(m.group(1)):02d}:{m.group(2)}"
    else:
        validator = _FIELD_VALIDATORS.get(field)
        if validator is None:
            return
        try:
            value = validator(raw)
        except ValidationError as exc:
            await message.answer(str(exc))
            return

    try:
        await update_event_field(session, user, event_id, **{field: value})
    except NotFoundError:
        await message.answer(t("error.not_found", user.language))
        return

    await state.set_state(EditEvent.choosing_field)
    event = await get_owned_event(session, user, event_id)
    name = esc(format_name(event.first_name, event.last_name))
    text = f"{t('edit.field_saved', user.language)}\n\n{t('more.title', user.language, name=name)}"
    await message.answer(text, reply_markup=more_details_keyboard(user.language, event))


async def _apply_field(
    callback: CallbackQuery,
    session: Any,
    user: User,
    state: FSMContext,
    field: str,
    value: str | None,
) -> None:
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    model_field = "photo_file_id" if field == "photo" else field
    try:
        await update_event_field(session, user, event_id, **{model_field: value})
        await state.set_state(EditEvent.choosing_field)
        await _render_more_details(callback, session, user, event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await callback.answer()
