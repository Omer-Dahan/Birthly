from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

router = Router(name="fallback")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("✅ הפעולה בוטלה.")


@router.message()
async def fallback_message(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "לא הבנתי. אנא השב בהתאם או לחץ על /cancel כדי לבטל את הפעולה הנוכחית."
        )
    else:
        await message.answer("לא הבנתי את הפקודה. נסה להשתמש בתפריט /start או /help.")


@router.callback_query()
async def fallback_callback(callback: CallbackQuery) -> None:
    await callback.answer("הפעולה אינה זמינה כרגע.", show_alert=True)
