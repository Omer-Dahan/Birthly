from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dates import next_occurrence
from app.db.models import Event, User
from app.db.repositories.events import EventRepository
from app.services.clock import user_today
from app.services.exceptions import LimitError, NotFoundError


@dataclass(frozen=True)
class NewEventInput:
    first_name: str
    last_name: str | None
    month: int
    day: int
    year: int | None
    calendar_type: str = "gregorian"


async def create_minimal_event(
    session: AsyncSession, user: User, data: NewEventInput
) -> Event:
    """Create an event with only the fields the simplicity contract requires.

    Everything else (category, type, phone, ...) keeps its column default
    and can be filled in later via "עוד פרטים" — never required up front.
    """
    repo = EventRepository(session, user.id)
    count = await repo.count_not_deleted()
    if count >= settings.max_events_per_user:
        raise LimitError(f"reached the {settings.max_events_per_user}-event limit")

    event = Event(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        month=data.month,
        day=data.day,
        year=data.year,
        calendar_type=data.calendar_type,
    )
    _recompute_occurrence(event, user)
    return await repo.create(event)


async def get_owned_event(session: AsyncSession, user: User, event_id: int) -> Event:
    repo = EventRepository(session, user.id)
    event = await repo.get_owned(event_id)
    if event is None or event.deleted_at is not None:
        raise NotFoundError(f"event {event_id} not found for user {user.id}")
    return event


async def update_event_field(
    session: AsyncSession, user: User, event_id: int, **fields: object
) -> Event:
    """Apply field updates to an owned event and persist. Recomputes occurrence
    if any date-affecting field changed.
    """
    event = await get_owned_event(session, user, event_id)
    repo = EventRepository(session, user.id)

    date_fields = {"month", "day", "year", "calendar_type"}
    changed_date = any(key in date_fields for key in fields)

    for key, value in fields.items():
        setattr(event, key, value)

    if changed_date:
        _recompute_occurrence(event, user)

    return await repo.update(event)


async def delete_event(session: AsyncSession, user: User, event_id: int) -> Event:
    """Soft-delete (30-day trash, SPEC.md chapter 20)."""
    event = await get_owned_event(session, user, event_id)
    repo = EventRepository(session, user.id)
    await repo.soft_delete(event)
    return event


async def restore_event(session: AsyncSession, user: User, event_id: int) -> Event:
    repo = EventRepository(session, user.id)
    event = await repo.get_owned(event_id)
    if event is None:
        raise NotFoundError(f"event {event_id} not found for user {user.id}")
    await repo.restore(event)
    return event


async def toggle_mute(session: AsyncSession, user: User, event_id: int) -> Event:
    event = await get_owned_event(session, user, event_id)
    repo = EventRepository(session, user.id)
    event.is_active = not event.is_active
    return await repo.update(event)


def _recompute_occurrence(event: Event, user: User) -> None:
    event.next_occurrence = next_occurrence(
        event.calendar_type,
        event.year,
        event.month,
        event.day,
        user_today(user),
        adar_policy=user.adar_policy,
        feb29_policy=user.feb29_policy,
    )
