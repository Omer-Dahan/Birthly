"""APScheduler job functions.

Every job receives only what it needs (bot, session_factory) and is
wrapped in a try/except so a failing job never crashes the scheduler.

Dependency graph (SPEC.md ch.17):
    jobs → services → repositories → db.models
    jobs never import handlers or keyboards (except app.scheduler.notify,
    which builds a minimal InlineKeyboardMarkup for push messages).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.core.dates import next_occurrence as compute_next_occurrence
from app.db.models import Event, ReminderRule, User
from app.db.repositories.events import EventRepository
from app.db.repositories.notifications import NotificationRepository
from app.scheduler import notify

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: parse HH:MM string → (hour, minute)
# ──────────────────────────────────────────────────────────────────────────────


def _parse_hhmm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)


# ──────────────────────────────────────────────────────────────────────────────
# Core tick: reminder engine (SPEC.md ch.18)
# ──────────────────────────────────────────────────────────────────────────────


async def tick_reminders(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
    now_utc: datetime | None = None,
) -> None:
    """Main reminder engine tick — runs every SCHEDULER_TICK_SECONDS seconds.

    Algorithm (SPEC.md ch.18):
      1. Query users with events in the next MAX_UPCOMING_DAYS window.
      2. For each user, compute fire_utc for every (event × rule) pair.
      3. If fire_utc <= now_utc and within GRACE, insert pending log row
         (UNIQUE prevents double-send), then send.
      4. Recompute next_occurrence for events whose occurrence == today.

    ``now_utc`` defaults to the real current time; tests pass it explicitly
    instead of using freezegun, which corrupts aiosqlite's async greenlet
    bridge when a wall-clock freeze wraps an ``await`` on the DB session.
    """
    now_utc = now_utc if now_utc is not None else datetime.now(UTC)
    grace = timedelta(hours=settings.reminder_grace_hours)

    async with session_factory() as session:
        notif_repo = NotificationRepository(session)

        window_start = now_utc.date()
        window_end = window_start + timedelta(days=settings.max_upcoming_days)

        users = await notif_repo.list_active_users_with_events(window_start, window_end)
        logger.debug("tick_start", extra={"user_count": len(users), "now_utc": now_utc.isoformat()})

        send_tasks: list[tuple[User, Event, ReminderRule, int, int]] = []
        # (user, event, rule, log_id, occurrence_year)

        for user in users:
            tz = ZoneInfo(user.timezone)
            now_local = now_utc.astimezone(tz)
            today_local = now_local.date()

            events = await notif_repo.get_active_events_for_user(user.id, window_start, window_end)
            rules = await notif_repo.get_rules_for_user(user.id)

            # Split into global rules and per-event rules
            global_rules = [r for r in rules if r.event_id is None]
            per_event_rules: dict[int, list[ReminderRule]] = {}
            for r in rules:
                if r.event_id is not None:
                    per_event_rules.setdefault(r.event_id, []).append(r)

            for event in events:
                occ: date | None = event.next_occurrence
                if occ is None:
                    continue

                # Per-event rules override global rules with the same offset_days
                event_specific = per_event_rules.get(event.id, [])
                overridden_offsets = {
                    r.offset_days for r in event_specific if r.offset_days is not None
                }
                applicable_rules: list[ReminderRule] = list(event_specific)
                for gr in global_rules:
                    if gr.offset_days not in overridden_offsets:
                        applicable_rules.append(gr)

                # Deduplicate: if two rules produce the same fire minute, merge to one send
                seen_fire_minutes: set[tuple[int, int, int, int, int, int]] = set()

                for rule in applicable_rules:
                    if rule.offset_days is not None:
                        send_time_str = rule.send_time or user.default_notify_time
                        sh, sm = _parse_hhmm(send_time_str)
                        fire_date = occ - timedelta(days=rule.offset_days)
                        fire_local = datetime(
                            fire_date.year,
                            fire_date.month,
                            fire_date.day,
                            sh,
                            sm,
                            tzinfo=tz,
                        )
                    elif rule.offset_minutes is not None:
                        if not event.event_time:
                            continue  # only meaningful when event has a time
                        eh, em = _parse_hhmm(event.event_time)
                        event_local = datetime(occ.year, occ.month, occ.day, eh, em, tzinfo=tz)
                        fire_local = event_local - timedelta(minutes=rule.offset_minutes)
                    else:
                        continue

                    fire_utc = fire_local.astimezone(UTC)

                    if fire_utc > now_utc:
                        continue  # not yet

                    if now_utc - fire_utc > grace:
                        # Outside grace window — record as skipped
                        log = await notif_repo.create_pending(
                            user_id=user.id,
                            event_id=event.id,
                            rule_id=rule.id,
                            occurrence_date=occ,
                            scheduled_at=fire_utc,
                        )
                        if log is not None:
                            await notif_repo.mark_skipped(log.id)
                            logger.warning(
                                "reminder_skipped_grace",
                                extra={
                                    "user_id": user.id,
                                    "event_id": event.id,
                                    "fire_utc": fire_utc.isoformat(),
                                },
                            )
                        continue

                    # Deduplication: same fire minute → one send
                    fire_key = (
                        event.id,
                        fire_utc.year,
                        fire_utc.month,
                        fire_utc.day,
                        fire_utc.hour,
                        fire_utc.minute,
                    )
                    if fire_key in seen_fire_minutes:
                        continue
                    seen_fire_minutes.add(fire_key)

                    # Insert pending row BEFORE sending (idempotency)
                    log = await notif_repo.create_pending(
                        user_id=user.id,
                        event_id=event.id,
                        rule_id=rule.id,
                        occurrence_date=occ,
                        scheduled_at=fire_utc,
                    )
                    if log is None:
                        # Already sent (UNIQUE constraint fired) — skip
                        logger.debug(
                            "reminder_already_logged",
                            extra={"user_id": user.id, "event_id": event.id},
                        )
                        continue

                    send_tasks.append((user, event, rule, log.id, occ.year))

            # After processing all rules, recompute next_occurrence for events
            # where occ == today (the birthday has passed for this year)
            event_repo = EventRepository(session, user.id)
            for event in events:
                if event.next_occurrence == today_local:
                    event.next_occurrence = compute_next_occurrence(
                        event.calendar_type,
                        event.year,
                        event.month,
                        event.day,
                        today_local + timedelta(days=1),
                        adar_policy=user.adar_policy,
                        feb29_policy=user.feb29_policy,
                    )
                    await event_repo.update(event)

        # Send all queued notifications in a fresh session
        async with session_factory() as send_session:
            from app.db.models import NotificationLog as NL

            for user, event, rule, log_id, occ_year in send_tasks:
                log_obj = await send_session.get(NL, log_id)
                if log_obj is None:
                    continue

                await notify.send(
                    bot=bot,
                    session=send_session,
                    user=user,
                    event=event,
                    rule=rule,
                    log=log_obj,
                    occurrence_year=occ_year,
                )

        await _record_last_tick(session, now_utc)

        logger.info(
            "tick_done",
            extra={"sends_queued": len(send_tasks), "elapsed_ms": _elapsed_ms(now_utc)},
        )


async def _record_last_tick(session: AsyncSession, now_utc: datetime) -> None:
    """Health signal for /dbstats (SPEC.md ch.33): last successful tick_reminders run."""
    from app.db.models import AppMeta

    await session.merge(AppMeta(key="last_tick_at", value=now_utc.isoformat()))
    await session.commit()


def _elapsed_ms(start: datetime) -> int:
    return int((datetime.now(UTC) - start).total_seconds() * 1000)


# ──────────────────────────────────────────────────────────────────────────────
# Recompute next_occurrence for all active events (daily 02:00 UTC)
# ──────────────────────────────────────────────────────────────────────────────


async def recompute_occurrences(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Recalculate next_occurrence for every active event.

    Called daily at 02:00 UTC and also triggered after any event create/update.
    """
    logger.info("recompute_occurrences_start")
    async with session_factory() as session:
        # Load all users with active events
        from sqlalchemy import select

        from app.db.models import User as UserModel

        users_result = await session.execute(select(UserModel))
        users = list(users_result.scalars().all())

        updated = 0

        for user in users:
            today = datetime.now(ZoneInfo(user.timezone)).date()
            event_repo = EventRepository(session, user.id)
            events = await event_repo.list_active()
            for event in events:
                new_occ = compute_next_occurrence(
                    event.calendar_type,
                    event.year,
                    event.month,
                    event.day,
                    today,
                    adar_policy=user.adar_policy,
                    feb29_policy=user.feb29_policy,
                )
                if event.next_occurrence != new_occ:
                    event.next_occurrence = new_occ
                    await event_repo.update(event)
                    updated += 1

    logger.info("recompute_occurrences_done", extra={"updated": updated})


# ──────────────────────────────────────────────────────────────────────────────
# Daily digest (stub — full implementation in M6)
# ──────────────────────────────────────────────────────────────────────────────


async def daily_digest(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Send daily digest to users who have it enabled and whose digest_time window just opened.

    Runs every 15 minutes; sends only if digest_time is within the current 15-min window.
    Full rendering is part of M6; this stub just ensures the job slot is reserved.
    """
    logger.debug("daily_digest_tick")
    # Full implementation: M6


# ──────────────────────────────────────────────────────────────────────────────
# Auto backup (daily at AUTO_BACKUP_TIME)
# ──────────────────────────────────────────────────────────────────────────────


async def auto_backup(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Create a VACUUM INTO snapshot of the DB and clean up old backups.

    Uses VACUUM INTO which is safe during live operation (unlike file copy).
    """
    from pathlib import Path

    backup_dir = Path(settings.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(UTC).strftime("%Y%m%d")
    dest = backup_dir / f"birthly_{stamp}.db"

    logger.info("auto_backup_start", extra={"dest": str(dest)})

    async with session_factory() as session:
        # VACUUM INTO is a raw SQLite command — execute via the sync connection
        from sqlalchemy import text

        try:
            await session.execute(text(f"VACUUM INTO '{dest}'"))
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.error("auto_backup_failed", extra={"error": str(exc)}, exc_info=True)
            return

    # Prune old backups beyond retention window
    cutoff_date = (datetime.now(UTC) - timedelta(days=settings.backup_retention_days)).strftime(
        "%Y%m%d"
    )
    pruned = 0
    for old_file in backup_dir.glob("birthly_*.db"):
        stamp_part = old_file.stem.split("_")[-1]
        if stamp_part < cutoff_date:
            old_file.unlink(missing_ok=True)
            pruned += 1

    logger.info("auto_backup_done", extra={"dest": str(dest), "pruned": pruned})


# ──────────────────────────────────────────────────────────────────────────────
# Purge soft-deleted events (daily 04:00 UTC)
# ──────────────────────────────────────────────────────────────────────────────


async def purge_soft_deleted(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Hard-delete events with deleted_at older than SOFT_DELETE_RETENTION_DAYS."""
    from sqlalchemy import select

    from app.constants import SOFT_DELETE_RETENTION_DAYS
    from app.db.models import User as UserModel

    cutoff = datetime.now(UTC) - timedelta(days=SOFT_DELETE_RETENTION_DAYS)
    logger.info("purge_soft_deleted_start", extra={"cutoff": cutoff.isoformat()})

    total_purged = 0
    async with session_factory() as session:
        users_result = await session.execute(select(UserModel.id))
        user_ids = [row[0] for row in users_result.all()]
        for uid in user_ids:
            repo = EventRepository(session, uid)
            count = await repo.purge_deleted_before(cutoff)
            total_purged += count

    logger.info("purge_soft_deleted_done", extra={"purged": total_purged})


# ──────────────────────────────────────────────────────────────────────────────
# Log cleanup (weekly)
# ──────────────────────────────────────────────────────────────────────────────


async def cleanup_logs(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Delete old audit_logs (>90d) and notifications_log (>180d)."""
    now = datetime.now(UTC)
    audit_cutoff = now - timedelta(days=90)
    notif_cutoff = now - timedelta(days=180)

    async with session_factory() as session:
        notif_repo = NotificationRepository(session)
        deleted_audit = await notif_repo.delete_old_audit_logs(audit_cutoff)
        deleted_notif = await notif_repo.delete_old_logs(notif_cutoff)

    logger.info(
        "cleanup_logs_done",
        extra={"audit_deleted": deleted_audit, "notif_deleted": deleted_notif},
    )
