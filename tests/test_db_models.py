from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import Event, NotificationLog, ReminderRule, User


async def test_user_created_with_defaults(db_session, user: User) -> None:
    assert user.language == "he"
    assert user.timezone == "Asia/Jerusalem"
    assert user.notifications_enabled is True


async def test_event_minimal_fields_only(db_session, user: User) -> None:
    """The simplicity contract (SPEC 11.1): only first_name + month + day are required."""
    event = Event(user_id=user.id, first_name="Dana", month=3, day=15)
    db_session.add(event)
    await db_session.commit()

    result = await db_session.execute(select(Event).where(Event.user_id == user.id))
    saved = result.scalar_one()
    assert saved.first_name == "Dana"
    assert saved.year is None
    assert saved.event_type == "birthday"
    assert saved.calendar_type == "gregorian"


async def test_cascade_delete_removes_events_and_rules(db_session, user: User) -> None:
    event = Event(user_id=user.id, first_name="Dana", month=3, day=15)
    db_session.add(event)
    await db_session.commit()

    rule = ReminderRule(user_id=user.id, event_id=event.id, offset_days=1)
    db_session.add(rule)
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    events = (await db_session.execute(select(Event))).scalars().all()
    rules = (await db_session.execute(select(ReminderRule))).scalars().all()
    assert events == []
    assert rules == []


async def test_reminder_rule_requires_exactly_one_offset(db_session, user: User) -> None:
    user_id = user.id

    both_set = ReminderRule(user_id=user_id, offset_days=1, offset_minutes=30)
    db_session.add(both_set)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    neither_set = ReminderRule(user_id=user_id)
    db_session.add(neither_set)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_notification_log_unique_prevents_duplicate(db_session, user: User) -> None:
    event = Event(user_id=user.id, first_name="Dana", month=3, day=15)
    db_session.add(event)
    await db_session.commit()

    rule = ReminderRule(user_id=user.id, event_id=event.id, offset_days=1)
    db_session.add(rule)
    await db_session.commit()

    occ = date(2026, 3, 15)
    log1 = NotificationLog(
        user_id=user.id,
        event_id=event.id,
        rule_id=rule.id,
        occurrence_date=occ,
        scheduled_at=datetime(2026, 3, 14, 9, 0),
        status="pending",
    )
    db_session.add(log1)
    await db_session.commit()

    log2 = NotificationLog(
        user_id=user.id,
        event_id=event.id,
        rule_id=rule.id,
        occurrence_date=occ,
        scheduled_at=datetime(2026, 3, 14, 9, 0),
        status="pending",
    )
    db_session.add(log2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
