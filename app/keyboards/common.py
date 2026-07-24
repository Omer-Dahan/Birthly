from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import NavCallback


def back_button(text: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=NavCallback(action="back").pack())


def home_button(text: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=NavCallback(action="home").pack())


def cancel_button(text: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=NavCallback(action="cancel").pack())


def single_row_keyboard(*buttons: InlineKeyboardButton) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[list(buttons)])


def build_grid(
    buttons: list[InlineKeyboardButton], columns: int = 2
) -> list[list[InlineKeyboardButton]]:
    """Lay out buttons in rows of ``columns`` (SPEC.md UX rule: max 2 per row)."""
    return [buttons[i : i + columns] for i in range(0, len(buttons), columns)]
