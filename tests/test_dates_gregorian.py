from __future__ import annotations

from datetime import date

import pytest

from app.core.dates import age_at, days_until, next_occurrence, upcoming_between


class FakeEvent:
    def __init__(self, next_occurrence: date | None) -> None:
        self.next_occurrence = next_occurrence


class TestNextOccurrenceGregorian:
    def test_birthday_tomorrow(self) -> None:
        today = date(2026, 3, 14)
        assert next_occurrence("gregorian", 1990, 3, 15, today) == date(2026, 3, 15)

    def test_birthday_today_returns_today(self) -> None:
        today = date(2026, 3, 14)
        assert next_occurrence("gregorian", 1990, 3, 14, today) == date(2026, 3, 14)

    def test_birthday_yesterday_rolls_to_next_year(self) -> None:
        today = date(2026, 3, 14)
        assert next_occurrence("gregorian", 1990, 3, 13, today) == date(2027, 3, 13)

    def test_dec_31_checked_from_dec_30(self) -> None:
        today = date(2026, 12, 30)
        assert next_occurrence("gregorian", None, 12, 31, today) == date(2026, 12, 31)

    def test_dec_31_checked_from_jan_1_next_year(self) -> None:
        today = date(2027, 1, 1)
        assert next_occurrence("gregorian", None, 12, 31, today) == date(2027, 12, 31)

    def test_no_year_still_computes_occurrence(self) -> None:
        today = date(2026, 1, 1)
        assert next_occurrence("gregorian", None, 6, 1, today) == date(2026, 6, 1)

    def test_feb29_non_leap_year_feb28_policy(self) -> None:
        today = date(2026, 1, 1)  # 2026 is not a leap year
        result = next_occurrence("gregorian", None, 2, 29, today, feb29_policy="feb28")
        assert result == date(2026, 2, 28)

    def test_feb29_non_leap_year_mar01_policy(self) -> None:
        today = date(2026, 1, 1)
        result = next_occurrence("gregorian", None, 2, 29, today, feb29_policy="mar01")
        assert result == date(2026, 3, 1)

    def test_feb29_leap_year_lands_on_feb29(self) -> None:
        today = date(2028, 1, 1)  # 2028 is a leap year
        result = next_occurrence("gregorian", None, 2, 29, today)
        assert result == date(2028, 2, 29)

    def test_feb29_exactly_on_feb28_with_feb28_policy_is_today(self) -> None:
        today = date(2026, 2, 28)
        result = next_occurrence("gregorian", None, 2, 29, today, feb29_policy="feb28")
        assert result == date(2026, 2, 28)

    def test_feb29_rolls_to_next_year_still_non_leap(self) -> None:
        today = date(2026, 6, 1)
        result = next_occurrence("gregorian", None, 2, 29, today, feb29_policy="feb28")
        assert result == date(2027, 2, 28)

    def test_feb29_rolls_to_next_year_which_is_leap(self) -> None:
        today = date(2027, 6, 1)  # 2028 is leap
        result = next_occurrence("gregorian", None, 2, 29, today)
        assert result == date(2028, 2, 29)

    def test_april_31_does_not_exist_clamps_to_april_30(self) -> None:
        # April has only 30 days; a stored day=31 for month=4 must not crash.
        today = date(2026, 1, 1)
        result = next_occurrence("gregorian", None, 4, 31, today)
        assert result == date(2026, 4, 30)

    def test_april_31_clamped_when_rolling_into_next_year(self) -> None:
        today = date(2026, 5, 1)  # this year's April 30 already passed
        result = next_occurrence("gregorian", None, 4, 31, today)
        assert result == date(2027, 4, 30)


class TestAgeAtGregorian:
    def test_age_exact_on_occurrence_day(self) -> None:
        assert age_at("gregorian", 1990, 3, 15, date(2026, 3, 15)) == 36

    def test_age_none_when_year_unknown(self) -> None:
        assert age_at("gregorian", None, 3, 15, date(2026, 3, 15)) is None

    def test_age_day_before_occurrence_uses_prior_year(self) -> None:
        # age_at reflects age AT the given occurrence date, not "today"
        assert age_at("gregorian", 1990, 3, 15, date(2025, 3, 15)) == 35


class TestDaysUntil:
    def test_today_is_zero(self) -> None:
        assert days_until(date(2026, 3, 14), date(2026, 3, 14)) == 0

    def test_tomorrow_is_one(self) -> None:
        assert days_until(date(2026, 3, 15), date(2026, 3, 14)) == 1

    def test_past_is_negative(self) -> None:
        assert days_until(date(2026, 3, 10), date(2026, 3, 14)) == -4


class TestUpcomingBetween:
    def test_filters_and_sorts_by_occurrence(self) -> None:
        e1 = FakeEvent(date(2026, 3, 20))
        e2 = FakeEvent(date(2026, 3, 15))
        e3 = FakeEvent(date(2026, 4, 1))  # out of range
        e4 = FakeEvent(None)  # no occurrence at all

        result = upcoming_between([e1, e2, e3, e4], date(2026, 3, 1), date(2026, 3, 31))
        assert [pair[0] for pair in result] == [e2, e1]
        assert [pair[1] for pair in result] == [date(2026, 3, 15), date(2026, 3, 20)]

    def test_empty_list(self) -> None:
        assert upcoming_between([], date(2026, 1, 1), date(2026, 12, 31)) == []

    def test_boundary_inclusive(self) -> None:
        e = FakeEvent(date(2026, 3, 1))
        result = upcoming_between([e], date(2026, 3, 1), date(2026, 3, 1))
        assert len(result) == 1


@pytest.mark.parametrize(
    ("month", "day"),
    [(1, 1), (6, 15), (12, 31), (2, 28)],
)
def test_next_occurrence_always_on_or_after_today(month: int, day: int) -> None:
    today = date(2026, 5, 1)
    result = next_occurrence("gregorian", None, month, day, today)
    assert result >= today
