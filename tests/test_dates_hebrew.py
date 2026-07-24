from __future__ import annotations

import random
from datetime import date, timedelta

import pytest

from app.core import hebcal
from app.core.dates import age_at, next_occurrence


class TestMonthMapping:
    """SPEC.md chapter 10: verify the month table against the installed pyluach."""

    def test_nisan_is_month_1(self) -> None:
        # Nisan 1, 5786 falls in March 2026 per pyluach.
        assert hebcal.to_gregorian(5786, 1, 1) == date(2026, 3, 19)

    def test_tishrei_is_month_7(self) -> None:
        assert hebcal.to_gregorian(5786, 7, 1) == date(2025, 9, 23)

    def test_cheshvan_is_month_8(self) -> None:
        d = hebcal.to_gregorian(5786, 8, 1)
        year, month, day = hebcal.to_hebrew(d)
        assert (year, month, day) == (5786, 8, 1)

    def test_adar_is_month_12_in_simple_year(self) -> None:
        assert hebcal.is_leap_year(5786) is False
        # Should not raise: month 12 exists in a simple year.
        hebcal.to_gregorian(5786, 12, 1)

    def test_adar_ii_is_month_13_only_in_leap_year(self) -> None:
        assert hebcal.is_leap_year(5784) is True
        hebcal.to_gregorian(5784, 13, 1)  # should not raise
        with pytest.raises(ValueError):
            hebcal.to_gregorian(5786, 13, 1)  # 5786 is not leap

    def test_hebrew_month_names_match_spec_table(self) -> None:
        names = [hebcal.hebrew_month_name(m) for m in range(1, 14)]
        assert names == [
            "ניסן",
            "אייר",
            "סיוון",
            "תמוז",
            "אב",
            "אלול",
            "תשרי",
            "חשוון",
            "כסלו",
            "טבת",
            "שבט",
            "אדר",
            "אדר ב׳",
        ]


class TestRoundTrip:
    def test_gregorian_hebrew_gregorian_round_trip_3000_dates(self) -> None:
        rng = random.Random(42)
        start = date(1950, 1, 1)
        span_days = (date(2100, 1, 1) - start).days

        for _ in range(3000):
            d = start + timedelta(days=rng.randint(0, span_days))
            h_year, h_month, h_day = hebcal.to_hebrew(d)
            back = hebcal.to_gregorian(h_year, h_month, h_day)
            assert back == d, f"round trip failed for {d}: got {h_year}-{h_month}-{h_day} -> {back}"


class TestChesvanEdgeCase:
    def test_30_cheshvan_in_short_year_falls_back_to_29(self) -> None:
        # 5786 (2026): Cheshvan is short (29 days) per pyluach.
        assert hebcal.month_length(5786, 8) == 29
        result = hebcal.to_gregorian(5786, 8, 30)
        assert result == hebcal.to_gregorian(5786, 8, 29)

    def test_30_cheshvan_in_full_year_is_valid(self) -> None:
        # 5785: Cheshvan is full (30 days) per pyluach.
        assert hebcal.month_length(5785, 8) == 30
        result = hebcal.to_gregorian(5785, 8, 30)
        year, month, day = hebcal.to_hebrew(result)
        assert (month, day) == (8, 30)

    def test_never_rolls_into_next_month(self) -> None:
        result = hebcal.to_gregorian(5786, 8, 30)
        _, month, _ = hebcal.to_hebrew(result)
        assert month == 8


class TestKislevEdgeCase:
    def test_30_kislev_in_short_year_falls_back_to_29(self) -> None:
        # Find a year where Kislev is short (29 days).
        short_kislev_year = next(
            y for y in range(5780, 5800) if hebcal.month_length(y, 9) == 29
        )
        result = hebcal.to_gregorian(short_kislev_year, 9, 30)
        assert result == hebcal.to_gregorian(short_kislev_year, 9, 29)

    def test_30_kislev_in_full_year_is_valid(self) -> None:
        full_kislev_year = next(
            y for y in range(5780, 5800) if hebcal.month_length(y, 9) == 30
        )
        result = hebcal.to_gregorian(full_kislev_year, 9, 30)
        _, month, day = hebcal.to_hebrew(result)
        assert (month, day) == (9, 30)


class TestAdarPolicy:
    def test_born_in_adar_simple_year_resolves_to_adar_ii_by_default(self) -> None:
        # 5784 is a leap year.
        resolved = hebcal.resolve_month(5784, 12, "adar_ii")
        assert resolved == 13

    def test_born_in_adar_simple_year_resolves_to_adar_i_when_configured(self) -> None:
        resolved = hebcal.resolve_month(5784, 12, "adar_i")
        assert resolved == 12

    def test_born_in_adar_i_maps_to_adar_in_simple_year(self) -> None:
        resolved = hebcal.resolve_month(5786, 13, "adar_ii")
        assert resolved == 12

    def test_born_in_adar_ii_maps_to_adar_in_simple_year(self) -> None:
        resolved = hebcal.resolve_month(5786, 13, "adar_i")
        assert resolved == 12

    def test_30_adar_i_falls_back_to_29_in_simple_year(self) -> None:
        # In a simple year, Adar (month 12) has 29 days.
        assert hebcal.month_length(5786, 12) == 29
        result = hebcal.to_gregorian(5786, 12, 30)
        assert result == hebcal.to_gregorian(5786, 12, 29)

    def test_plain_months_unaffected_by_policy(self) -> None:
        assert hebcal.resolve_month(5786, 3, "adar_ii") == 3
        assert hebcal.resolve_month(5784, 5, "adar_i") == 5

    def test_born_in_adar_ii_stays_adar_ii_in_another_leap_year(self) -> None:
        # 5784 and 5787 are both leap years; someone born specifically in
        # Adar II (month 13) should resolve to Adar II again, regardless of policy.
        assert hebcal.is_leap_year(5787) is True
        assert hebcal.resolve_month(5787, 13, "adar_i") == 13
        assert hebcal.resolve_month(5787, 13, "adar_ii") == 13


class TestHebrewOccurrence:
    def test_next_occurrence_hebrew_calendar(self) -> None:
        today = date(2026, 1, 1)
        result = next_occurrence("hebrew", 5750, 8, 30, today)
        h_year, h_month, h_day = hebcal.to_hebrew(result)
        assert h_month == 8
        assert result >= today

    def test_next_occurrence_hebrew_crosses_adar_leap_boundary(self) -> None:
        today = date(2026, 6, 1)  # next relevant Hebrew year (5787) is leap
        result = next_occurrence("hebrew", 5750, 12, 15, today, adar_policy="adar_ii")
        h_year, h_month, h_day = hebcal.to_hebrew(result)
        assert h_month == 13
        assert h_day == 15


class TestHebrewAge:
    def test_hebrew_age_close_to_gregorian_age_within_one_year(self) -> None:
        # Same person's birthday, compared in both calendars — hebrew year
        # count may differ from the gregorian one by at most 1.
        occ_date = date(2026, 3, 8)  # 19 Adar 5786
        gregorian_age = age_at("gregorian", 1990, 3, 15, occ_date)
        hebrew_age = age_at("hebrew", 5750, 12, 19, occ_date)
        assert gregorian_age is not None
        assert hebrew_age is not None
        assert abs(gregorian_age - hebrew_age) <= 1

    def test_hebrew_age_none_when_year_unknown(self) -> None:
        assert age_at("hebrew", None, 12, 19, date(2026, 3, 8)) is None


class TestGematria:
    def test_year_5786(self) -> None:
        assert hebcal.hebrew_year_gematria(5786) == "תשפ״ו"

    def test_15_is_tet_vav_not_yud_heh(self) -> None:
        assert hebcal.gematria(15) == "ט״ו"

    def test_16_is_tet_zayin_not_yud_vav(self) -> None:
        assert hebcal.gematria(16) == "ט״ז"

    def test_single_digit_uses_geresh(self) -> None:
        assert hebcal.gematria(3) == "ג׳"

    def test_round_ten_uses_geresh(self) -> None:
        assert hebcal.gematria(20) == "כ׳"

    def test_multi_letter_uses_gershayim(self) -> None:
        assert hebcal.gematria(11) == "י״א"

    def test_zero_returns_empty_string(self) -> None:
        assert hebcal.gematria(0) == ""

    @pytest.mark.parametrize(
        ("num", "expected"),
        [(1, "א׳"), (9, "ט׳"), (10, "י׳"), (14, "י״ד"), (17, "י״ז"), (26, "כ״ו"), (30, "ל׳")],
    )
    def test_various_values(self, num: int, expected: str) -> None:
        assert hebcal.gematria(num) == expected


class TestFormatHebrewDate:
    def test_format_with_year(self) -> None:
        assert hebcal.format_hebrew_date(5786, 12, 19) == "י״ט באדר תשפ״ו"

    def test_format_without_year(self) -> None:
        result = hebcal.format_hebrew_date(5786, 12, 19, with_year=False)
        assert result == "י״ט באדר"
