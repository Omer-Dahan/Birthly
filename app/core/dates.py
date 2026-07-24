"""Occurrence and age calculations for both calendars.

Pure functions only: no DB, no I/O, no aiogram. See SPEC.md chapter 9.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from app.core import hebcal

if TYPE_CHECKING:
    from app.db.models import Event


def _next_gregorian_occurrence(
    month: int, day: int, today: date, feb29_policy: str
) -> date:
    resolved_month, resolved_day = month, day
    if month == 2 and day == 29:
        try:
            date(today.year, 2, 29)
        except ValueError:
            resolved_month, resolved_day = (2, 28) if feb29_policy == "feb28" else (3, 1)

    try:
        candidate = date(today.year, resolved_month, resolved_day)
    except ValueError:
        candidate = date(today.year, resolved_month, resolved_day - 1)

    if candidate >= today:
        return candidate

    next_year = today.year + 1
    target_month, target_day = month, day
    if month == 2 and day == 29:
        try:
            date(next_year, 2, 29)
        except ValueError:
            target_month, target_day = (2, 28) if feb29_policy == "feb28" else (3, 1)

    try:
        return date(next_year, target_month, target_day)
    except ValueError:
        return date(next_year, target_month, target_day - 1)


def _next_hebrew_occurrence(
    h_month: int, h_day: int, today: date, adar_policy: str
) -> date:
    h_year_today, _, _ = hebcal.to_hebrew(today)

    for h_year in (h_year_today, h_year_today + 1):
        resolved_month = hebcal.resolve_month(h_year, h_month, adar_policy)
        candidate = hebcal.to_gregorian(h_year, resolved_month, h_day)
        if candidate >= today:
            return candidate

    raise AssertionError(  # pragma: no cover
        "unreachable: next Hebrew occurrence not found within one year"
    )


def next_occurrence(
    calendar_type: str,
    year: int | None,
    month: int,
    day: int,
    today: date,
    adar_policy: str = "adar_ii",
    feb29_policy: str = "feb28",
) -> date:
    """The next Gregorian date this recurring event falls on, on or after ``today``."""
    if calendar_type == "hebrew":
        return _next_hebrew_occurrence(month, day, today, adar_policy)
    return _next_gregorian_occurrence(month, day, today, feb29_policy)


def days_until(target: date, today: date) -> int:
    """Number of days from ``today`` to ``target`` (0 if today, negative if past)."""
    return (target - today).days


def age_at(
    calendar_type: str, year: int | None, month: int, day: int, on: date
) -> int | None:
    """Age reached on occurrence date ``on``. ``None`` if birth year is unknown."""
    if year is None:
        return None

    if calendar_type == "hebrew":
        occurrence_h_year, _, _ = hebcal.to_hebrew(on)
        return occurrence_h_year - year

    return on.year - year


def upcoming_between(
    events: list[Event], start: date, end: date
) -> list[tuple[Event, date]]:
    """Events (with their occurrence date) whose ``next_occurrence`` falls in [start, end]."""
    result = []
    for event in events:
        occ = event.next_occurrence
        if occ is not None and start <= occ <= end:
            result.append((event, occ))
    result.sort(key=lambda pair: pair[1])
    return result


__all__ = ["age_at", "days_until", "next_occurrence", "upcoming_between"]
