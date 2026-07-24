"""Hebrew calendar support: conversions, edge cases, and gematria formatting.

Wraps pyluach for the Gregorian <-> Hebrew conversions and month-length
queries, and implements the "clamp to last existing day, never roll into
the next month" rule from SPEC.md chapter 10 for dates that do not exist
in the target Hebrew year (e.g. the 30th of a 29-day Cheshvan).
"""

from __future__ import annotations

from datetime import date

from pyluach import hebrewcal
from pyluach.dates import HebrewDate

from app.constants import HEBREW_MONTH_NAMES

_GEMATRIA_ONES = {1: "א", 2: "ב", 3: "ג", 4: "ד", 5: "ה", 6: "ו", 7: "ז", 8: "ח", 9: "ט"}
_GEMATRIA_TENS = {10: "י", 20: "כ", 30: "ל", 40: "מ", 50: "נ", 60: "ס", 70: "ע", 80: "פ", 90: "צ"}
_GEMATRIA_HUNDREDS = {100: "ק", 200: "ר", 300: "ש", 400: "ת"}


def is_leap_year(h_year: int) -> bool:
    """True if ``h_year`` (Hebrew year) has 13 months (Adar I + Adar II)."""
    return hebrewcal.Year(h_year).leap


def month_length(h_year: int, h_month: int) -> int:
    """Number of days in ``h_month`` of ``h_year``.

    ``h_month`` uses the SPEC.md numbering: 1=Nisan .. 6=Elul, 7=Tishrei ..
    11=Shevat, 12=Adar (or Adar I in a leap year), 13=Adar II (leap only).
    """
    for month in hebrewcal.Year(h_year).itermonths():
        if month.month == h_month:
            return len(month)
    raise ValueError(f"month {h_month} does not exist in Hebrew year {h_year}")


def resolve_month(h_year: int, src_month: int, policy: str) -> int:
    """Resolve a month number recorded against one leap-status into the
    equivalent month for ``h_year``, applying the Adar policy.

    - Plain months (1-11) pass through unchanged.
    - ``src_month == 12`` (Adar, or Adar I) in a target leap year resolves to
      13 (Adar II) if ``policy == "adar_ii"``, else stays at 12 (Adar I).
    - ``src_month == 13`` (Adar II) in a target non-leap year resolves to 12
      (the single Adar).
    """
    target_is_leap = is_leap_year(h_year)

    if src_month not in (12, 13):
        return src_month

    if target_is_leap:
        if src_month == 13:
            return 13
        return 13 if policy == "adar_ii" else 12

    return 12


def to_gregorian(h_year: int, h_month: int, h_day: int) -> date:
    """Convert a Hebrew date to its Gregorian equivalent.

    If ``h_day`` does not exist in ``h_month`` of ``h_year`` (e.g. the 30th
    of a 29-day month), clamps to the last existing day of that month.
    Never rolls over into the next month.
    """
    max_day = month_length(h_year, h_month)
    day = min(h_day, max_day)
    return HebrewDate(h_year, h_month, day).to_pydate()


def to_hebrew(d: date) -> tuple[int, int, int]:
    """Convert a Gregorian date to (hebrew_year, hebrew_month, hebrew_day)."""
    h = HebrewDate.from_pydate(d)
    return h.year, h.month, h.day


def hebrew_year_gematria(y: int) -> str:
    """Render a Hebrew year as gematria, e.g. 5786 -> 'תשפ״ו'.

    Drops the leading thousands digit (5), per convention (5786 -> 786).
    """
    return gematria(y % 1000)


def gematria(num: int) -> str:
    """Render an integer (1-999) as a Hebrew gematria string with gershayim.

    Applies the traditional exception: 15 -> ט״ו and 16 -> ט״ז instead of
    the letter combinations that would spell divine names (י״ה / י״ו).
    """
    if num <= 0:
        return ""

    hundreds, remainder = divmod(num, 100)
    tens, ones = divmod(remainder, 10)

    letters = ""
    while hundreds > 0:
        chunk = min(hundreds, 4) * 100
        letters += _GEMATRIA_HUNDREDS[chunk]
        hundreds -= chunk // 100

    if remainder == 15:
        letters += "טו"
    elif remainder == 16:
        letters += "טז"
    else:
        if tens > 0:
            letters += _GEMATRIA_TENS[tens * 10]
        if ones > 0:
            letters += _GEMATRIA_ONES[ones]

    if len(letters) == 1:
        return f"{letters}׳"
    return f"{letters[:-1]}״{letters[-1]}"


def hebrew_month_name(h_month: int) -> str:
    """Hebrew name for a SPEC-numbered month (1-13)."""
    return HEBREW_MONTH_NAMES[h_month - 1]


def format_hebrew_date(h_year: int, h_month: int, h_day: int, with_year: bool = True) -> str:
    """Format a Hebrew date as e.g. 'י״ד בניסן תשפ״ו' (day, month, optional year)."""
    day_str = gematria(h_day)
    month_name = hebrew_month_name(h_month)
    result = f"{day_str} ב{month_name}"
    if with_year:
        result += f" {hebrew_year_gematria(h_year)}"
    return result
