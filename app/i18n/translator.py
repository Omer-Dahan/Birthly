from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

_LOCALES_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent / "locales"
_FALLBACK_LANGUAGE: Final[str] = "he"

_catalogs: dict[str, dict[str, str]] = {}


def load_locales(locales_dir: Path = _LOCALES_DIR) -> dict[str, dict[str, str]]:
    """Load every ``<lang>.json`` file in ``locales_dir`` into memory.

    Returns the loaded catalogs and also caches them for :func:`t`.
    """
    catalogs: dict[str, dict[str, str]] = {}
    for path in sorted(locales_dir.glob("*.json")):
        lang = path.stem
        with path.open(encoding="utf-8") as f:
            catalogs[lang] = json.load(f)
    _catalogs.clear()
    _catalogs.update(catalogs)
    return catalogs


def t(key: str, lang: str = _FALLBACK_LANGUAGE, **kwargs: object) -> str:
    """Translate ``key`` into ``lang``. Falls back to Hebrew, then to the key itself."""
    if not _catalogs:
        load_locales()

    catalog = _catalogs.get(lang) or _catalogs.get(_FALLBACK_LANGUAGE) or {}
    template = catalog.get(key)

    if template is None:
        fallback_catalog = _catalogs.get(_FALLBACK_LANGUAGE) or {}
        template = fallback_catalog.get(key)

    if template is None:
        logger.warning("missing_i18n_key", extra={"key": key, "lang": lang})
        return key

    if kwargs:
        return template.format(**kwargs)
    return template
