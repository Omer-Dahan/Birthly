"""Input validation and the free-text date parser. Pure functions only.

See SPEC.md chapters 9, 15 (S2/S3), and 27.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from app.constants import (
    MAX_YEAR_GREGORIAN,
    MAX_YEAR_HEBREW,
    MIN_YEAR_GREGORIAN,
    MIN_YEAR_HEBREW,
    NAME_MAX_LEN,
    NICKNAME_MAX_LEN,
    NOTES_MAX_LEN,
    PHONE_MAX_LEN,
    RELATION_MAX_LEN,
)
from app.core.hebcal import to_hebrew


class ValidationError(Exception):
    """Raised with a ready-to-display, user-friendly Hebrew message."""


@dataclass(frozen=True)
class ParsedDate:
    day: int
    month: int
    year: int | None


_HEBREW_MONTH_ALIASES = {
    "ינואר": 1,
    "פברואר": 2,
    "מרץ": 3,
    "אפריל": 4,
    "מאי": 5,
    "יוני": 6,
    "יולי": 7,
    "אוגוסט": 8,
    "ספטמבר": 9,
    "אוקטובר": 10,
    "נובמבר": 11,
    "דצמבר": 12,
}

_ENGLISH_MONTH_ALIASES = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_MONTH_DAYS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def month_number_from_name(text: str) -> int | None:
    """Resolve a Hebrew or English month name/abbreviation to 1-12, or None."""
    cleaned = text.strip().lower()
    if not cleaned:
        return None
    month = _HEBREW_MONTH_ALIASES.get(text.strip())
    if month is not None:
        return month
    return _ENGLISH_MONTH_ALIASES.get(cleaned)


_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _is_valid_day_month(day: int, month: int) -> bool:
    if not (1 <= month <= 12):
        return False
    return 1 <= day <= _MONTH_DAYS[month - 1]


def _normalize_two_digit_year(yy: int) -> int:
    current_yy = date.today().year % 100
    return 2000 + yy if yy <= current_yy else 1900 + yy


def parse_gregorian(text: str) -> ParsedDate:
    """Parse free-text Gregorian date input per SPEC.md 15/S3's fallback order.

    Raises ValidationError with a friendly Hebrew message if nothing matches.
    """
    raw = text.strip()

    # 1. DD/MM/YYYY, DD.MM.YYYY, DD-MM-YYYY
    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", raw)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _is_valid_day_month(day, month) and MIN_YEAR_GREGORIAN <= year <= MAX_YEAR_GREGORIAN:
            return ParsedDate(day, month, year)
        raise ValidationError("❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990")

    # 2. DD/MM/YY (two-digit year)
    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2})", raw)
    if m:
        day, month, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _is_valid_day_month(day, month):
            return ParsedDate(day, month, _normalize_two_digit_year(yy))
        raise ValidationError("❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990")

    # 5. YYYY-MM-DD (ISO) — checked before the bare DD/MM fallback since it
    #    also uses a separator-delimited numeric form.
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _is_valid_day_month(day, month) and MIN_YEAR_GREGORIAN <= year <= MAX_YEAR_GREGORIAN:
            return ParsedDate(day, month, year)
        raise ValidationError("❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990")

    # 3. DD/MM or DD.MM — no year
    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})", raw)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        if _is_valid_day_month(day, month):
            return ParsedDate(day, month, None)
        raise ValidationError("❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990")

    # 4. "<day> ב<Hebrew month>" / "<day> <English month name>"
    m = re.fullmatch(r"(\d{1,2})\s+ב?([א-ת]+)", raw)
    if m:
        day = int(m.group(1))
        hebrew_month = _HEBREW_MONTH_ALIASES.get(m.group(2))
        if hebrew_month is not None and _is_valid_day_month(day, hebrew_month):
            return ParsedDate(day, hebrew_month, None)
        raise ValidationError("❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990")

    m = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)", raw)
    if m:
        day = int(m.group(1))
        english_month = _ENGLISH_MONTH_ALIASES.get(m.group(2).lower())
        if english_month is not None and _is_valid_day_month(day, english_month):
            return ParsedDate(day, english_month, None)
        raise ValidationError("❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990")

    raise ValidationError("❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990")


def _strip_control_chars(value: str) -> str:
    return _CONTROL_CHAR_RE.sub("", value)


def validate_name(value: str) -> str:
    """1-64 chars, control characters stripped, not empty/whitespace-only."""
    cleaned = _strip_control_chars(value).strip()
    if not cleaned or cleaned.isspace():
        raise ValidationError("מה השם? 🙂")
    if len(cleaned) > NAME_MAX_LEN:
        raise ValidationError(f"זה ארוך מדי — עד {NAME_MAX_LEN} תווים.")
    return cleaned


def _validate_optional_text(value: str, max_len: int) -> str:
    cleaned = _strip_control_chars(value).strip()
    if len(cleaned) > max_len:
        raise ValidationError(f"זה ארוך מדי — עד {max_len} תווים.")
    return cleaned


def validate_nickname(value: str) -> str:
    return _validate_optional_text(value, NICKNAME_MAX_LEN)


def validate_notes(value: str) -> str:
    return _validate_optional_text(value, NOTES_MAX_LEN)


def validate_relation(value: str) -> str:
    return _validate_optional_text(value, RELATION_MAX_LEN)


def validate_phone(value: str) -> str:
    """Accepts E.164 or Israeli local format; strips separators, checks length."""
    cleaned = _strip_control_chars(value).strip()
    if len(cleaned) > PHONE_MAX_LEN:
        raise ValidationError(f"זה ארוך מדי — עד {PHONE_MAX_LEN} תווים.")
    digits_and_plus = re.sub(r"[\s\-().]", "", cleaned)
    if not re.fullmatch(r"\+?\d{7,15}", digits_and_plus):
        raise ValidationError("❌ מספר הטלפון לא תקין.")
    return digits_and_plus


def validate_year(year: int, *, hebrew: bool = False) -> int:
    if hebrew:
        if not (MIN_YEAR_HEBREW <= year <= MAX_YEAR_HEBREW):
            raise ValidationError("❌ שנה לא תקינה.")
        return year
    if not (MIN_YEAR_GREGORIAN <= year <= MAX_YEAR_GREGORIAN):
        raise ValidationError("❌ שנה לא תקינה.")
    return year


def parse_hebrew_year_input(raw: str) -> int:
    """Parse a year typed during Hebrew-date entry, accepting either a Hebrew
    year (e.g. 5750) or a Gregorian year (e.g. 1990), auto-detecting by range.
    """
    cleaned = _strip_control_chars(raw).strip()
    if not cleaned.isdigit():
        raise ValidationError("❌ שנה לא תקינה.")

    year = int(cleaned)
    if MIN_YEAR_HEBREW <= year <= MAX_YEAR_HEBREW:
        return year
    if MIN_YEAR_GREGORIAN <= year <= MAX_YEAR_GREGORIAN:
        return to_hebrew(date(year, 1, 1))[0]
    raise ValidationError("❌ שנה לא תקינה.")


def contains_only_symbols(value: str) -> bool:
    """True if ``value`` has no letters or digits (e.g. only emoji/punctuation/whitespace)."""
    return not any(unicodedata.category(ch)[0] in ("L", "N") for ch in value)


__all__ = [
    "ParsedDate",
    "ValidationError",
    "contains_only_symbols",
    "month_number_from_name",
    "parse_gregorian",
    "parse_hebrew_year_input",
    "validate_name",
    "validate_nickname",
    "validate_notes",
    "validate_phone",
    "validate_relation",
    "validate_year",
]
