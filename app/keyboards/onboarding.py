from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import NavCallback, SettingsCallback
from app.i18n.translator import t


def _skip_button(lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=t("onboarding.skip_all", lang), callback_data=NavCallback(action="cancel").pack()
    )


def language_keyboard() -> InlineKeyboardMarkup:
    he = InlineKeyboardButton(
        text=t("onboarding.language.he", "he"),
        callback_data=SettingsCallback(action="lang", value="he").pack(),
    )
    en = InlineKeyboardButton(
        text=t("onboarding.language.en", "en"),
        callback_data=SettingsCallback(action="lang", value="en").pack(),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[he, en], [_skip_button("he")]])


def timezone_keyboard(lang: str) -> InlineKeyboardMarkup:
    israel = InlineKeyboardButton(
        text=t("onboarding.timezone.israel", lang),
        callback_data=SettingsCallback(action="tz", value="Asia/Jerusalem").pack(),
    )
    other = InlineKeyboardButton(
        text=t("onboarding.timezone.other", lang),
        callback_data=SettingsCallback(action="tz", value="other").pack(),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[israel, other], [_skip_button(lang)]])


def notify_time_keyboard(lang: str) -> InlineKeyboardMarkup:
    def btn(hhmm: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=hhmm,
            callback_data=SettingsCallback(action="time", value=hhmm.replace(":", "-")).pack(),
        )

    other = InlineKeyboardButton(
        text=t("onboarding.notify_time.other", lang),
        callback_data=SettingsCallback(action="time", value="other").pack(),
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [btn("09:00"), btn("12:00"), btn("18:00")],
            [other],
            [_skip_button(lang)],
        ]
    )
