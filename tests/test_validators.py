from __future__ import annotations

import pytest

from app.core.validators import (
    ParsedDate,
    ValidationError,
    contains_only_symbols,
    parse_gregorian,
    parse_hebrew_year_input,
    validate_name,
    validate_nickname,
    validate_notes,
    validate_phone,
    validate_relation,
    validate_year,
)


class TestParseGregorian:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("15/03/1990", ParsedDate(15, 3, 1990)),
            ("15.03.1990", ParsedDate(15, 3, 1990)),
            ("15-03-1990", ParsedDate(15, 3, 1990)),
            ("15/03", ParsedDate(15, 3, None)),
            ("15.03", ParsedDate(15, 3, None)),
            ("1990-03-15", ParsedDate(15, 3, 1990)),
            ("15 במרץ", ParsedDate(15, 3, None)),
            ("15 March", ParsedDate(15, 3, None)),
            ("15 march", ParsedDate(15, 3, None)),
            ("1 בינואר", ParsedDate(1, 1, None)),
        ],
    )
    def test_valid_formats(self, text: str, expected: ParsedDate) -> None:
        assert parse_gregorian(text) == expected

    def test_two_digit_year_low_maps_to_2000s(self) -> None:
        # current year is 2026 -> yy=10 is <= 26, maps to 2010
        result = parse_gregorian("15/03/10")
        assert result.year == 2010

    def test_two_digit_year_high_maps_to_1900s(self) -> None:
        # yy=90 is > 26, maps to 1990
        result = parse_gregorian("15/03/90")
        assert result.year == 1990

    def test_garbage_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("not a date")

    def test_invalid_month_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("15/13/1990")

    def test_invalid_day_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("32/01/1990")

    def test_year_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("15/03/1800")

    def test_unknown_month_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("15 Blorptember")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("")

    def test_script_injection_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("<script>alert(1)</script>")

    def test_two_digit_year_invalid_day_month_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("32/13/90")

    def test_iso_format_invalid_day_month_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("1990-13-32")

    def test_iso_format_year_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("1800-03-15")

    def test_no_year_format_invalid_day_month_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("32/13")

    def test_hebrew_month_name_invalid_day_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_gregorian("32 במרץ")


class TestValidateName:
    def test_valid_name_passes_through(self) -> None:
        assert validate_name("Dana Cohen") == "Dana Cohen"

    def test_strips_whitespace(self) -> None:
        assert validate_name("  Dana  ") == "Dana"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_name("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_name("   ")

    def test_max_length_boundary_passes(self) -> None:
        assert validate_name("a" * 64) == "a" * 64

    def test_over_max_length_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_name("a" * 65)

    def test_control_characters_stripped(self) -> None:
        assert validate_name("Dana\x00\x01Cohen") == "DanaCohen"

    def test_emoji_allowed(self) -> None:
        assert validate_name("Dana 🎂") == "Dana 🎂"

    def test_script_tag_not_stripped_only_escaped_later(self) -> None:
        # Validators store raw text; escaping happens at render time (core/text.esc).
        result = validate_name("<script>x</script>")
        assert "<script>" in result


class TestValidateOptionalFields:
    def test_nickname_max_length(self) -> None:
        with pytest.raises(ValidationError):
            validate_nickname("a" * 33)
        assert validate_nickname("a" * 32) == "a" * 32

    def test_notes_max_length(self) -> None:
        with pytest.raises(ValidationError):
            validate_notes("a" * 501)
        assert validate_notes("a" * 500) == "a" * 500

    def test_relation_max_length(self) -> None:
        with pytest.raises(ValidationError):
            validate_relation("a" * 33)
        assert validate_relation("a" * 32) == "a" * 32

    def test_empty_optional_fields_are_valid(self) -> None:
        assert validate_nickname("") == ""
        assert validate_notes("") == ""
        assert validate_relation("") == ""


class TestValidatePhone:
    @pytest.mark.parametrize(
        "text",
        ["+972501234567", "0501234567", "050-123-4567", "050 123 4567", "(050) 123-4567"],
    )
    def test_valid_phones(self, text: str) -> None:
        result = validate_phone(text)
        assert result.replace("+", "").isdigit()

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_phone("1" * 21)

    def test_letters_raise(self) -> None:
        with pytest.raises(ValidationError):
            validate_phone("call-me-maybe")

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_phone("123")

    def test_control_characters_stripped(self) -> None:
        result = validate_phone("050\x001234567")
        assert "\x00" not in result


class TestValidateYear:
    def test_gregorian_valid_range(self) -> None:
        assert validate_year(1990) == 1990
        assert validate_year(1900) == 1900
        assert validate_year(2100) == 2100

    def test_gregorian_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_year(1899)
        with pytest.raises(ValidationError):
            validate_year(2101)

    def test_hebrew_valid_range(self) -> None:
        assert validate_year(5750, hebrew=True) == 5750

    def test_hebrew_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_year(5659, hebrew=True)
        with pytest.raises(ValidationError):
            validate_year(5861, hebrew=True)


class TestParseHebrewYearInput:
    def test_hebrew_year_passes_through(self) -> None:
        assert parse_hebrew_year_input("5750") == 5750

    def test_gregorian_year_auto_converts(self) -> None:
        result = parse_hebrew_year_input("1990")
        assert 5750 <= result <= 5751

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_hebrew_year_input("abc")

    def test_out_of_any_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            parse_hebrew_year_input("42")


class TestContainsOnlySymbols:
    def test_emoji_only(self) -> None:
        assert contains_only_symbols("🎂🎉") is True

    def test_whitespace_and_punctuation_only(self) -> None:
        assert contains_only_symbols("   ...!!!") is True

    def test_has_letters(self) -> None:
        assert contains_only_symbols("Dana") is False

    def test_has_digits(self) -> None:
        assert contains_only_symbols("123") is False

    def test_hebrew_letters(self) -> None:
        assert contains_only_symbols("דנה") is False
