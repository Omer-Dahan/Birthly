from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event, NotificationLog, ReminderRule, User


class NotificationRepository:
    """All DB access for notifications_log.

    Unlike BaseRepository this is NOT scoped to a single user_id because the
    scheduler tick processes all users in one session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists(
        self,
        event_id: int,
        rule_id: int | None,
        occurrence_date: date,
    ) -> bool:
        """Return True if a log row already exists for this (event, rule, date) triple."""
        stmt = select(NotificationLog.id).where(
            NotificationLog.event_id == event_id,
            NotificationLog.rule_id == rule_id,
            NotificationLog.occurrence_date == occurrence_date,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_pending(
        self,
        *,
        user_id: int,
        event_id: int,
        rule_id: int | None,
        occurrence_date: date,
        scheduled_at: datetime,
    ) -> NotificationLog | None:
        """INSERT a pending row *before* sending.

        Returns the new row, or None if the UNIQUE constraint fires (duplicate).
        Callers must treat None as "already handled — skip".
        """
        log = NotificationLog(
            user_id=user_id,
            event_id=event_id,
            rule_id=rule_id,
            occurrence_date=occurrence_date,
            scheduled_at=scheduled_at,
            status="pending",
        )
        try:
            # A SAVEPOINT confines rollback-on-duplicate to just this insert —
            # a plain session.rollback() would expire every object already
            # loaded in the tick's outer loop (users, events), and the next
            # attribute access on them then tries a lazy-load outside of an
            # awaited context, raising MissingGreenlet.
            async with self.session.begin_nested():
                self.session.add(log)
                await self.session.flush()
            return log
        except IntegrityError:
            return None

    async def mark_sent(self, log_id: int) -> None:
        """Update status → 'sent' and record sent_at."""
        log = await self.session.get(NotificationLog, log_id)
        if log is not None:
            log.status = "sent"
            log.sent_at = datetime.now(UTC)
            log.attempts += 1
            await self.session.commit()

    async def mark_failed(self, log_id: int, error: str) -> None:
        """Update status → 'failed' and store error text."""
        log = await self.session.get(NotificationLog, log_id)
        if log is not None:
            log.status = "failed"
            log.error = error[:500]
            log.attempts += 1
            await self.session.commit()

    async def mark_skipped(self, log_id: int) -> None:
        """Update status → 'skipped' (outside grace window)."""
        log = await self.session.get(NotificationLog, log_id)
        if log is not None:
            log.status = "skipped"
            log.attempts += 1
            await self.session.commit()

    async def list_active_users_with_events(
        self,
        window_start: date,
        window_end: date,
    ) -> list[User]:
        """Return distinct User objects whose active events fall in [window_start, window_end].

        Only users with notifications_enabled=True, is_blocked=False, bot_blocked_by_user=False.
        Uses a JOIN so we only load users that actually have work to do this tick.
        """
        stmt = (
            select(User)
            .join(Event, Event.user_id == User.id)
            .where(
                User.notifications_enabled.is_(True),
                User.is_blocked.is_(False),
                User.bot_blocked_by_user.is_(False),
                Event.deleted_at.is_(None),
                Event.is_active.is_(True),
                Event.next_occurrence.is_not(None),
                Event.next_occurrence >= window_start,
                Event.next_occurrence <= window_end,
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_events_for_user(
        self,
        user_id: int,
        window_start: date,
        window_end: date,
    ) -> list[Event]:
        """Active events for a specific user in the occurrence window."""
        stmt = select(Event).where(
            Event.user_id == user_id,
            Event.deleted_at.is_(None),
            Event.is_active.is_(True),
            Event.next_occurrence.is_not(None),
            Event.next_occurrence >= window_start,
            Event.next_occurrence <= window_end,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_rules_for_user(self, user_id: int) -> list[ReminderRule]:
        """All enabled rules (global + per-event) for the user."""
        stmt = select(ReminderRule).where(
            ReminderRule.user_id == user_id,
            ReminderRule.enabled.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_old_logs(self, cutoff: datetime) -> int:
        """Hard-delete notification logs older than cutoff. Returns count deleted."""
        stmt = select(NotificationLog).where(NotificationLog.scheduled_at < cutoff)
        result = await self.session.execute(stmt)
        logs = list(result.scalars().all())
        for log in logs:
            await self.session.delete(log)
        await self.session.commit()
        return len(logs)

    async def get_pending_logs_before(self, cutoff: datetime) -> list[NotificationLog]:
        """Pending logs whose scheduled_at is in the past (for recovery on restart)."""
        stmt = select(NotificationLog).where(
            NotificationLog.status == "pending",
            NotificationLog.scheduled_at <= cutoff,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_old_audit_logs(self, cutoff: datetime) -> int:
        """Alias used by cleanup_logs job — delegated here to keep jobs thin."""
        from app.db.models import AuditLog

        stmt = select(AuditLog).where(AuditLog.created_at < cutoff)
        result = await self.session.execute(stmt)
        logs = list(result.scalars().all())
        for log in logs:
            await self.session.delete(log)
        await self.session.commit()
        return len(logs)
