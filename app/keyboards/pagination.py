from __future__ import annotations

from aiogram.types import InlineKeyboardButton

from app.callbacks.factories import ListCallback, NoopCallback


def page_row(page: int, total_pages: int) -> list[InlineKeyboardButton]:
    """The [◀️] [n/total] [▶️] row. Prev/next are noop buttons at the edges."""
    prev_button = InlineKeyboardButton(
        text="◀️",
        callback_data=(
            ListCallback(action="p", value=str(page - 1)).pack()
            if page > 0
            else NoopCallback().pack()
        ),
    )
    label = InlineKeyboardButton(
        text=f"{page + 1}/{max(total_pages, 1)}", callback_data=NoopCallback().pack()
    )
    next_button = InlineKeyboardButton(
        text="▶️",
        callback_data=(
            ListCallback(action="p", value=str(page + 1)).pack()
            if page + 1 < total_pages
            else NoopCallback().pack()
        ),
    )
    return [prev_button, label, next_button]
