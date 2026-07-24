from __future__ import annotations

from pathlib import Path

from app.i18n.translator import load_locales, t

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


def test_he_and_en_have_same_keys() -> None:
    catalogs = load_locales(LOCALES_DIR)
    he_keys = set(catalogs["he"].keys())
    en_keys = set(catalogs["en"].keys())
    assert he_keys == en_keys, (
        f"key mismatch — only in he: {he_keys - en_keys}, only in en: {en_keys - he_keys}"
    )


def test_t_returns_hebrew_by_default() -> None:
    load_locales(LOCALES_DIR)
    assert t("common.home", "he") == "🏠 בית"


def test_t_falls_back_to_hebrew_for_unknown_language() -> None:
    load_locales(LOCALES_DIR)
    assert t("common.home", "fr") == "🏠 בית"


def test_t_missing_key_returns_key_itself() -> None:
    load_locales(LOCALES_DIR)
    assert t("does.not.exist", "he") == "does.not.exist"


def test_t_formats_kwargs() -> None:
    load_locales(LOCALES_DIR)
    assert t("error.too_long", "he", max=64) == "זה ארוך מדי — עד 64 תווים."
