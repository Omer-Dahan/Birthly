"""SPEC.md chapter 11.1: only first_name + (month + day) are required.

Verifies that an event with nothing else set flows through core date/age/
formatting logic and the DB layer without error or a silently-required
field. The handler/service/reminder-engine legs of this contract are
exercised again in later milestones once those layers exist.
"""

from __future__ import annotations

from datetime import date

from app.core.dates import age_at, next_occurrence
from app.core.formatting import format_countdown, format_date, format_name
from app.core.validators import validate_name
from app.db.models import Event


async def test_minimal_event_survives_core_pipeline() -> None:
    name = validate_name("Dana")
    today = date(2026, 1, 1)

    occurrence = next_occurrence("gregorian", None, 3, 15, today)
    age = age_at("gregorian", None, 3, 15, occurrence)
    countdown = format_countdown((occurrence - today).days)
    display_date = format_date(occurrence, "DD/MM/YYYY")
    display_name = format_name(name, None)

    assert age is None
    assert countdown
    assert display_date == "15/03/2026"
    assert display_name == "Dana"


async def test_minimal_event_persists_with_only_required_fields(db_session, user) -> None:
    event = Event(user_id=user.id, first_name="Dana", month=3, day=15)
    db_session.add(event)
    await db_session.commit()

    assert event.id is not None
    assert event.year is None
    assert event.last_name is None
    assert event.nickname is None
    assert event.gender is None
    assert event.relation is None
    assert event.phone is None
    assert event.notes is None
    assert event.photo_file_id is None
    assert event.event_time is None
    # Fields with sane silent defaults, never surfaced as "missing":
    assert event.event_type == "birthday"
    assert event.calendar_type == "gregorian"
    assert event.category == "other"
    assert event.is_active is True
