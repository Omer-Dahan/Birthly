"""Text utilities: HTML escaping and Hebrew pluralization. Pure functions only."""

from __future__ import annotations

import html

_DUAL_FORMS = {
    "day": "יומיים",
    "year": "שנתיים",
    "week": "שבועיים",
    "month": "חודשיים",
    "person": "שני אנשים",
}

_SINGULAR_FORMS = {
    "day": "יום",
    "year": "שנה",
    "week": "שבוע",
    "month": "חודש",
    "person": "אדם",
}

_PLURAL_FORMS = {
    "day": "ימים",
    "year": "שנים",
    "week": "שבועות",
    "month": "חודשים",
    "person": "אנשים",
}


def esc(value: str | None) -> str:
    """HTML-escape user-supplied text before embedding in an HTML-parse-mode message."""
    if value is None:
        return ""
    return html.escape(value, quote=False)


def pluralize_hebrew(count: int, unit: str) -> str:
    """Render ``count`` of ``unit`` ("day", "year", "week", "person") in Hebrew.

    Handles the dual form (2 -> "יומיים" not "2 ימים") and the standard
    singular ("1 יום") / plural ("5 ימים") forms.
    """
    if unit not in _SINGULAR_FORMS:
        raise ValueError(f"unknown unit: {unit}")

    if count == 1:
        return f"1 {_SINGULAR_FORMS[unit]}"
    if count == 2:
        return _DUAL_FORMS[unit]
    return f"{count} {_PLURAL_FORMS[unit]}"


def truncate(value: str, max_len: int, suffix: str = "…") -> str:
    """Shorten ``value`` to at most ``max_len`` characters, appending ``suffix`` if cut."""
    if len(value) <= max_len:
        return value
    if max_len <= len(suffix):
        return suffix[:max_len]
    return value[: max_len - len(suffix)] + suffix


def split_name(full_name: str) -> tuple[str, str | None]:
    """Split "Dana Cohen" into ("Dana", "Cohen") on the first space.

    A name with no space becomes (name, None) — no last name.
    """
    parts = full_name.split(" ", 1)
    if len(parts) == 1:
        return parts[0], None
    first, rest = parts
    rest = rest.strip()
    return first, rest or None
