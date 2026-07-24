from __future__ import annotations

from app.core.text import esc


class TestEsc:
    def test_escapes_script_tag(self) -> None:
        result = esc("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escapes_ampersand(self) -> None:
        assert esc("Tom & Jerry") == "Tom &amp; Jerry"

    def test_none_returns_empty_string(self) -> None:
        assert esc(None) == ""

    def test_plain_text_unchanged(self) -> None:
        assert esc("Dana Cohen") == "Dana Cohen"

    def test_hebrew_text_unchanged(self) -> None:
        assert esc("דנה כהן") == "דנה כהן"

    def test_quotes_not_escaped(self) -> None:
        # Rendered as HTML body text, not an attribute — quotes are safe as-is.
        assert esc('He said "hi"') == 'He said "hi"'
