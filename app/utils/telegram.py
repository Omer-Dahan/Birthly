from __future__ import annotations

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def edit_or_ignore(
    callback: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Edit the message behind a callback, if it's still editable.

    ``callback.message`` can be ``None`` or an ``InaccessibleMessage`` (too
    old to edit) — both cases are silently skipped rather than raising, per
    SPEC.md chapter 26 (a single update must never crash the bot).
    """
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=reply_markup)
