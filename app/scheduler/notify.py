"""Telegram-facing reminder delivery.

Lives in app/scheduler (not app/services) because it touches aiogram's Bot
and exception types directly — app/services must stay framework-agnostic
(SPEC.md ch.5). Pure text rendering stays in app.services.notify_service.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Event, NotificationLog, ReminderRule, User
from app.db.repositories.notifications import NotificationRepository
from app.db.repositories.users import UserRepository
from app.services.notify_service import render_reminder
from app.utils.ratelimit import AsyncRateLimiter

logger = logging.getLogger(__name__)

# Global send rate limiter: max 20 messages / second (SPEC.md ch.18)
_send_limiter = AsyncRateLimiter(rate=settings.broadcast_rate_per_sec)


def reminder_keyboard(event_id: int, lang: str = "he") -> InlineKeyboardMarkup:
    """Action keyboard shown below a reminder push (SPEC.md S16)."""
    if lang == "he":
        btn_greeting = InlineKeyboardButton(text="💌 ברכה", callback_data=f"ev:gr:{event_id}")
        btn_card = InlineKeyboardButton(text="👤 הכרטיס", callback_data=f"ev:v:{event_id}")
        btn_mute = InlineKeyboardButton(text="🔕 השתק", callback_data=f"ev:mute:{event_id}")
    else:
        btn_greeting = InlineKeyboardButton(text="💌 Greeting", callback_data=f"ev:gr:{event_id}")
        btn_card = InlineKeyboardButton(text="👤 Card", callback_data=f"ev:v:{event_id}")
        btn_mute = InlineKeyboardButton(text="🔕 Mute", callback_data=f"ev:mute:{event_id}")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [btn_greeting, btn_card],
            [btn_mute],
        ]
    )


async def send(
    bot: Bot,
    session: AsyncSession,
    user: User,
    event: Event,
    rule: ReminderRule,
    log: NotificationLog,
    occurrence_year: int,
) -> bool:
    """Send a single reminder message and update the log row.

    Returns True on success, False on failure.
    Handles TelegramForbiddenError (bot blocked) and TelegramRetryAfter.
    """
    notif_repo = NotificationRepository(session)

    text = render_reminder(user, event, rule, occurrence_year)
    kb = reminder_keyboard(event.id, user.language)

    for attempt in range(3):
        try:
            await _send_limiter.acquire()
            await bot.send_message(
                user.id,
                text,
                reply_markup=kb,
                parse_mode="HTML",
                disable_notification=user.silent_notifications,
            )
            await notif_repo.mark_sent(log.id)
            logger.info(
                "reminder_sent",
                extra={
                    "user_id": user.id,
                    "event_id": event.id,
                    "rule_id": rule.id,
                    "log_id": log.id,
                    "attempt": attempt + 1,
                },
            )
            return True

        except TelegramForbiddenError:
            # User blocked the bot — disable notifications permanently.
            # ``user`` was loaded in a different (now-closed) session than
            # this one, so mutating it directly wouldn't persist — fetch a
            # fresh, session-attached instance instead.
            user_repo = UserRepository(session)
            db_user = await user_repo.get(user.id)
            if db_user is not None:
                db_user.bot_blocked_by_user = True
                db_user.notifications_enabled = False
                await session.commit()
            await notif_repo.mark_failed(log.id, "bot_blocked_by_user")
            logger.warning(
                "bot_blocked_by_user",
                extra={"user_id": user.id, "event_id": event.id},
            )
            return False

        except TelegramRetryAfter as exc:
            wait = exc.retry_after + 1
            logger.warning(
                "telegram_retry_after",
                extra={"user_id": user.id, "wait_seconds": wait, "attempt": attempt + 1},
            )
            if attempt < 2:
                await asyncio.sleep(wait)
            else:
                await notif_repo.mark_failed(log.id, "TelegramRetryAfter after 3 attempts")
                return False

        except Exception as exc:  # noqa: BLE001
            err = str(exc)[:400]
            logger.error(
                "reminder_send_error",
                extra={"user_id": user.id, "event_id": event.id, "error": err},
                exc_info=True,
            )
            await notif_repo.mark_failed(log.id, err)
            return False

    return False
