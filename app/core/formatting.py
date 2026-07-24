"""Display formatting: dates, countdowns, ages, phones, names, and RTL/LTR wrapping.

Pure functions only. See SPEC.md chapters 9, 19, and 30.
"""

from __future__ import annotations

from datetime import date

from app.core.text import pluralize_hebrew

RLM = "‏"
LRM = "‎"

_DATE_FORMATTERS: dict[str, str] = {
    "DD/MM/YYYY": "{d:02d}/{m:02d}/{y:04d}",
    "DD.MM.YYYY": "{d:02d}.{m:02d}.{y:04d}",
    "YYYY-MM-DD": "{y:04d}-{m:02d}-{d:02d}",
}


def format_date(d: date, date_format: str) -> str:
    """Render ``d`` per the user's chosen ``date_format`` setting."""
    template = _DATE_FORMATTERS.get(date_format, _DATE_FORMATTERS["DD/MM/YYYY"])
    return template.format(d=d.day, m=d.month, y=d.year)


def format_time(hour: int, minute: int, time_format: str) -> str:
    """Render a time of day as ``HH:MM`` (24h) or ``H:MM AM/PM`` (12h)."""
    if time_format == "12h":
        period = "AM" if hour < 12 else "PM"
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"
    return f"{hour:02d}:{minute:02d}"


def format_countdown(days: int) -> str:
    """Render a countdown in Hebrew: 'היום' / 'מחר' / 'עוד יומיים' / 'עוד 5 ימים' / ..."""
    if days == 0:
        return "היום"
    if days == 1:
        return "מחר"
    if days < 7:
        return f"עוד {pluralize_hebrew(days, 'day')}"
    if days < 14:
        return "עוד שבוע"
    if days < 30:
        weeks = days // 7
        return f"עוד {pluralize_hebrew(weeks, 'week')}"
    if days < 60:
        return "עוד חודש"
    if days < 90:
        return "עוד חודשיים"
    months = days // 30
    return f"עוד {pluralize_hebrew(months, 'month')}"


def format_phone(phone: str) -> str:
    """Convert an E.164 or raw Israeli phone number into '050-1234567' display form."""
    digits = "".join(c for c in phone if c.isdigit())

    if digits.startswith("972"):
        digits = "0" + digits[3:]
    elif not digits.startswith("0"):
        digits = "0" + digits

    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:]}"
    if len(digits) == 9:
        return f"{digits[:2]}-{digits[2:]}"
    return digits


def format_name(first_name: str, last_name: str | None) -> str:
    """Join first and last name, omitting a missing last name cleanly."""
    if last_name:
        return f"{first_name} {last_name}"
    return first_name


def rtl(text: str) -> str:
    """Wrap ``text`` with a leading RLM to prevent bidi reordering in RTL context."""
    return f"{RLM}{text}"


def ltr(text: str) -> str:
    """Wrap ``text`` with LRM on both sides, for phones/usernames/Latin dates inside RTL text."""
    return f"{LRM}{text}{LRM}"


__all__ = [
    "format_countdown",
    "format_date",
    "format_name",
    "format_phone",
    "format_time",
    "ltr",
    "rtl",
]
