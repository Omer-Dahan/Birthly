from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from aiogram import Bot, Router
from aiogram.types import ErrorEvent

from app.config import settings

logger = logging.getLogger(__name__)
router = Router(name="errors")

# In-memory deduplication cache: dict[error_signature, next_report_time]
_error_cache: dict[str, datetime] = {}


@router.errors()
async def global_error_handler(event: ErrorEvent, bot: Bot) -> None:
    error_id = str(uuid.uuid4())[:4].upper()
    exception = event.exception

    # Deduplication signature: exception class + truncated message.
    signature = f"{type(exception).__name__}:{str(exception)[:50]}"

    logger.error(
        f"Unhandled exception (ID: {error_id}): {exception}",
        exc_info=exception,
        extra={"error_id": error_id, "signature": signature},
    )

    # Notify user if possible
    user_id = None
    update = event.update
    if update.message:
        user_id = update.message.chat.id
    elif update.callback_query and update.callback_query.message:
        user_id = update.callback_query.message.chat.id
        # Also answer callback to avoid loading state
        try:
            await update.callback_query.answer("שגיאה, נסה שוב.", show_alert=True)
        except Exception:
            pass

    if user_id:
        try:
            await bot.send_message(user_id, f"😕 משהו השתבש. נסה שוב בעוד רגע. (קוד: {error_id})")
        except Exception as e:
            logger.error(f"Failed to send error message to user {user_id}: {e}")

    # Notify admins with deduplication
    if getattr(settings, "report_errors_to_admin", False) and settings.admin_ids:
        now = datetime.now(UTC)
        next_report = _error_cache.get(signature)

        if not next_report or now >= next_report:
            _error_cache[signature] = now + timedelta(hours=1)

            admin_msg = (
                f"🚨 <b>שגיאה חדשה במערכת</b> (ID: <code>{error_id}</code>)\n\n"
                f"<b>סוג:</b> {type(exception).__name__}\n"
                f"<b>פרטים:</b> <code>{str(exception)[:500]}</code>\n\n"
                f"<i>* התראה זו הושתקה לשעה הקרובה.</i>"
            )
            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(admin_id, admin_msg)
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
