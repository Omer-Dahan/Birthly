from __future__ import annotations

from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.callbacks.factories import AdminCallback
from app.db.models import User
from app.keyboards.admin import admin_home_kb, back_to_admin_kb, broadcast_confirm_kb
from app.services.admin_service import (
    force_backup,
    get_broadcast_targets,
    get_recent_logs,
    get_system_stats,
    get_user_info,
    toggle_block_user,
)
from app.states.forms import AdminFlow
from app.utils.ratelimit import AsyncRateLimiter
from app.utils.telegram import edit_or_ignore

router = Router(name="admin")


# Filter to restrict this entire router to admins. Must subclass aiogram's
# Filter — a bare class's __call__ is never awaited by the dispatcher, so it
# evaluates as a truthy coroutine object and the check silently always passes.
class IsAdminFilter(Filter):
    async def __call__(self, event: Message | CallbackQuery, user: User) -> bool:
        return user.is_admin


router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


def _admin_home_text(stats: dict[str, Any]) -> str:
    return (
        f"🛠 <b>ניהול</b>\n\n"
        f"👥 משתמשים: {stats['total_users']}  (פעילים 30 יום: {stats['active_users']})\n"
        f"🎂 אירועים: {stats['total_events']}\n"
        f"🔔 תזכורות נשלחו היום: {stats['sent_today']}  (נכשלו: {stats['failed_today']})\n"
        f"💾 DB: {stats['db_size_mb']} MB  ·  גיבוי אחרון: {stats['last_backup']}\n"
        f"⏱ טיק אחרון: {stats['last_tick_at']}\n"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: Any) -> None:
    stats = await get_system_stats(session)
    await message.answer(_admin_home_text(stats), reply_markup=admin_home_kb())


@router.callback_query(AdminCallback.filter(F.action == "home"))
async def cq_admin_home(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    await state.clear()
    stats = await get_system_stats(session)
    await edit_or_ignore(callback, _admin_home_text(stats), admin_home_kb())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "stats"))
@router.message(Command("dbstats"))
async def cq_admin_stats(event: Message | CallbackQuery, session: Any) -> None:
    stats = await get_system_stats(session)
    text = "\n".join([f"{k}: {v}" for k, v in stats.items()])
    full_text = f"📊 <b>סטטיסטיקות מתקדמות</b>\n\n{text}"
    if isinstance(event, CallbackQuery):
        await edit_or_ignore(event, full_text, back_to_admin_kb())
        await event.answer()
    else:
        await event.answer(full_text)


@router.callback_query(AdminCallback.filter(F.action == "bc"))
@router.message(Command("broadcast"))
async def cq_admin_bc(event: Message | CallbackQuery, state: FSMContext) -> None:
    text = "📢 <b>הודעה לכולם</b>\n\nאנא הקלד את תוכן ההודעה שתרצה לשלוח לכל המשתמשים הפעילים:"
    if isinstance(event, CallbackQuery):
        await edit_or_ignore(event, text, back_to_admin_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=back_to_admin_kb())
    await state.set_state(AdminFlow.broadcast_text)


@router.message(AdminFlow.broadcast_text)
async def process_bc_text(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("אנא שלח טקסט בלבד.")
        return

    await state.update_data(bc_text=message.html_text)
    text = f"📢 <b>תצוגה מקדימה:</b>\n\n{message.html_text}\n\nהאם לשלוח הודעה זו?"
    await message.answer(text, reply_markup=broadcast_confirm_kb())
    await state.set_state(AdminFlow.broadcast_confirm)


@router.callback_query(AdminCallback.filter(F.action == "bc_ok"), AdminFlow.broadcast_confirm)
async def cq_admin_bc_ok(
    callback: CallbackQuery, bot: Bot, session: Any, state: FSMContext, user: User
) -> None:
    data = await state.get_data()
    bc_text = data.get("bc_text")
    if not bc_text:
        await callback.answer("שגיאה, נסה שוב.", show_alert=True)
        return

    await edit_or_ignore(callback, "⏳ שולח... אנא המתן.")

    # Awaited directly rather than dispatched to a background task: the rate
    # limiter caps this at 20 sends/sec, so even a few hundred users finishes
    # within Telegram's callback-response window.
    targets = await get_broadcast_targets(session, user.id, bc_text)
    limiter = AsyncRateLimiter(rate=20)
    sent = 0
    blocked = 0
    for target in targets:
        await limiter.acquire()
        try:
            await bot.send_message(target.id, bc_text)
            sent += 1
        except Exception:
            blocked += 1

    done_text = f"✅ <b>סיום שליחה</b>\n\nנשלח בהצלחה: {sent}\nנכשלו/חסמו: {blocked}"
    await edit_or_ignore(callback, done_text, back_to_admin_kb())
    await state.clear()
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "logs"))
@router.message(Command("logs"))
async def cq_admin_logs(event: Message | CallbackQuery, bot: Bot) -> None:
    n = 50
    if isinstance(event, Message) and event.text:
        parts = event.text.split()
        if len(parts) > 1 and parts[1].isdigit():
            n = int(parts[1])

    logs_text = get_recent_logs(n)

    if isinstance(event, CallbackQuery):
        await event.answer()
        if event.message is None:
            return
        chat_id = event.message.chat.id
    else:
        chat_id = event.chat.id

    log_file = BufferedInputFile(logs_text.encode("utf-8"), filename="bot_logs.txt")
    await bot.send_document(chat_id, log_file, caption=f"הנה {n} השורות האחרונות מהלוג.")


@router.callback_query(AdminCallback.filter(F.action == "u"))
async def cq_admin_user_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    text = (
        "👤 לחיפוש משתמש אנא שלח את הפקודה:\n"
        "<code>/userinfo &lt;id or username&gt;</code>\n"
        "או <code>/block &lt;id&gt;</code> ו-<code>/unblock &lt;id&gt;</code>."
    )
    await edit_or_ignore(callback, text, back_to_admin_kb())
    await callback.answer()


@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message, session: Any) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("שימוש: /userinfo <id או שם משתמש>")
        return

    ident = parts[1]
    info = await get_user_info(session, ident)

    if not info:
        await message.answer("לא נמצא משתמש כזה.")
        return

    text = (
        f"👤 <b>פרטי משתמש</b>\n"
        f"ID: <code>{info['id']}</code>\n"
        f"שם: {info['name']}\n"
        f"יוזרניים: @{info['username'] or '—'}\n"
        f"אירועים: {info['events_count']}\n"
        f"נוצר ב: {info['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        f"נראה לאחרונה: {info['last_seen_at'].strftime('%Y-%m-%d %H:%M')}\n"
        f"חסום ע״י אדמין: {'✅ כן' if info['is_blocked'] else '❌ לא'}\n"
        f"חסם את הבוט: {'✅ כן' if info['bot_blocked'] else '❌ לא'}"
    )
    await message.answer(text)


@router.message(Command("block"))
async def cmd_block(message: Message, session: Any, user: User) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("שימוש: /block <id>")
        return

    target_id = int(parts[1])
    success = await toggle_block_user(session, user.id, target_id, True)
    if success:
        await message.answer(f"משתמש {target_id} נחסם בהצלחה.")
    else:
        await message.answer("משתמש לא נמצא.")


@router.message(Command("unblock"))
async def cmd_unblock(message: Message, session: Any, user: User) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("שימוש: /unblock <id>")
        return

    target_id = int(parts[1])
    success = await toggle_block_user(session, user.id, target_id, False)
    if success:
        await message.answer(f"משתמש {target_id} שוחרר בהצלחה.")
    else:
        await message.answer("משתמש לא נמצא.")


@router.callback_query(AdminCallback.filter(F.action == "backup"))
@router.message(Command("forcebackup"))
async def cq_admin_backup(
    event: Message | CallbackQuery, session: Any, user: User
) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer("מבצע גיבוי...")
    path = await force_backup(session, user.id)
    text = f"✅ גיבוי ידני בוצע בהצלחה:\n<code>{path}</code>"
    if isinstance(event, CallbackQuery):
        await edit_or_ignore(event, text, back_to_admin_kb())
    else:
        await event.answer(text)
