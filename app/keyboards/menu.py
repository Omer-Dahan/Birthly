from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import MenuCallback
from app.i18n.translator import t


def home_keyboard(lang: str) -> InlineKeyboardMarkup:
    """S1 home screen keyboard: 2 buttons per row, per SPEC.md chapter 15."""

    def btn(key: str, action: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=t(key, lang), callback_data=MenuCallback(action=action).pack()
        )

    rows = [
        [btn("menu.add", "add"), btn("menu.list", "list")],
        [btn("menu.search", "srch"), btn("menu.reminders", "rem")],
        [btn("menu.stats", "stat"), btn("menu.settings", "set")],
        [btn("menu.help", "help")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
