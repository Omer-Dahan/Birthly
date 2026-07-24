from __future__ import annotations

from datetime import date

import pytest

from app.core.formatting import (
    LRM,
    RLM,
    format_countdown,
    format_date,
    format_name,
    format_phone,
    format_time,
    ltr,
    rtl,
)
from app.core.text import pluralize_hebrew, split_name, truncate


class TestFormatDate:
    def test_dd_mm_yyyy(self) -> None:
        assert format_date(date(1990, 3, 5), "DD/MM/YYYY") == "05/03/1990"

    def test_dd_dot_mm_dot_yyyy(self) -> None:
        assert format_date(date(1990, 3, 5), "DD.MM.YYYY") == "05.03.1990"

    def test_iso(self) -> None:
        assert format_date(date(1990, 3, 5), "YYYY-MM-DD") == "1990-03-05"

    def test_unknown_format_falls_back_to_default(self) -> None:
        assert format_date(date(1990, 3, 5), "bogus") == "05/03/1990"


class TestFormatTime:
    def test_24h(self) -> None:
        assert format_time(9, 5, "24h") == "09:05"
        assert format_time(23, 0, "24h") == "23:00"

    def test_12h_am(self) -> None:
        assert format_time(9, 5, "12h") == "9:05 AM"

    def test_12h_pm(self) -> None:
        assert format_time(13, 30, "12h") == "1:30 PM"

    def test_12h_midnight(self) -> None:
        assert format_time(0, 0, "12h") == "12:00 AM"

    def test_12h_noon(self) -> None:
        assert format_time(12, 0, "12h") == "12:00 PM"


class TestFormatCountdown:
    def test_today(self) -> None:
        assert format_countdown(0) == "היום"

    def test_tomorrow(self) -> None:
        assert format_countdown(1) == "מחר"

    def test_two_days_uses_dual_form(self) -> None:
        assert format_countdown(2) == "עוד יומיים"

    def test_five_days(self) -> None:
        assert format_countdown(5) == "עוד 5 ימים"

    def test_seven_days_is_a_week(self) -> None:
        assert format_countdown(7) == "עוד שבוע"

    def test_two_months_uses_dual_form(self) -> None:
        assert "חודשיים" in format_countdown(65)

    def test_always_returns_nonempty(self) -> None:
        for days in range(0, 200, 7):
            assert format_countdown(days)


class TestFormatPhone:
    def test_israeli_e164(self) -> None:
        assert format_phone("+972501234567") == "050-1234567"

    def test_israeli_local(self) -> None:
        assert format_phone("0501234567") == "050-1234567"

    def test_without_leading_zero(self) -> None:
        assert format_phone("501234567") == "050-1234567"

    def test_landline_style_9_digits(self) -> None:
        # e.g. a 2-digit area code + 7-digit number after normalization
        result = format_phone("021234567")
        assert result.count("-") == 1

    def test_non_standard_length_returned_as_digits(self) -> None:
        # A foreign number that doesn't fit the 9/10-digit Israeli shape
        # is returned as plain digits rather than forced into a hyphenated form.
        result = format_phone("+14155552671")
        assert result == "014155552671"


class TestFormatName:
    def test_with_last_name(self) -> None:
        assert format_name("Dana", "Cohen") == "Dana Cohen"

    def test_without_last_name(self) -> None:
        assert format_name("Dana", None) == "Dana"

    def test_empty_last_name_omitted(self) -> None:
        assert format_name("Dana", "") == "Dana"


class TestRtlLtr:
    def test_rtl_prepends_rlm(self) -> None:
        assert rtl("שלום") == f"{RLM}שלום"

    def test_ltr_wraps_both_sides(self) -> None:
        assert ltr("050-123") == f"{LRM}050-123{LRM}"


class TestPluralizeHebrew:
    @pytest.mark.parametrize(
        ("count", "unit", "expected"),
        [
            (1, "day", "1 יום"),
            (2, "day", "יומיים"),
            (5, "day", "5 ימים"),
            (1, "year", "1 שנה"),
            (2, "year", "שנתיים"),
            (5, "year", "5 שנים"),
            (1, "week", "1 שבוע"),
            (2, "week", "שבועיים"),
            (3, "week", "3 שבועות"),
        ],
    )
    def test_pluralization(self, count: int, unit: str, expected: str) -> None:
        assert pluralize_hebrew(count, unit) == expected

    def test_unknown_unit_raises(self) -> None:
        with pytest.raises(ValueError):
            pluralize_hebrew(1, "banana")


class TestTruncate:
    def test_short_text_unchanged(self) -> None:
        assert truncate("hello", 10) == "hello"

    def test_long_text_truncated_with_ellipsis(self) -> None:
        result = truncate("hello world", 8)
        assert len(result) == 8
        assert result.endswith("…")

    def test_exact_length_unchanged(self) -> None:
        assert truncate("hello", 5) == "hello"

    def test_max_len_smaller_than_suffix_truncates_suffix_itself(self) -> None:
        result = truncate("hello world", 1)
        assert result == "…"
        assert len(result) == 1


class TestSplitName:
    def test_full_name_splits_on_first_space(self) -> None:
        assert split_name("Dana Cohen") == ("Dana", "Cohen")

    def test_single_name_has_no_last_name(self) -> None:
        assert split_name("Dana") == ("Dana", None)

    def test_multiple_spaces_keep_rest_as_last_name(self) -> None:
        assert split_name("Dana Ben Cohen") == ("Dana", "Ben Cohen")

    def test_trailing_whitespace_after_first_name_yields_no_last_name(self) -> None:
        assert split_name("Dana  ") == ("Dana", None)
