from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.callbacks.factories import NavCallback, SettingsCallback
from app.db.models import User
from app.handlers.menu import render_home
from app.i18n.translator import t
from app.keyboards.onboarding import (
    language_keyboard,
    notify_time_keyboard,
    timezone_keyboard,
)
from app.services.user_service import (
    complete_onboarding,
    set_default_notify_time,
    set_language,
    set_timezone,
)
from app.states.forms import Onboarding
from app.utils.telegram import edit_or_ignore

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message, session: Any, user: User, state: FSMContext
) -> None:
    if user.onboarded:
        text, keyboard = await render_home(session, user)
        await message.answer(text, reply_markup=keyboard)
        return

    await state.set_state(Onboarding.language)
    welcome = t("onboarding.welcome", user.language)
    language_prompt = t("onboarding.language.prompt", user.language)
    await message.answer(
        f"{welcome}\n\n{language_prompt}",
        reply_markup=language_keyboard(),
    )


@router.callback_query(Onboarding.language, SettingsCallback.filter(F.action == "lang"))
async def cb_onboarding_language(
    callback: CallbackQuery,
    callback_data: SettingsCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    await set_language(session, user, callback_data.value or "he")

    await state.set_state(Onboarding.timezone)
    await edit_or_ignore(
        callback,
        t("onboarding.timezone.prompt", user.language),
        timezone_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(Onboarding.timezone, SettingsCallback.filter(F.action == "tz"))
async def cb_onboarding_timezone(
    callback: CallbackQuery,
    callback_data: SettingsCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    if callback_data.value and callback_data.value != "other":
        await set_timezone(session, user, callback_data.value)

    await state.set_state(Onboarding.notify_time)
    await edit_or_ignore(
        callback,
        t("onboarding.notify_time.prompt", user.language),
        notify_time_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(Onboarding.notify_time, SettingsCallback.filter(F.action == "time"))
async def cb_onboarding_notify_time(
    callback: CallbackQuery,
    callback_data: SettingsCallback,
    session: Any,
    user: User,
    state: FSMContext,
) -> None:
    if callback_data.value and callback_data.value != "other":
        await set_default_notify_time(session, user, callback_data.value.replace("-", ":"))

    await _finish_onboarding(callback, session, user, state)


@router.callback_query(Onboarding.language, NavCallback.filter(F.action == "cancel"))
@router.callback_query(Onboarding.timezone, NavCallback.filter(F.action == "cancel"))
@router.callback_query(Onboarding.notify_time, NavCallback.filter(F.action == "cancel"))
async def cb_onboarding_skip_all(
    callback: CallbackQuery, session: Any, user: User, state: FSMContext
) -> None:
    await _finish_onboarding(callback, session, user, state)


async def _finish_onboarding(
    callback: CallbackQuery, session: Any, user: User, state: FSMContext
) -> None:
    await complete_onboarding(session, user)
    await state.clear()

    text, keyboard = await render_home(session, user)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()
