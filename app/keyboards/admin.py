from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks.factories import AdminCallback, NavCallback


def admin_home_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 סטטיסטיקות", callback_data=AdminCallback(action="stats"))
    builder.button(text="📢 הודעה לכולם", callback_data=AdminCallback(action="bc"))
    builder.button(text="📜 לוגים", callback_data=AdminCallback(action="logs"))
    builder.button(text="👤 חיפוש משתמש", callback_data=AdminCallback(action="u"))
    builder.button(text="💾 גיבוי עכשיו", callback_data=AdminCallback(action="backup"))
    builder.button(text="🏠 בית", callback_data=NavCallback(action="home"))
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ שלח תפוצה", callback_data=AdminCallback(action="bc_ok"))
    builder.button(text="❌ ביטול", callback_data=AdminCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="← חזרה לאדמין", callback_data=AdminCallback(action="home"))
    builder.adjust(1)
    return builder.as_markup()
