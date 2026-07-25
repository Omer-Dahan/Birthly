from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import days_until
from app.db.models import Event, User
from app.db.repositories.events import EventRepository
from app.services.clock import user_today


@dataclass(frozen=True)
class HomeSummary:
    today_count: int
    week_count: int
    nearest_event: Event | None
    nearest_days_until: int | None


async def get_home_summary(session: AsyncSession, user: User) -> HomeSummary:
    """Live counts for the S1 home screen banner: today, this week, and the nearest event."""
    repo = EventRepository(session, user.id)
    today = user_today(user)
    week_end = today + timedelta(days=7)

    upcoming = await repo.upcoming_between(today, week_end)

    today_count = sum(1 for e in upcoming if e.next_occurrence == today)
    week_count = len(upcoming)

    nearest_event = upcoming[0] if upcoming else None
    nearest_days: int | None = None
    if nearest_event is not None:
        assert nearest_event.next_occurrence is not None  # guaranteed by upcoming_between query
        nearest_days = days_until(nearest_event.next_occurrence, today)

    return HomeSummary(
        today_count=today_count,
        week_count=week_count,
        nearest_event=nearest_event,
        nearest_days_until=nearest_days,
    )
