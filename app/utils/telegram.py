from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def edit_or_ignore(
    callback: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Edit the message behind a callback, if it's still editable.

    ``callback.message`` can be ``None`` or an ``InaccessibleMessage`` (too
    old to edit) — both cases are silently skipped rather than raising, per
    SPEC.md chapter 26 (a single update must never crash the bot).

    Telegram also rejects an edit whose text and keyboard are byte-identical
    to the current message (e.g. re-tapping a button that leads back to the
    same screen) with "message is not modified" — that's a no-op from the
    user's perspective, not an error, so it's swallowed the same way.
    """
    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as exc:
            if "message is not modified" not in exc.message:
                raise
