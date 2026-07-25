from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import age_at, days_until
from app.db.models import Event, User
from app.db.repositories.events import EventRepository
from app.services.clock import user_today


@dataclass(frozen=True)
class UserStats:
    total: int
    today: int
    this_week: int
    this_month: int
    next_30_days: int
    nearest: Event | None
    nearest_days_until: int | None
    by_category: dict[str, int]
    by_type: dict[str, int]
    by_month: dict[int, int]
    youngest: tuple[Event, int] | None
    oldest: tuple[Event, int] | None
    avg_age: float | None
    without_year: int
    muted: int


async def get_user_stats(session: AsyncSession, user: User) -> UserStats:
    """SPEC.md ch.21: aggregate stats for the S13 screen.

    Loads every non-deleted event once and computes all fields client-side —
    fine at this scale (max_events_per_user caps well under a page-fault
    concern), and keeps the whole calculation in one readable pass.
    """
    repo = EventRepository(session, user.id)
    events = await repo.list_not_deleted()
    today = user_today(user)

    week_end = today + timedelta(days=7)
    month_end = today + timedelta(days=30)
    next_30_end = today + timedelta(days=30)

    today_count = 0
    week_count = 0
    month_count = 0
    next_30_count = 0
    by_category: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_month: dict[int, int] = {}
    without_year = 0
    muted = 0

    nearest: Event | None = None
    nearest_days: int | None = None

    ages: list[tuple[Event, int]] = []

    for event in events:
        occ = event.next_occurrence
        if occ is not None:
            if occ == today:
                today_count += 1
            if today <= occ <= week_end:
                week_count += 1
            if today <= occ <= month_end:
                month_count += 1
            if today <= occ <= next_30_end:
                next_30_count += 1

            if nearest is None or occ < nearest.next_occurrence:  # type: ignore[operator]
                nearest = event
                nearest_days = days_until(occ, today)

            by_month[occ.month] = by_month.get(occ.month, 0) + 1

        by_category[event.category] = by_category.get(event.category, 0) + 1
        by_type[event.event_type] = by_type.get(event.event_type, 0) + 1

        if event.year is None:
            without_year += 1
        if not event.is_active:
            muted += 1

        if event.year is not None and occ is not None:
            age = age_at(event.calendar_type, event.year, event.month, event.day, occ)
            if age is not None:
                ages.append((event, age))

    youngest = min(ages, key=lambda pair: pair[1]) if ages else None
    oldest = max(ages, key=lambda pair: pair[1]) if ages else None
    avg_age = sum(age for _, age in ages) / len(ages) if ages else None

    return UserStats(
        total=len(events),
        today=today_count,
        this_week=week_count,
        this_month=month_count,
        next_30_days=next_30_count,
        nearest=nearest,
        nearest_days_until=nearest_days,
        by_category=by_category,
        by_type=by_type,
        by_month=by_month,
        youngest=youngest,
        oldest=oldest,
        avg_age=avg_age,
        without_year=without_year,
        muted=muted,
    )
