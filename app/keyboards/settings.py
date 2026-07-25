from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import NavCallback, SettingsCallback
from app.constants import DateFormat, Language, TimeFormat
from app.db.models import User
from app.i18n.translator import t


def _mark(value: bool) -> str:
    return "✅" if value else "⬜"


def settings_keyboard(user: User) -> InlineKeyboardMarkup:
    lang = user.language

    def nav(key: str, action: str, value: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=t(key, lang, value=value), callback_data=SettingsCallback(action=action).pack()
        )

    home = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                nav(
                    "settings.language",
                    "lang_menu",
                    t(f"onboarding.language.{user.language}", lang),
                )
            ],
            [nav("settings.timezone", "tz_menu", user.timezone)],
            [nav("settings.notify_time", "time_menu", user.default_notify_time)],
            [nav("settings.date_format", "df_menu", user.date_format)],
            [nav("settings.time_format", "tf_menu", user.time_format)],
            [nav("settings.show_hebrew_date", "hebd_toggle", _mark(user.show_hebrew_date))],
            [nav("settings.notifications", "notif_toggle", _mark(user.notifications_enabled))],
            [
                nav(
                    "settings.silent_notifications",
                    "silent_toggle",
                    _mark(user.silent_notifications),
                )
            ],
            [nav("settings.daily_digest", "digest_toggle", _mark(user.daily_digest_enabled))],
            [
                InlineKeyboardButton(
                    text=t("settings.backup_menu", lang),
                    callback_data=SettingsCallback(action="backup").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("settings.wipe_account", lang),
                    callback_data=SettingsCallback(action="wipe").pack(),
                )
            ],
            [home],
        ]
    )


def language_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=t(f"onboarding.language.{lg.value}", lang),
            callback_data=SettingsCallback(action="lang", value=lg.value).pack(),
        )
        for lg in Language
    ]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=SettingsCallback(action="back").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [back]])


def timezone_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    israel = InlineKeyboardButton(
        text=t("settings.timezone_israel", lang),
        callback_data=SettingsCallback(action="tz", value="Asia/Jerusalem").pack(),
    )
    ny = InlineKeyboardButton(
        text=t("settings.timezone_ny", lang),
        callback_data=SettingsCallback(action="tz", value="America/New_York").pack(),
    )
    london = InlineKeyboardButton(
        text=t("settings.timezone_london", lang),
        callback_data=SettingsCallback(action="tz", value="Europe/London").pack(),
    )
    other = InlineKeyboardButton(
        text=t("settings.timezone_other", lang),
        callback_data=SettingsCallback(action="tz_other").pack(),
    )
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=SettingsCallback(action="back").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[israel, ny], [london, other], [back]])


def date_format_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=fmt.value, callback_data=SettingsCallback(action="df", value=fmt.value).pack()
        )
        for fmt in DateFormat
    ]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=SettingsCallback(action="back").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [back]])


def time_format_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=fmt.value, callback_data=SettingsCallback(action="tf", value=fmt.value).pack()
        )
        for fmt in TimeFormat
    ]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=SettingsCallback(action="back").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [back]])


def notify_time_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    choices = ["08:00", "09:00", "10:00", "18:00", "20:00"]
    buttons = [
        InlineKeyboardButton(
            text=tm,
            callback_data=SettingsCallback(action="time", value=tm.replace(":", "-")).pack(),
        )
        for tm in choices
    ]
    other = InlineKeyboardButton(
        text=t("settings.notify_time_other", lang),
        callback_data=SettingsCallback(action="time_other").pack(),
    )
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    rows.append([other])
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=SettingsCallback(action="back").pack()
    )
    rows.append([back])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def wipe_warning_keyboard(lang: str) -> InlineKeyboardMarkup:
    cancel = InlineKeyboardButton(
        text=t("common.cancel", lang), callback_data=SettingsCallback(action="back").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[cancel]])
