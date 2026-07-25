from __future__ import annotations

import re
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.callbacks.factories import MenuCallback, SettingsCallback
from app.db.models import User
from app.i18n.translator import t
from app.keyboards.settings import (
    date_format_picker_keyboard,
    language_picker_keyboard,
    notify_time_picker_keyboard,
    settings_keyboard,
    time_format_picker_keyboard,
    timezone_picker_keyboard,
    wipe_warning_keyboard,
)
from app.services.settings_service import (
    InvalidTimezoneError,
    update_setting,
    validate_timezone,
    wipe_account,
)
from app.states.forms import SettingsFlow
from app.utils.telegram import edit_or_ignore

router = Router(name="settings")

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


async def _render_home(callback: CallbackQuery, user: User) -> None:
    text = t("settings.title", user.language)
    await edit_or_ignore(callback, text, settings_keyboard(user))


@router.callback_query(MenuCallback.filter(F.action == "set"))
async def cb_menu_settings(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.clear()
    await _render_home(callback, user)
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "back"))
async def cb_settings_back(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.clear()
    await _render_home(callback, user)
    await callback.answer()


# ── Language ────────────────────────────────────────────────────────────────


@router.callback_query(SettingsCallback.filter(F.action == "lang_menu"))
async def cb_lang_menu(callback: CallbackQuery, user: User) -> None:
    await edit_or_ignore(
        callback,
        t("settings.pick_language", user.language),
        language_picker_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "lang"))
async def cb_lang_set(
    callback: CallbackQuery, callback_data: SettingsCallback, session: Any, user: User
) -> None:
    user = await update_setting(session, user, language=callback_data.value)
    await _render_home(callback, user)
    await callback.answer(t("common.saved", user.language))


# ── Timezone ────────────────────────────────────────────────────────────────


@router.callback_query(SettingsCallback.filter(F.action == "tz_menu"))
async def cb_tz_menu(callback: CallbackQuery, user: User) -> None:
    await edit_or_ignore(
        callback,
        t("settings.pick_timezone", user.language),
        timezone_picker_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "tz"))
async def cb_tz_set(
    callback: CallbackQuery, callback_data: SettingsCallback, session: Any, user: User
) -> None:
    user = await update_setting(session, user, timezone=callback_data.value)
    await _render_home(callback, user)
    await callback.answer(t("common.saved", user.language))


@router.callback_query(SettingsCallback.filter(F.action == "tz_other"))
async def cb_tz_other(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(SettingsFlow.custom_timezone)
    await edit_or_ignore(callback, t("settings.timezone_prompt", user.language))
    await callback.answer()


@router.message(SettingsFlow.custom_timezone)
async def msg_tz_custom(message: Message, session: Any, user: User, state: FSMContext) -> None:
    raw = message.text or ""
    try:
        tz = validate_timezone(raw)
    except InvalidTimezoneError:
        await message.answer(t("settings.timezone_invalid", user.language))
        return

    await update_setting(session, user, timezone=tz)
    await state.clear()
    await message.answer(t("common.saved", user.language), reply_markup=settings_keyboard(user))


# ── Date / time format ──────────────────────────────────────────────────────


@router.callback_query(SettingsCallback.filter(F.action == "df_menu"))
async def cb_df_menu(callback: CallbackQuery, user: User) -> None:
    await edit_or_ignore(
        callback,
        t("settings.pick_date_format", user.language),
        date_format_picker_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "df"))
async def cb_df_set(
    callback: CallbackQuery, callback_data: SettingsCallback, session: Any, user: User
) -> None:
    user = await update_setting(session, user, date_format=callback_data.value)
    await _render_home(callback, user)
    await callback.answer(t("common.saved", user.language))


@router.callback_query(SettingsCallback.filter(F.action == "tf_menu"))
async def cb_tf_menu(callback: CallbackQuery, user: User) -> None:
    await edit_or_ignore(
        callback,
        t("settings.pick_time_format", user.language),
        time_format_picker_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "tf"))
async def cb_tf_set(
    callback: CallbackQuery, callback_data: SettingsCallback, session: Any, user: User
) -> None:
    user = await update_setting(session, user, time_format=callback_data.value)
    await _render_home(callback, user)
    await callback.answer(t("common.saved", user.language))


# ── Default notify time ─────────────────────────────────────────────────────


@router.callback_query(SettingsCallback.filter(F.action == "time_menu"))
async def cb_time_menu(callback: CallbackQuery, user: User) -> None:
    await edit_or_ignore(
        callback,
        t("settings.pick_notify_time", user.language),
        notify_time_picker_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "time"))
async def cb_time_set(
    callback: CallbackQuery, callback_data: SettingsCallback, session: Any, user: User
) -> None:
    packed = callback_data.value or ""
    hh, _, mm = packed.partition("-")
    if not (hh.isdigit() and mm.isdigit()):
        await callback.answer(t("error.generic", user.language), show_alert=True)
        return
    user = await update_setting(session, user, default_notify_time=f"{int(hh):02d}:{mm}")
    await _render_home(callback, user)
    await callback.answer(t("common.saved", user.language))


@router.callback_query(SettingsCallback.filter(F.action == "time_other"))
async def cb_time_other(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(SettingsFlow.custom_time)
    await edit_or_ignore(callback, t("settings.notify_time_prompt", user.language))
    await callback.answer()


@router.message(SettingsFlow.custom_time)
async def msg_time_custom(message: Message, session: Any, user: User, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    match = _TIME_RE.match(raw)
    if not match:
        await message.answer(t("edit.time_error", user.language))
        return

    time_str = f"{int(match.group(1)):02d}:{match.group(2)}"
    await update_setting(session, user, default_notify_time=time_str)
    await state.clear()
    await message.answer(t("common.saved", user.language), reply_markup=settings_keyboard(user))


# ── Simple on/off toggles ───────────────────────────────────────────────────


@router.callback_query(SettingsCallback.filter(F.action == "hebd_toggle"))
async def cb_hebd_toggle(callback: CallbackQuery, session: Any, user: User) -> None:
    user = await update_setting(session, user, show_hebrew_date=not user.show_hebrew_date)
    await _render_home(callback, user)
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "notif_toggle"))
async def cb_notif_toggle(callback: CallbackQuery, session: Any, user: User) -> None:
    user = await update_setting(session, user, notifications_enabled=not user.notifications_enabled)
    await _render_home(callback, user)
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "silent_toggle"))
async def cb_silent_toggle(callback: CallbackQuery, session: Any, user: User) -> None:
    user = await update_setting(session, user, silent_notifications=not user.silent_notifications)
    await _render_home(callback, user)
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "digest_toggle"))
async def cb_digest_toggle(callback: CallbackQuery, session: Any, user: User) -> None:
    user = await update_setting(session, user, daily_digest_enabled=not user.daily_digest_enabled)
    await _render_home(callback, user)
    await callback.answer()


# ── Wipe account ─────────────────────────────────────────────────────────────


@router.callback_query(SettingsCallback.filter(F.action == "wipe"))
async def cb_wipe_warning(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(SettingsFlow.wipe_confirm)
    await edit_or_ignore(
        callback, t("settings.wipe_warning", user.language), wipe_warning_keyboard(user.language)
    )
    await callback.answer()


@router.message(SettingsFlow.wipe_confirm)
async def msg_wipe_confirm(message: Message, session: Any, user: User, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    expected = "מחק" if user.language == "he" else "delete"
    if raw != expected:
        await message.answer(t("settings.wipe_confirm_wrong", user.language))
        return

    await wipe_account(session, user)
    await state.clear()
    await message.answer(t("settings.wipe_done", user.language))
